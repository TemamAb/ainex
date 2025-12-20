terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  
  default_tags {
    tags = {
      Project     = "AINEON Enterprise"
      Environment = "Production"
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Configuration
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"

  name = "aineon-enterprise-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
  enable_vpn_gateway = false

  tags = {
    Terraform   = "true"
    Environment = "production"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "aineon-enterprise"
  cluster_version = "1.27"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    main = {
      min_size     = 3
      max_size     = 10
      desired_size = 3

      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"

      update_config = {
        max_unavailable_percentage = 33
      }
    }
  }

  tags = {
    Environment = "production"
  }
}

# RDS Database
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 5.0"

  identifier = "aineon-enterprise-db"

  engine               = "postgres"
  engine_version       = "14.5"
  family               = "postgres14"
  major_engine_version = "14"
  instance_class       = "db.t3.large"

  allocated_storage     = 100
  max_allocated_storage = 500

  db_name  = "aineon_enterprise"
  username = var.db_username
  password = var.db_password
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.vpc.default_security_group_id]

  maintenance_window = "Mon:00:00-Mon:03:00"
  backup_window      = "03:00-06:00"
  backup_retention_period = 30

  tags = {
    Environment = "production"
  }
}

# Elasticache Redis
resource "aws_elasticache_cluster" "cache" {
  cluster_id           = "aineon-enterprise-cache"
  engine              = "redis"
  node_type           = "cache.t3.micro"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  engine_version      = "7.0"
  port               = 6379

  subnet_group_name = module.vpc.elasticache_subnet_group_name
  security_group_ids = [module.vpc.default_security_group_id]

  tags = {
    Environment = "production"
  }
}

# S3 Bucket for backups
resource "aws_s3_bucket" "backups" {
  bucket = "aineon-enterprise-backups-${var.environment}"

  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "cdn" {
  origin {
    domain_name = var.alb_dns_name
    origin_id   = "aineon-enterprise-alb"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "AINEON Enterprise CDN"
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "aineon-enterprise-alb"

    forwarded_values {
      query_string = true
      headers      = ["Origin"]

      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "whitelist"
      locations        = ["US", "CA", "GB", "DE", "FR", "JP", "SG", "AU"]
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = false
    acm_certificate_arn            = var.acm_certificate_arn
    ssl_support_method             = "sni-only"
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  tags = {
    Environment = var.environment
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  alarm_name          = "aineon-api-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "4xxErrorRate"
  namespace          = "AWS/ApplicationELB"
  period             = "300"
  statistic          = "Average"
  threshold          = "5"
  alarm_description  = "API 4xx error rate above 5%"
  alarm_actions      = [var.sns_topic_arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "api_latency" {
  alarm_name          = "aineon-api-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name        = "TargetResponseTime"
  namespace          = "AWS/ApplicationELB"
  period             = "60"
  statistic          = "Average"
  threshold          = "1"
  alarm_description  = "API latency above 1 second"
  alarm_actions      = [var.sns_topic_arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
}

# Outputs
output "cluster_endpoint" {
  description = "Endpoint for EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  description = "Endpoint for RDS database"
  value       = module.rds.db_instance_address
  sensitive   = true
}

output "cloudfront_domain" {
  description = "Domain name for CloudFront distribution"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

output "s3_bucket_name" {
  description = "Name of S3 backup bucket"
  value       = aws_s3_bucket.backups.bucket
}
