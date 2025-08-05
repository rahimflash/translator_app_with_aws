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
PROJECT_NAME="translation-platform"

echo -e "${BLUE}🚀 Starting Modular Translation Platform Deployment${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}AWS Region: ${AWS_REGION}${NC}"
echo -e "${BLUE}Project: ${PROJECT_NAME}${NC}"
echo "=" * 60

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed${NC}"
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        exit 1
    fi
    
    # Check if lambda function file exists
    if [ ! -f "lambda_function.py" ]; then
        echo -e "${RED}❌ lambda_function.py not found in root directory${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to setup directory structure
setup_directory() {
    echo -e "${YELLOW}📁 Setting up directory structure...${NC}"
    
    # Create environment directory if it doesn't exist
    mkdir -p "environments/${ENVIRONMENT}"
    
    # Copy environment-specific configuration if it doesn't exist
    if [ ! -f "environments/${ENVIRONMENT}/terraform.tfvars" ]; then
        echo -e "${YELLOW}📝 Creating environment-specific terraform.tfvars...${NC}"
        cp terraform.tfvars.example "environments/${ENVIRONMENT}/terraform.tfvars"
        
        # Update environment in the file
        sed -i.bak "s/environment = \"dev\"/environment = \"${ENVIRONMENT}\"/" "environments/${ENVIRONMENT}/terraform.tfvars"
        sed -i.bak "s/aws_region = \"eu-west-1\"/aws_region = \"${AWS_REGION}\"/" "environments/${ENVIRONMENT}/terraform.tfvars"
        rm "environments/${ENVIRONMENT}/terraform.tfvars.bak" 2>/dev/null || true
        
        echo -e "${YELLOW}⚠️  Please review and edit environments/${ENVIRONMENT}/terraform.tfvars before proceeding${NC}"
        echo "Press Enter to continue after editing terraform.tfvars..."
        read
    fi
    
    echo -e "${GREEN}✅ Directory structure ready${NC}"
}

# Function to validate Terraform
validate_terraform() {
    echo -e "${YELLOW}🔧 Validating Terraform configuration...${NC}"
    
    cd "environments/${ENVIRONMENT}"
    
    # Initialize Terraform
    terraform init
    
    # Validate configuration
    terraform validate
    
    # Format check
    terraform fmt -check=true -recursive
    
    echo -e "${GREEN}✅ Terraform validation passed${NC}"
    
    cd ../..
}

# Function to plan deployment
plan_deployment() {
    echo -e "${YELLOW}📋 Planning deployment...${NC}"
    
    cd "environments/${ENVIRONMENT}"
    
    terraform plan -out=tfplan
    
    echo -e "${BLUE}🤔 Review the plan above. Do you want to proceed with deployment? (yes/no)${NC}"
    read -r response
    
    if [[ "$response" != "yes" ]]; then
        echo -e "${RED}❌ Deployment cancelled${NC}"
        cd ../..
        exit 1
    fi
    
    cd ../..
}

# Function to apply deployment
apply_deployment() {
    echo -e "${YELLOW}🚀 Applying deployment...${NC}"
    
    cd "environments/${ENVIRONMENT}"
    
    terraform apply tfplan
    
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
    
    cd ../..
}

