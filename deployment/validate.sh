#!/bin/bash

set -e

# Colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🔍 Validating Modular Terraform Structure${NC}"
terraform fmt -recursive

# Function to validate module structure
validate_module() {
    local module_path=$1
    local module_name=$2
    
    echo -e "${YELLOW}Checking module: ${module_name}${NC}"
    
    # Check required files
    required_files=("main.tf" "outputs.tf")
    for file in "${required_files[@]}"; do
        if [ ! -f "${module_path}/${file}" ]; then
            echo -e "${RED}❌ Missing ${file} in ${module_name}${NC}"
            return 1
        fi
    done
    
    # Format terraform syntax
    cd "$module_path"
    if terraform fmt -recursive > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${module_name} Formatting passed${NC}"
    else
        echo -e "${RED}❌ ${module_name} Formatting failed${NC}"
        terraform fmt -recursive
        return 1
    fi
    cd - > /dev/null

    # Validate terraform syntax
    cd "$module_path"
    if terraform validate > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${module_name} validation passed${NC}"
    else
        echo -e "${RED}❌ ${module_name} validation failed${NC}"
        terraform validate
        return 1
    fi
    cd - > /dev/null
}

# Validate environment configurations
environments=("environments/dev" "environments/prod")
for env in "${environments[@]}"; do
    if [ -d "$env" ]; then
        echo -e "${YELLOW}Validating environment: $(basename $env)${NC}"
        cd "$env"
        if terraform validate > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $(basename $env) environment valid${NC}"
        else
            echo -e "${RED}❌ $(basename $env) environment invalid${NC}"
            terraform validate
            exit 1
        fi
        cd - > /dev/null
    fi
done

echo -e "${GREEN}🎉 All validations passed!${NC}"
