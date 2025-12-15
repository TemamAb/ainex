# Aineon Enterprise Infrastructure as Code
# Top 0.001% Enterprise Grade - Production Ready

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    bucket         = "aineon-terraform-state"
    key            = "enterprise/production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "aineon-terraform-locks"
  }
}

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment   = var.environment
      Project       = "Aineon"
      ManagedBy     = "Terraform"
      Certification = "Top 0.001% Enterprise Grade"
      Owner         = "Enterprise Architecture Team"
    }
  }
}

# ============================================================================
# VPC AND NETWORKING
# ============================================================================

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "aineon-${var.environment}"
  cidr = var.vpc_cidr

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway     = true
  single_nat_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # VPC Flow Logs for security monitoring
  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true

  tags = {
    Name = "aineon-${var.environment}-vpc"
  }
}

# Security Groups
resource "aws_security_group" "aineon_engine" {
  name_prefix = "aineon-engine-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTPS from load balancer"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  ingress {
    description = "HTTP from load balancer"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aineon-engine-sg"
  }
}

# ============================================================================
# EKS CLUSTER
# ============================================================================

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "aineon-${var.environment}"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Cluster endpoint access
  cluster_endpoint_public_access  = false
  cluster_endpoint_private_access = true

  # Encryption
  attach_cluster_encryption_policy = true
  cluster_encryption_config = [{
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }]

  # Logging
  cloudwatch_log_group_retention_in_days = 90
  cluster_enabled_log_types = [
    "api", "audit", "authenticator", "controllerManager", "scheduler"
  ]

  # Node Groups
  eks_managed_node_groups = {
    core = {
      name           = "aineon-core"
      instance_types = ["c6i.xlarge"]
      min_size       = 3
      max_size       = 50
      desired_size   = 10

      # Auto-scaling
      enable_autoscaling = true

      # Spot instances for cost optimization
      capacity_type = "SPOT"
      spot_allocation_strategy = "diversified"

      # Security
      iam_role_additional_policies = [
        "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
      ]

      # Monitoring
      enable_monitoring = true

      tags = {
        "k8s.io/cluster-autoscaler/enabled" = "true"
        "k8s.io/cluster-autoscaler/aineon-${var.environment}" = "owned"
      }
    }

    monitoring = {
      name           = "aineon-monitoring"
      instance_types = ["c6i.large"]
      min_size       = 2
      max_size       = 10
      desired_size   = 3

      taints = [{
        key    = "dedicated"
        value  = "monitoring"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  # IRSA (IAM Roles for Service Accounts)
  enable_irsa = true

  # Cluster add-ons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  tags = {
    Name = "aineon-${var.environment}-eks"
  }
}

# KMS Key for EKS encryption
resource "aws_kms_key" "eks" {
  description             = "KMS key for EKS cluster encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = data.aws_iam_policy_document.eks_kms.json

  tags = {
    Name = "aineon-eks-encryption"
  }
}

data "aws_iam_policy_document" "eks_kms" {
  statement {
    sid    = "Enable IAM User Permissions"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "Allow EKS to use KMS"
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = [module.eks.cluster_iam_role_arn]
    }
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]
    resources = ["*"]
  }
}

# ============================================================================
# DATABASE (RDS PostgreSQL)
# ============================================================================

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "aineon-${var.environment}"

  # Engine configuration
  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.r6g.xlarge"

  # Storage
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.rds.arn

  # Database configuration
  db_name  = "aineon"
  username = "aineon_admin"
  port     = 5432

  # Multi-AZ for high availability
  multi_az = true

  # Backup and maintenance
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # Security
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.aineon.name

  # Monitoring
  monitoring_interval    = 60
  monitoring_role_arn    = aws_iam_role.rds_enhanced_monitoring.arn
  create_monitoring_role = false

  # Performance Insights
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  tags = {
    Name = "aineon-${var.environment}-rds"
  }
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "aineon-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "PostgreSQL from EKS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  tags = {
    Name = "aineon-rds-sg"
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "aineon" {
  name       = "aineon-${var.environment}"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "aineon-db-subnet-group"
  }
}

# KMS Key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "aineon-rds-encryption"
  }
}

# RDS Enhanced Monitoring IAM Role
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "aineon-rds-enhanced-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"]
}

# ============================================================================
# REDIS CACHE
# ============================================================================

module "redis" {
  source = "cloudposse/elasticache-redis/aws"
  version = "0.50.0"

  name               = "aineon-${var.environment}"
  replication_group_id = "aineon-${var.environment}"

  # Engine configuration
  engine_version = "7.0"
  port           = 6379
  instance_type  = "cache.r6g.large"
  cluster_size   = 3

  # Multi-AZ
  automatic_failover_enabled = true
  multi_az_enabled          = true

  # Security
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  security_group_ids = [aws_security_group.redis.id]

  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                = aws_kms_key.redis.arn

  # Backup
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-04:00"

  # Maintenance
  maintenance_window = "sun:04:00-sun:05:00"

  tags = {
    Name = "aineon-${var.environment}-redis"
  }
}

# Redis Security Group
resource "aws_security_group" "redis" {
  name_prefix = "aineon-redis-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Redis from EKS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  tags = {
    Name = "aineon-redis-sg"
  }
}