# Function to get outputs and test
get_outputs_and_test() {
    echo -e "${YELLOW}📤 Retrieving deployment outputs...${NC}"
    
    cd "environments/${ENVIRONMENT}"
    
    # Get outputs
    API_ENDPOINT=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")
    INPUT_BUCKET=$(terraform output -raw input_bucket_name 2>/dev/null || echo "")
    OUTPUT_BUCKET=$(terraform output -raw output_bucket_name 2>/dev/null || echo "")
    LAMBDA_FUNCTION=$(terraform output -raw lambda_function_name 2>/dev/null || echo "")
    
    # Handle sensitive output (API key)
    API_KEY=$(terraform output -raw api_key 2>/dev/null || echo "")
    
    cd ../..
    
    echo ""
    echo -e "${GREEN}🎉 Deployment Summary:${NC}"
    echo -e "${BLUE}API Endpoint:${NC} $API_ENDPOINT"
    echo -e "${BLUE}Input Bucket:${NC} $INPUT_BUCKET"
    echo -e "${BLUE}Output Bucket:${NC} $OUTPUT_BUCKET"
    echo -e "${BLUE}Lambda Function:${NC} $LAMBDA_FUNCTION"
    echo -e "${BLUE}API Key:${NC} [HIDDEN - Use 'terraform output api_key' to view]"
    echo ""
    
    # Test the deployment
    if [ -n "$API_ENDPOINT" ] && [ -n "$API_KEY" ]; then
        echo -e "${YELLOW}🧪 Testing the deployment...${NC}"
        
        TEST_PAYLOAD='{
          "source_language": "en",
          "target_languages": ["es", "fr"],
          "sentences": ["Hello world", "This is a test"]
        }'
        
        echo "Sending test request..."
        RESPONSE=$(curl -X POST "$API_ENDPOINT" \
          -H "Content-Type: application/json" \
          -H "X-API-Key: $API_KEY" \
          -d "$TEST_PAYLOAD" \
          --silent --show-error --write-out "HTTPSTATUS:%{http_code}")
        
        HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        HTTP_BODY=$(echo $RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
        
        if [ "$HTTP_STATUS" -eq 200 ]; then
            echo -e "${GREEN}✅ API test successful!${NC}"
            echo "Response: $HTTP_BODY" | python3 -m json.tool 2>/dev/null || echo "$HTTP_BODY"
        else
            echo -e "${RED}❌ API test failed with status: $HTTP_STATUS${NC}"
            echo "Response: $HTTP_BODY"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}📚 Next steps:${NC}"
    echo "1. Configure the CLI tool:"
    echo -e "   ${BLUE}python cli/translation_cli.py configure \\${NC}"
    echo -e "   ${BLUE}  --endpoint $API_ENDPOINT \\${NC}"
    echo -e "   ${BLUE}  --api-key [API_KEY] \\${NC}"
    echo -e "   ${BLUE}  --output-bucket $OUTPUT_BUCKET \\${NC}"
    echo -e "   ${BLUE}  --aws-region $AWS_REGION${NC}"
    echo ""
    echo "2. Test with CLI:"
    echo -e "   ${BLUE}python cli/translation_cli.py translate \\${NC}"
    echo -e "   ${BLUE}  --source-lang en --target-langs es,fr \\${NC}"
    echo -e "   ${BLUE}  --text 'Hello world'${NC}"
    echo ""
    echo "3. Run comprehensive tests:"
    echo -e "   ${BLUE}python testing/test_api.py $API_ENDPOINT $API_KEY${NC}"
    echo ""
    echo "4. Monitor in CloudWatch:"
    echo -e "   ${BLUE}aws logs describe-log-groups --log-group-name-prefix '/aws/lambda/${LAMBDA_FUNCTION}'${NC}"
}

# Function to cleanup on failure
cleanup_on_failure() {
    echo -e "${RED}❌ Deployment failed. Cleaning up...${NC}"
    
    cd "environments/${ENVIRONMENT}" 2>/dev/null || return
    
    if [ -f "tfplan" ]; then
        rm -f tfplan
    fi
    
    echo -e "${YELLOW}🗑️  To destroy resources if needed:${NC}"
    echo -e "   ${BLUE}./deployment/destroy_modular.sh $ENVIRONMENT $AWS_REGION${NC}"
    
    cd ../..
}

# Main execution
main() {
    # Set up trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    check_prerequisites
    setup_directory
    validate_terraform
    plan_deployment
    apply_deployment
    get_outputs_and_test
    
    echo -e "${GREEN}🎉 Modular deployment completed successfully!${NC}"
}

# Run main function
main "$@"