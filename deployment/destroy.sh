#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${2:-eu-west-1}

echo -e "${RED}🗑️  Starting Translation Platform Destruction${NC}"
echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"
echo -e "${YELLOW}AWS Region: $AWS_REGION${NC}"

echo ""
echo -e "${RED}⚠️  WARNING: This will destroy ALL resources for environment: $ENVIRONMENT${NC}"
echo -e "${RED}⚠️  This action CANNOT be undone!${NC}"
echo ""
echo -e "${YELLOW}Type 'DESTROY' to confirm destruction:${NC}"
read -r confirmation

if [[ "$confirmation" != "DESTROY" ]]; then
    echo -e "${GREEN}❌ Destruction cancelled${NC}"
    exit 1
fi

# Check if environment directory exists
if [ ! -d "environments/${ENVIRONMENT}" ]; then
    echo -e "${RED}❌ Environment directory not found: environments/${ENVIRONMENT}${NC}"
    exit 1
fi

cd "environments/${ENVIRONMENT}"

echo -e "${YELLOW}🔍 Planning destruction...${NC}"
terraform plan -destroy

echo ""
echo -e "${RED}🗑️  Proceeding with destruction...${NC}"
terraform destroy -auto-approve

echo -e "${GREEN}✅ Infrastructure destroyed successfully${NC}"

cd ../..