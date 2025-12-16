# Aineon Enterprise Infrastructure Variables
# Top 0.001% Enterprise Grade Configuration

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^(us|eu|ap|ca|sa)-(east|west|central|south|northeast|southeast)-[1-3]$", var.aws_region))
    error_message = "AWS region must be a valid region identifier."
  }
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "Environment must be one of: production, staging, development."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid CIDR block."
  }
}

variable "private_subnets" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]

  validation {
    condition = alltrue([
      for subnet in var.private_subnets : can(cidrhost(subnet, 0))
    ])
    error_message = "All private subnet CIDRs must be valid."
  }
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  validation {
    condition = alltrue([
      for subnet in var.public_subnets : can(cidrhost(subnet, 0))
    ])
    error_message = "All public subnet CIDRs must be valid."
  }
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "aineon.enterprise"

  validation {
    condition     = can(regex("^[a-zA-Z0-9.-]+$", var.domain_name))
    error_message = "Domain name must be a valid domain format."
  }
}

variable "create_hosted_zone" {
  description = "Whether to create a new Route 53 hosted zone"
  type        = bool
  default     = true
}

variable "hosted_zone_id" {
  description = "Existing Route 53 hosted zone ID (if not creating new)"
  type        = string
  default     = ""
}

# ============================================================================
# EKS CONFIGURATION
# ============================================================================

variable "eks_cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"

  validation {
    condition     = can(regex("^1\\.(2[4-9]|3[0-9])$", var.eks_cluster_version))
    error_message = "EKS cluster version must be 1.24 or higher."
  }
}

variable "eks_node_instance_types" {
  description = "EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["c6i.xlarge", "c6i.2xlarge"]

  validation {
    condition = alltrue([
      for type in var.eks_node_instance_types : can(regex("^[a-z][0-9][a-z]?\\.[0-9]*xlarge$", type))
    ])
    error_message = "Instance types must be valid EC2 instance types."
  }
}

variable "eks_min_nodes" {
  description = "Minimum number of EKS nodes"
  type        = number
  default     = 3

  validation {
    condition     = var.eks_min_nodes >= 1
    error_message = "Minimum nodes must be at least 1."
  }
}

variable "eks_max_nodes" {
  description = "Maximum number of EKS nodes"
  type        = number
  default     = 50

  validation {
    condition     = var.eks_max_nodes >= var.eks_min_nodes
    error_message = "Maximum nodes must be greater than or equal to minimum nodes."
  }
}

variable "eks_desired_nodes" {
  description = "Desired number of EKS nodes"
  type        = number
  default     = 10

  validation {
    condition     = var.eks_desired_nodes >= var.eks_min_nodes && var.eks_desired_nodes <= var.eks_max_nodes
    error_message = "Desired nodes must be between min and max nodes."
  }
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.xlarge"

  validation {
    condition     = can(regex("^db\\.[a-z][0-9][a-z]?\\.[0-9]*xlarge$", var.rds_instance_class))
    error_message = "RDS instance class must be a valid DB instance type."
  }
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100

  validation {
    condition     = var.rds_allocated_storage >= 20 && var.rds_allocated_storage <= 65536
    error_message = "RDS allocated storage must be between 20 and 65536 GB."
  }
}

variable "rds_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 1000

  validation {
    condition     = var.rds_max_allocated_storage >= var.rds_allocated_storage
    error_message = "RDS max allocated storage must be greater than or equal to allocated storage."
  }
}

variable "rds_backup_retention" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 30

  validation {
    condition     = var.rds_backup_retention >= 1 && var.rds_backup_retention <= 35
    error_message = "RDS backup retention must be between 1 and 35 days."
  }
}

# ============================================================================
# REDIS CONFIGURATION
# ============================================================================

variable "redis_instance_type" {
  description = "Redis instance type"
  type        = string
  default     = "cache.r6g.large"

  validation {
    condition     = can(regex("^cache\\.[a-z][0-9][a-z]?\\.[0-9]*large$", var.redis_instance_type))
    error_message = "Redis instance type must be a valid ElastiCache instance type."
  }
}

variable "redis_cluster_size" {
  description = "Redis cluster size"
  type        = number
  default     = 3

  validation {
    condition     = var.redis_cluster_size >= 1 && var.redis_cluster_size <= 6
    error_message = "Redis cluster size must be between 1 and 6."
  }
}

