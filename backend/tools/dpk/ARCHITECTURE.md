# DPK Toolkit Architecture

## Overview

The DPK (Development and Pipeline Kit) toolkit provides automation and tooling for POLICYGUARD's development, deployment, and operations workflows. It complements Nova (runtime AI/ML execution) by handling infrastructure automation, configuration management, and deployment pipelines.

## Design Philosophy

### Separation of Concerns

- **DPK**: Handles development infrastructure, deployment automation, configuration management, and DevOps workflows
- **Nova**: Manages runtime AI/ML model execution, orchestration, and inference

These tools work together but remain independent:
- DPK sets up the infrastructure and environment
- Nova runs within that infrastructure to execute AI/ML workloads

## Architecture Components

### 1. Configuration Manager (`config_manager.py`)

**Purpose**: Centralized configuration management for all environments and services.

**Key Features**:
- Environment-specific configuration (development, staging, production)
- Hierarchical configuration with nested access
- Configuration validation
- Support for multiple configuration sources (JSON, YAML, environment variables)

**Usage Example**:
```python
from backend.tools.dpk import ConfigManager

config = ConfigManager('config.json')
db_host = config.get('environments.production.database.host')
config.set('environments.development.debug', True)
```

### 2. Environment Setup (`env_setup.py`)

**Purpose**: Validate and configure development/deployment environments.

**Key Features**:
- AWS credentials validation
- Required dependencies checking
- Environment variable setup
- Virtual environment management
- Automated environment repair

**Validation Checks**:
- Python version compatibility
- AWS SDK (boto3) installation
- AWS credentials configuration
- Required environment variables
- Network connectivity to AWS services

**Usage Example**:
```python
from backend.tools.dpk import EnvironmentValidator, ConfigManager

config = ConfigManager()
validator = EnvironmentValidator(config)

# Validate environment
results = validator.validate_all()

# Auto-setup if issues found
if not all(r['valid'] for r in results.values()):
    validator.setup_environment()
```

### 3. Deployment Manager (`deployment.py`)

**Purpose**: Automate infrastructure deployment and manage deployment lifecycle.

**Key Features**:
- Infrastructure deployment (Lambda, API Gateway, RDS, monitoring)
- Deployment verification and health checks
- Rollback capabilities
- Deployment history tracking
- Multi-environment support

**Deployment Flow**:
1. Validate environment configuration
2. Deploy infrastructure components:
   - Lambda functions
   - API Gateway endpoints
   - Database resources
   - CloudWatch monitoring and alarms
3. Verify deployment health
4. Log deployment metadata

**Usage Example**:
```python
from backend.tools.dpk import DeploymentManager, ConfigManager

config = ConfigManager()
deployer = DeploymentManager(config)

# Deploy to production
result = deployer.deploy_infrastructure('production')

# Verify deployment
health = deployer.verify_deployment('production')

# Rollback if needed
if health['status'] != 'healthy':
    deployer.rollback_deployment(result['deployment_id'])
```

### 4. Command-Line Interface (`cli.py`)

**Purpose**: Provide developer-friendly CLI for all DPK operations.

**Command Structure**:
```
dpk
├── config              # Configuration management
│   ├── init           # Initialize configuration
│   ├── get            # Get configuration value
│   └── set            # Set configuration value
├── env                 # Environment management
│   ├── validate       # Validate environment setup
│   └── setup          # Set up development environment
├── deploy              # Deployment operations
│   ├── infrastructure # Deploy infrastructure
│   ├── verify         # Verify deployment health
│   └── rollback       # Rollback deployment
└── info                # Display toolkit information
```

**Usage Examples**:
```bash
# Initialize development environment
dpk config init --environment development

# Validate environment
dpk env validate --fix

# Deploy to production
dpk deploy infrastructure --environment production

# Verify deployment
dpk deploy verify --environment production

# Get configuration value
dpk config get environments.production.database.host
```

## Integration with POLICYGUARD

### Directory Structure
```
POLICYGUARD-/
├── backend/
│   ├── tools/
│   │   ├── dpk/              # DPK Toolkit (this package)
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   ├── config_manager.py
│   │   │   ├── deployment.py
│   │   │   ├── env_setup.py
│   │   │   └── ARCHITECTURE.md
│   │   └── nova/             # Nova AI/ML Runtime (separate)
│   ├── agents/               # Policy compliance agents
│   ├── models/               # Data models
│   └── services/             # Business logic services
```

### Workflow Integration

