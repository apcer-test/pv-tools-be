# APCER Infrastructure

A comprehensive AWS infrastructure project built with Terraform, providing a production-ready environment with containerized applications, databases, security services, and CI/CD pipelines.

## Overview

This project creates a complete AWS infrastructure stack including:

- **Networking**: VPC, subnets, security groups
- **Compute**: ECS Fargate services with auto-scaling
- **Storage**: S3 buckets, RDS database, ElastiCache Redis
- **Security**: WAF, GuardDuty, Inspector, Security Hub, IAM
- **Monitoring**: CloudWatch, CloudTrail, X-Ray, Synthetics
- **CDN**: CloudFront distributions
- **CI/CD**: CodePipeline with CodeBuild
- **DNS**: Route53 hosted zones and records
- **Backup**: AWS Backup vault and plans

## Prerequisites

- Terraform >= 1.9.0
- AWS CLI configured with appropriate credentials
- AWS S3 bucket for Terraform state storage
- GitLab account (for CodePipeline connections)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pv-tool-infra
```

### 2. Configure Backend

Update `main/backend.hcl` with your S3 bucket details:

```hcl
bucket         = "your-terraform-state-bucket"
key            = "your-project/terraform.tfstate"
region         = "your-backend-region"
encrypt        = true
```

### 3. Configure Variables

Edit `main/terraform.tfvars` with your specific values:

```hcl
region = "us-east-2"
project_name = "your-project"
env = "dev"

# Update domain names
route53_domain_name = "your-domain.com"
domain_name = "your-domain.com"

# Update ACM certificate ARN for CloudFront
cloudfront_acm_certificate_arn = "arn:aws:acm:us-east-1:YOUR-ACCOUNT:certificate/YOUR-CERT-ID"
```

### 4. Initialize Terraform

```bash
cd main
terraform init -backend-config=../backend.hcl
```

### 5. Plan and Apply

```bash
terraform plan
terraform apply
```
NOTE: we'll add targeted tfvars when moving to other enviroment

## Infrastructure Components

### Core Services

| Service | Description | Module |
|---------|-------------|---------|
| VPC | Virtual Private Cloud with public/private subnets | `modules/vpc` |
| ECS Fargate | Container orchestration with auto-scaling | `modules/ecs-fargate` |
| Application Load Balancer | Traffic distribution to ECS services | `modules/alb` |
| RDS PostgreSQL | Managed database with backup and monitoring | `modules/rds` |
| ElastiCache Redis | In-memory caching layer | `modules/elasticache-redis` |
| S3 | Object storage for static assets and artifacts | `modules/s3` |
| CloudFront | Global content delivery network | `modules/cloudfront` |

### Security Services

| Service | Description | Module |
|---------|-------------|---------|
| WAF | Web Application Firewall protection | `modules/security` |
| GuardDuty | Threat detection and monitoring | `modules/security` |
| Inspector | Security vulnerability assessment | `modules/security` |
| Security Hub | Security findings aggregation | `modules/security` |
| IAM | Identity and access management | `modules/iam` |
| CloudTrail | API activity logging | `modules/cloudtrail` |

### Monitoring & Observability

| Service | Description | Module |
|---------|-------------|---------|
| CloudWatch | Metrics, logs, and alarms | `modules/cloudwatch` |
| X-Ray | Distributed tracing for ECS services | `modules/ecs-fargate` |
| Synthetics | Automated health checks | `modules/cloudwatch-synthetics` |
| AWS Backup | Automated backup and recovery | `modules/aws-backup` |
| AWS Budgets | Cost monitoring and alerts | `modules/aws-budgets` |
| AWS VPN | Client VPN and Site-to-Site VPN | `modules/aws-vpn` |

### CI/CD & DevOps

| Service | Description | Module |
|---------|-------------|---------|
| CodePipeline | Automated deployment pipelines | `modules/code-pipeline` |
| CodeBuild | Build and test automation | `modules/code-pipeline` |
| ECR | Container image registry | `modules/ecr` |


### Authentication & Messaging

| Service | Description | Module |
|---------|-------------|---------|
| Cognito | User authentication and authorization | `modules/cognito` |


## Configuration

### Environment Variables

Key configuration variables in `terraform.tfvars`:

- `region`: AWS region for deployment
- `project_name`: Project identifier used in resource naming
- `env`: Environment name (dev, staging, prod)
- `route53_domain_name`: Primary domain for DNS management
- `cloudfront_acm_certificate_arn`: SSL certificate for CloudFront

### ECS Services Configuration

Services are configured in the `services` block:

```hcl
services = {
  service1 = {
    container_name      = "api"
    container_port      = 8000
    cpu                 = 480
    memory              = 768
    domain              = "api-test.your-domain.com"
    enable_xray         = true
    create_cloudfront   = true
  }
}
```

### Frontend Configuration

Static frontends are configured in the `frontends` block:

```hcl
frontends = {
  admin = {
    service_name         = "admin"
    domain              = "admin-test.your-domain.com"
    repository_path     = "your-org/your-admin-repo"
    create_codepipeline = true
    enable_oac         = true
  }
}
```

## Security Features

- **Network Security**: Private subnets, security groups
- **Application Security**: WAF rules, HTTPS enforcement, secure headers
- **Identity Security**: IAM roles, Cognito authentication, least privilege access
- **Monitoring Security**: CloudTrail logging, GuardDuty threat detection
- **Data Security**: RDS encryption, S3 encryption, backup encryption

## Monitoring & Alerting

- **Application Monitoring**: CloudWatch metrics for ECS services
- **Infrastructure Monitoring**: CPU, memory, disk, network metrics
- **Security Monitoring**: GuardDuty findings, WAF blocked requests
- **Health Checks**: Route53 health checks, CloudWatch Synthetics
- **Logging**: Centralized logging with CloudWatch Logs

## Backup & Recovery

- **Database Backups**: Automated RDS snapshots with retention policies
- **Application Backups**: AWS Backup for ECS, S3, and other resources
- **Disaster Recovery**: Multi-AZ deployments, cross-region backups

## Cost Optimization

- **Resource Scheduling**: Auto-scaling based on demand
- **Storage Optimization**: S3 lifecycle policies, RDS storage optimization
- **Compute Optimization**: Fargate spot instances (configurable)
- **Monitoring**: Cost alerts and budget tracking

## Troubleshooting

### Common Issues

1. **Terraform State Lock**: If state is locked, check for running Terraform processes
2. **Provider Version Conflicts**: Ensure all modules use compatible provider versions
3. **IAM Permissions**: Verify AWS credentials have required permissions
4. **VPC Limits**: Check AWS account limits for VPC resources

### Useful Commands

```bash
# Validate Terraform configuration
terraform validate

# Check current state
terraform show

# List resources
terraform state list

# Import existing resources
terraform import <resource_address> <resource_id>

# Destroy specific resources
terraform destroy -target=module.vpc
```