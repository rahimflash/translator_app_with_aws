# README.md for modular structure
# Translation Platform - Modular Terraform Structure

## 📁 Directory Structure

```
terraform/
├── main.tf                    # Root configuration with module calls
├── variables.tf               # Root variables
├── outputs.tf                 # Root outputs
├── lambda_function.py         # Lambda function code
├── terraform.tfvars.example   # Example configuration
├── modules/
│   ├── iam/                   # IAM roles and policies
│   │   ├── main.tf
│   │   └── outputs.tf
│   ├── s3/                    # S3 buckets and configurations
│   │   ├── main.tf
│   │   └── outputs.tf
│   ├── lambda/                # Lambda function and logs
│   │   ├── main.tf
│   │   └── outputs.tf
│   └── api-gateway/           # API Gateway and related resources
│       ├── main.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf            # Dev environment configuration
│   │   └── terraform.tfvars   # Dev-specific variables
│   └── prod/
│       ├── main.tf            # Prod environment configuration
│       └── terraform.tfvars   # Prod-specific variables
└── deployment/
    ├── deploy_modular.sh      # Deployment script
    ├── destroy_modular.sh     # Destruction script
    └── validate_modular.sh    # Validation script
```

## 🚀 Quick Start

### 1. Deploy Development Environment

```bash
# Clone and navigate to terraform directory
cd terraform/

# Deploy dev environment
make apply-dev
# OR
./deployment/deploy_modular.sh dev eu-west-1
```

### 2. Deploy Production Environment

```bash
# Deploy prod environment
make apply-prod
# OR
./deployment/deploy_modular.sh prod eu-west-1
```

### 3. Validate Configuration

```bash
# Validate all modules and environments
make validate
# OR
./deployment/validate_modular.sh
```

## 🔧 Module Breakdown

### **IAM Module (`modules/iam/`)**
- **Purpose**: Manages IAM roles and policies
- **Resources**:
  - Lambda execution role
  - S3 access policies
  - Translate service permissions
- **Outputs**: Role ARNs for other modules

### **S3 Module (`modules/s3/`)**
- **Purpose**: Manages S3 buckets for input/output
- **Resources**:
  - Input bucket with versioning
  - Output bucket with versioning
  - Encryption configurations
  - Public access blocks
  - Lifecycle policies
- **Outputs**: Bucket names and ARNs

### **Lambda Module (`modules/lambda/`)**
- **Purpose**: Manages Lambda function and logging
- **Resources**:
  - Lambda function with environment variables
  - CloudWatch log group
  - Function packaging
- **Outputs**: Function ARN and name

### **API Gateway Module (`modules/api-gateway/`)**
- **Purpose**: Manages API Gateway and related resources
- **Resources**:
  - REST API with validation
  - CORS configuration
  - Usage plans and API keys
  - Lambda integration
- **Outputs**: API endpoint URL and keys

## 🌍 Environment Management

### Development Environment (`environments/dev/`)
- **Characteristics**:
  - Lower resource limits
  - Shorter log retention (7 days)
  - Reduced API quotas
  - Smaller Lambda memory allocation

### Production Environment (`environments/prod/`)
- **Characteristics**:
  - Higher resource limits
  - Longer log retention (30 days)
  - Higher API quotas
  - Larger Lambda memory allocation
  - Enhanced monitoring

## 📋 Common Commands

```bash
# Validate all configurations
make validate

# Development workflow
make dev-workflow    # Validate, init, and plan dev
make apply-dev       # Apply dev environment

# Production workflow  
make prod-workflow   # Validate, init, and plan prod
make apply-prod      # Apply prod environment

# Testing
make test ENDPOINT=https://api-url API_KEY=key

# Cleanup
make destroy-dev     # Destroy dev environment
make destroy-prod    # Destroy prod environment
make clean          # Clean temporary files
```

## 🔒 Security Features

- **Least Privilege IAM**: Each module has minimal required permissions
- **Resource Isolation**: Separate state files per environment
- **Encrypted Storage**: S3 buckets encrypted by default
- **API Security**: API keys and rate limiting
- **Network Security**: Private API endpoints option

## 📊 Benefits of Modular Structure

1. **Reusability**: Modules can be reused across environments
2. **Maintainability**: Easier to update specific components
3. **Testing**: Individual modules can be tested separately
4. **Scalability**: Easy to add new environments or modify existing ones
5. **Collaboration**: Teams can work on different modules independently
6. **State Management**: Separate state files reduce blast radius

## 🔄 Deployment Workflow

1. **Validate** all configurations
2. **Initialize** Terraform for target environment
3. **Plan** deployment and review changes
4. **Apply** changes after approval
5. **Test** deployed infrastructure
6. **Monitor** through CloudWatch

## 📈 Scaling Considerations

- **Multi-Region**: Easy to replicate in different regions
- **Multi-Account**: Can be deployed across AWS accounts
- **Module Versioning**: Pin module versions for stability
- **State Locking**: Use remote state with DynamoDB locking
- **CI/CD Integration**: Easily integrated with GitLab/GitHub Actions

## 🛠️ Customization

Each environment can be customized by modifying the respective `terraform.tfvars`:

```hcl
# environments/dev/terraform.tfvars
environment = "dev"
lambda_memory_size = 256
api_rate_limit = 50
log_retention_days = 7

# environments/prod/terraform.tfvars
environment = "prod"
lambda_memory_size = 1024
api_rate_limit = 500
log_retention_days = 30
```