#### Development Workflow
1. Developer runs `dpk env setup` to configure local environment
2. Developer uses `dpk config` to manage configuration
3. Developer tests changes locally
4. Developer runs `dpk deploy infrastructure --environment development` to deploy to dev environment
5. Developer uses `dpk deploy verify` to check deployment health

#### CI/CD Pipeline
1. Code pushed to repository
2. CI pipeline runs `dpk env validate` to check environment
3. CI pipeline runs tests
4. On success, `dpk deploy infrastructure --environment staging` deploys to staging
5. `dpk deploy verify --environment staging` validates staging deployment
6. Manual approval gate
7. `dpk deploy infrastructure --environment production` deploys to production
8. `dpk deploy verify --environment production` validates production
9. If verification fails, `dpk deploy rollback` reverts changes

## Configuration Schema

### Environment Configuration
```json
{
  "environments": {
    "development": {
      "name": "development",
      "region": "us-east-1",
      "lambda": {
        "functions": [
          {
            "name": "policyguard-compliance-agent",
            "runtime": "python3.9",
            "handler": "agent.handler",
            "timeout": 300
          }
        ]
      },
      "api_gateway": {
        "name": "policyguard-api-dev",
        "stage": "dev"
      },
      "database": {
        "type": "RDS",
        "engine": "postgres",
        "instance_class": "db.t3.micro"
      },
      "monitoring": {
        "enabled": true,
        "alarms": [
          {
            "name": "HighErrorRate",
            "metric": "Errors",
            "threshold": 10
          }
        ]
      }
    },
    "production": {
      "name": "production",
      "region": "us-east-1",
      "lambda": { /* ... */ },
      "api_gateway": { /* ... */ },
      "database": { /* ... */ },
      "monitoring": { /* ... */ }
    }
  }
}
```

## DPK vs Nova: Complementary Tools

| Aspect | DPK | Nova |
|--------|-----|------|
| **Purpose** | Infrastructure & DevOps | AI/ML Runtime & Orchestration |
| **Scope** | Project setup, deployment, pipelines | Model execution, inference |
| **When Used** | Development, CI/CD, infrastructure changes | Runtime, during application execution |
| **Example Tasks** | Deploy Lambda, configure RDS, set up monitoring | Run ML models, process predictions, orchestrate AI workflows |
| **Target Users** | DevOps engineers, developers | Data scientists, ML engineers, application runtime |
| **Dependencies** | boto3, click, pyyaml | Bedrock, ML frameworks, model libraries |

### Typical Workflow
1. **DPK** sets up the infrastructure: Lambda functions, databases, API Gateway
2. **DPK** deploys the application code including Nova components
3. **Nova** runs inside the deployed infrastructure to handle AI/ML workloads
4. **DPK** monitors and manages the infrastructure health
5. **Nova** focuses on model performance and inference quality

## Error Handling & Logging

All DPK modules implement consistent error handling:

- **Validation Errors**: Raised early with clear messages
- **Deployment Errors**: Logged with full context, support rollback
- **Configuration Errors**: Validated before any operations
- **Logging**: Structured logs with timestamps, levels, and context

## Security Considerations

1. **Credentials**: Never store AWS credentials in code or configuration files
2. **Configuration**: Sensitive values should use environment variables or AWS Secrets Manager
3. **Deployment**: Use IAM roles with least privilege access
4. **Validation**: All inputs validated before processing

## Extensibility

DPK is designed to be extended:

1. **New Modules**: Add new `.py` files to `backend/tools/dpk/`
2. **New Commands**: Add new CLI commands in `cli.py`
3. **Custom Validators**: Extend `EnvironmentValidator` with additional checks
4. **Deployment Targets**: Add new infrastructure types in `DeploymentManager`

## Future Enhancements

- [ ] Terraform integration for infrastructure as code
- [ ] Multi-region deployment support
- [ ] Blue-green deployment strategy
- [ ] Canary deployments
- [ ] Automated rollback on failure detection
- [ ] Cost estimation for deployments
- [ ] Performance benchmarking tools
- [ ] Integration with GitHub Actions
- [ ] Docker container support
- [ ] Kubernetes deployment options

## Contributing

When contributing to DPK:

1. Follow existing code structure and patterns
2. Add comprehensive docstrings
3. Include type hints
4. Add error handling for all operations
5. Update this ARCHITECTURE.md with significant changes
6. Ensure CLI commands follow the established command structure

## Support

For questions or issues:
- Review this documentation
- Run `dpk info` for toolkit information
- Run `dpk <command> --help` for command-specific help
- Check deployment logs for error details