# ============================================================================
# MONITORING & LOGGING
# ============================================================================

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring and logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 90

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch log retention value."
  }
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 1
    error_message = "Backup retention days must be at least 1."
  }
}

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

variable "enable_encryption" {
  description = "Enable encryption for all resources"
  type        = bool
  default     = true
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = true
}

variable "allowed_ip_ranges" {
  description = "Allowed IP ranges for administrative access"
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for ip in var.allowed_ip_ranges : can(cidrhost(ip, 0))
    ])
    error_message = "All IP ranges must be valid CIDR blocks."
  }
}

# ============================================================================
# COST OPTIMIZATION
# ============================================================================

variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = true
}

variable "reserved_instances" {
  description = "Enable reserved instances for cost optimization"
  type        = bool
  default     = false
}

variable "enable_cost_allocation_tags" {
  description = "Enable cost allocation tags"
  type        = bool
  default     = true
}

# ============================================================================
# TAGS
# ============================================================================

variable "common_tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default = {
    "Project"       = "Aineon"
    "Environment"   = "Production"
    "ManagedBy"     = "Terraform"
    "Certification" = "Top 0.001% Enterprise Grade"
    "Owner"         = "Enterprise Architecture Team"
    "CostCenter"    = "Trading"
    "Backup"        = "Daily"
    "SecurityLevel" = "Critical"
  }
}

# ============================================================================
# ADVANCED CONFIGURATION
# ============================================================================

variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment for high availability"
  type        = bool
  default     = true
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup for disaster recovery"
  type        = bool
  default     = true
}

variable "dr_region" {
  description = "Disaster recovery region"
  type        = string
  default     = "us-west-2"
}

variable "enable_waf" {
  description = "Enable Web Application Firewall"
  type        = bool
  default     = true
}

variable "waf_rule_groups" {
  description = "WAF managed rule groups to enable"
  type        = list(string)
  default = [
    "AWSManagedRulesCommonRuleSet",
    "AWSManagedRulesKnownBadInputsRuleSet",
    "AWSManagedRulesSQLiRuleSet",
    "AWSManagedRulesLinuxRuleSet"
  ]
}

# ============================================================================
# COMPLIANCE & GOVERNANCE
# ============================================================================

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for audit logging"
  type        = bool
  default     = true
}

variable "cloudtrail_retention_days" {
  description = "CloudTrail log retention in days"
  type        = number
  default     = 365

  validation {
    condition     = var.cloudtrail_retention_days >= 90
    error_message = "CloudTrail retention must be at least 90 days for compliance."
  }
}

variable "enable_guardduty" {
  description = "Enable Amazon GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Enable AWS Security Hub for security posture management"
  type        = bool
  default     = true
}

variable "enable_access_analyzer" {
  description = "Enable IAM Access Analyzer"
  type        = bool
  default     = true
}

# ============================================================================
# PERFORMANCE & SCALING
# ============================================================================

variable "enable_autoscaling" {
  description = "Enable auto-scaling for all scalable resources"
  type        = bool
  default     = true
}

variable "autoscaling_target_cpu" {
  description = "Target CPU utilization for auto-scaling"
  type        = number
  default     = 70

  validation {
    condition     = var.autoscaling_target_cpu >= 10 && var.autoscaling_target_cpu <= 90
    error_message = "Auto-scaling target CPU must be between 10% and 90%."
  }
}

variable "autoscaling_target_memory" {
  description = "Target memory utilization for auto-scaling"
  type        = number
  default     = 80

  validation {
    condition     = var.autoscaling_target_memory >= 10 && var.autoscaling_target_memory <= 90
    error_message = "Auto-scaling target memory must be between 10% and 90%."
  }
}

variable "enable_performance_insights" {
  description = "Enable Performance Insights for RDS"
  type        = bool
  default     = true
}

variable "performance_insights_retention" {
  description = "Performance Insights retention period"
  type        = number
  default     = 7

  validation {
    condition     = contains([7, 731], var.performance_insights_retention)
    error_message = "Performance Insights retention must be 7 days or 2 years (731 days)."
  }
}