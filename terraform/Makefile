# Makefile

.PHONY: help validate init-dev init-prod plan-dev plan-prod apply-dev apply-prod destroy-dev destroy-prod test clean

# Default environment
ENV ?= dev
REGION ?= eu-west-1

help:
	@echo "Translation Platform Modular Commands:"
	@echo "  validate        - Validate all Terraform configurations"
	@echo "  init-dev        - Initialize dev environment"
	@echo "  init-prod       - Initialize prod environment"
	@echo "  plan-dev        - Plan dev deployment"
	@echo "  plan-prod       - Plan prod deployment"
	@echo "  apply-dev       - Apply dev deployment"
	@echo "  apply-prod      - Apply prod deployment"
	@echo "  destroy-dev     - Destroy dev environment"
	@echo "  destroy-prod    - Destroy prod environment"
	@echo "  test           - Run API tests (requires ENDPOINT and API_KEY)"
	@echo "  clean          - Clean temporary files"

validate:
	@../deployment/validate.sh

init-dev:
	@cd environments/dev && terraform init

init-prod:
	@cd environments/prod && terraform init

plan-dev:
	@cd environments/dev && terraform plan

plan-prod:
	@cd environments/prod && terraform plan

apply-dev:
	@./deployment/deploy.sh dev $(REGION)

apply-prod:
	@./deployment/deploy.sh prod $(REGION)

destroy-dev:
	@./deployment/destroy.sh dev $(REGION)

destroy-prod:
	@./deployment/destroy.sh prod $(REGION)

test:
	@if [ -z "$(ENDPOINT)" ] || [ -z "$(API_KEY)" ]; then \
		echo "Error: ENDPOINT and API_KEY variables required"; \
		echo "Usage: make test ENDPOINT=https://your-api-endpoint API_KEY=your-key"; \
		exit 1; \
	fi
	@python3 ../testing/test_api.py $(ENDPOINT) $(API_KEY)

clean:
	@find . -name "*.tfstate*" -delete
	@find . -name ".terraform" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "tfplan" -delete
	@find . -name "lambda_function.zip" -delete
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Quick deployment targets
quick-dev: init-dev apply-dev
quick-prod: init-prod apply-prod

# Development workflow
dev-workflow: validate init-dev plan-dev
	@echo "Review the plan above, then run 'make apply-dev' to deploy"

prod-workflow: validate init-prod plan-prod
	@echo "Review the plan above, then run 'make apply-prod' to deploy"