# KMS Key for Redis encryption
resource "aws_kms_key" "redis" {
  description             = "KMS key for Redis encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "aineon-redis-encryption"
  }
}

# ============================================================================
# LOAD BALANCER
# ============================================================================

module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 8.0"

  name = "aineon-${var.environment}"

  load_balancer_type = "application"
  vpc_id             = module.vpc.vpc_id
  subnets            = module.vpc.public_subnets
  security_groups    = [aws_security_group.alb.id]

  # Access logs
  access_logs = {
    bucket = aws_s3_bucket.alb_logs.id
    prefix = "alb-logs"
  }

  # Listeners
  listeners = {
    http = {
      port     = 80
      protocol = "HTTP"

      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    https = {
      port            = 443
      protocol        = "HTTPS"
      certificate_arn = aws_acm_certificate.aineon.arn

      forward = {
        target_group_key = "aineon"
      }
    }
  }

  # Target Groups
  target_groups = {
    aineon = {
      name_prefix          = "aineon-"
      protocol             = "HTTP"
      port                 = 8082
      target_type          = "ip"
      deregistration_delay = 30

      health_check = {
        enabled             = true
        healthy_threshold   = 2
        interval            = 30
        matcher             = "200"
        path                = "/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 2
      }

      # Stickiness for session affinity
      stickiness = {
        type            = "lb_cookie"
        cookie_duration = 1800
        enabled         = true
      }
    }
  }

  tags = {
    Name = "aineon-${var.environment}-alb"
  }
}

# ALB Security Group
resource "aws_security_group" "alb" {
  name_prefix = "aineon-alb-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "aineon-alb-sg"
  }
}

# ============================================================================
# MONITORING & LOGGING
# ============================================================================

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "aineon" {
  for_each = toset([
    "/aws/eks/aineon-${var.environment}/application",
    "/aws/eks/aineon-${var.environment}/datadog",
    "/aws/eks/aineon-${var.environment}/fluent-bit"
  ])

  name              = each.value
  retention_in_days = 90

  kms_key_id = aws_kms_key.cloudwatch.arn

  tags = {
    Name = "aineon-${var.environment}-logs"
  }
}

# KMS Key for CloudWatch encryption
resource "aws_kms_key" "cloudwatch" {
  description             = "KMS key for CloudWatch log encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "aineon-cloudwatch-encryption"
  }
}

# ============================================================================
# BACKUP & DISASTER RECOVERY
# ============================================================================

# S3 Bucket for backups
resource "aws_s3_bucket" "backups" {
  bucket = "aineon-${var.environment}-backups-${random_string.suffix.result}"

  tags = {
    Name = "aineon-backups"
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
      kms_master_key_id = aws_kms_key.s3.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# KMS Key for S3 encryption
resource "aws_kms_key" "s3" {
  description             = "KMS key for S3 bucket encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "aineon-s3-encryption"
  }
}

# Random suffix for globally unique bucket names
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# ============================================================================
# CERTIFICATES & DNS
# ============================================================================

# ACM Certificate
resource "aws_acm_certificate" "aineon" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "aineon-${var.environment}-certificate"
  }
}

# Route 53 Hosted Zone (if creating new)
resource "aws_route53_zone" "aineon" {
  count = var.create_hosted_zone ? 1 : 0

  name = var.domain_name

  tags = {
    Name = "aineon-${var.environment}-hosted-zone"
  }
}

# Route 53 Records
resource "aws_route53_record" "aineon" {
  zone_id = var.create_hosted_zone ? aws_route53_zone.aineon[0].zone_id : var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = module.alb.lb_dns_name
    zone_id                = module.alb.lb_zone_id
    evaluate_target_health = true
  }
}

# ============================================================================
# IAM ROLES & POLICIES
# ============================================================================

# EKS Service Account IAM Role
resource "aws_iam_role" "aineon_sa" {
  name = "aineon-${var.environment}-sa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = module.eks.oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "${module.eks.oidc_provider}:sub": "system:serviceaccount:aineon:aineon-engine"
          }
        }
      }
    ]
  })

  tags = {
    Name = "aineon-service-account-role"
  }
}

# Attach policies to service account role
resource "aws_iam_role_policy_attachment" "aineon_sa_rds" {
  role       = aws_iam_role.aineon_sa.name
  policy_arn = aws_iam_policy.aineon_rds_access.arn
}

resource "aws_iam_role_policy_attachment" "aineon_sa_redis" {
  role       = aws_iam_role.aineon_sa.name
  policy_arn = aws_iam_policy.aineon_redis_access.arn
}

resource "aws_iam_role_policy_attachment" "aineon_sa_cloudwatch" {
  role       = aws_iam_role.aineon_sa.name
  policy_arn = aws_iam_policy.aineon_cloudwatch_access.arn
}

# IAM Policies
resource "aws_iam_policy" "aineon_rds_access" {
  name = "aineon-rds-access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-db:connect"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "aineon_redis_access" {
  name = "aineon-redis-access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticache:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "aineon_cloudwatch_access" {
  name = "aineon-cloudwatch-access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# DATA SOURCES
# ============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ============================================================================
# OUTPUTS
# ============================================================================

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.db_instance_address
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.redis.endpoint
}

output "alb_dns_name" {
  description = "Load balancer DNS name"
  value       = module.alb.lb_dns_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}