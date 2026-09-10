# POLICYGUARD Architecture: Dual-Tool System

## Overview

POLICYGUARD uses a **dual-tool architecture** that separates runtime AI operations from development automation:

- **Nova**: AI/ML Model Orchestration and Runtime
- **DPK**: Development and Project Kit for Automation

## Why Two Separate Tools?

The previous attempt incorrectly **renamed** Nova to DPK, which was semantically wrong. The correct architecture maintains **both tools** as independent, complementary systems:

### Nova's Role (Runtime)
- Handles **AI model orchestration** via Amazon Bedrock
- Performs **inference** and **compliance analysis**
- Manages **model invocation** and response parsing
- Provides **LLM-based decision making**
- **Location**: `backend/services/bedrock_client.py`, `backend/agents/compliance_agent.py`

### DPK's Role (Development)
- Handles **project configuration** management
- Automates **environment setup** and validation
- Manages **deployment pipelines**
- Provides **infrastructure automation** utilities
- **Location**: `backend/tools/dpk/`

---

## Implementation Status

### ✅ Completed

#### Nova (Fully Implemented)
1. **`backend/services/bedrock_client.py`**
   - `BedrockNovaClient` class
   - Model invocation wrapper
   - Response parsing and error handling
   - Singleton pattern for global access

2. **`backend/agents/compliance_agent.py`**
   - `call_nova_for_compliance()` function
   - Transaction compliance analysis
   - Policy validation logic
   - Integration with OpenSearch for policy retrieval

#### DPK (Partially Implemented)
1. **`backend/tools/dpk/__init__.py`**
   - Package initialization
   - Module exports
   - Version management

2. **`backend/tools/dpk/config_manager.py`**
   - `ConfigManager` class
   - Environment-specific config loading
   - YAML/JSON config support
   - Config validation
   - AWS and database config helpers

### ⏳ To Be Implemented

#### DPK Remaining Modules

3. **`backend/tools/dpk/env_setup.py`**
   ```python
   class EnvironmentSetup:
       """Validates and sets up development environment"""
       - Check required environment variables
       - Validate AWS credentials
       - Verify database connectivity
       - Check Python dependencies
       - Setup development certificates
   ```

4. **`backend/tools/dpk/deployment.py`**
   ```python
   class DeploymentAutomation:
       """Automates deployment to different environments"""
       - Deploy to development/staging/production
       - Run database migrations
       - Update environment configurations
       - Deploy Lambda functions
       - Update API Gateway
   ```

5. **`backend/tools/dpk/cli.py`** (Optional)
   ```python
   # Command-line interface for DPK
   dpk setup      # Setup development environment
   dpk config     # Manage configurations
   dpk deploy     # Deploy to environments
   dpk validate   # Validate project setup
   ```

---

## Directory Structure

```
POLICYGUARD/
├── backend/
│   ├── agents/
│   │   └── compliance_agent.py      # ✅ Nova integration
│   ├── services/
│   │   └── bedrock_client.py        # ✅ Nova client
│   └── tools/
│       └── dpk/                      # DPK toolkit
│           ├── __init__.py           # ✅ Package init
│           ├── config_manager.py    # ✅ Config management
│           ├── env_setup.py          # ⏳ To implement
│           ├── deployment.py         # ⏳ To implement
│           └── cli.py                # ⏳ Optional CLI
├── config/                           # Configuration files
│   ├── aws.yaml
│   ├── aws.development.yaml
│   ├── aws.production.yaml
│   └── database.yaml
└── ARCHITECTURE.md                   # This file
```

---

## Usage Examples

### Using Nova (Runtime AI)

```python
from backend.services.bedrock_client import get_bedrock_client
from backend.agents.compliance_agent import call_nova_for_compliance

# Get AI model client
client = get_bedrock_client()

# Analyze transaction compliance
result = call_nova_for_compliance(
    transaction_data=transaction,
    retrieved_policies=policies
)

print(result["verdict"])  # "Compliant" | "Non-Compliant" | "Manual Review"
```

### Using DPK (Development Automation)

```python
from backend.tools.dpk import ConfigManager, EnvironmentSetup, DeploymentAutomation

# Load configuration
config = ConfigManager()
aws_config = config.get_aws_config(env="production")

# Setup environment
env_setup = EnvironmentSetup()
env_setup.validate_environment()
env_setup.check_aws_credentials()

# Deploy to production
deployment = DeploymentAutomation()
deployment.deploy_to_environment("production")
```

---

## Key Principles

### 1. **Separation of Concerns**
- Nova focuses on **runtime operations**
- DPK focuses on **development operations**
- No overlap in responsibilities

### 2. **Independence**
- Nova can function without DPK
- DPK can function without Nova
- Both are optional but complementary

### 3. **Clear Naming**
- Nova = AI model orchestration
- DPK = Development and Project Kit
- Never rename one to the other

### 4. **Production vs Development**
- Nova is used in production runtime
- DPK is primarily used during development/deployment
- DPK helps setup/deploy Nova

---

## Environment Variables

### Nova (Runtime)
```bash
NOVA_MODEL_ID=amazon.nova-micro-v1:0
BEDROCK_REGION=us-east-1
```

### DPK (Development)
```bash
DPK_ENV=development  # development | staging | production
DPK_CONFIG_DIR=/path/to/config
```

---

## Next Steps for Full Implementation

1. **Implement `env_setup.py`**
   - Environment validation
   - Credential checking
   - Dependency verification

2. **Implement `deployment.py`**
   - Automated deployments
   - Migration management
   - Configuration updates

3. **Create config files**
   - `config/aws.yaml`
   - `config/database.yaml`
   - Environment-specific variants

4. **Write tests**
   - Unit tests for DPK modules
   - Integration tests for workflows

5. **Update README.md**
   - Document dual-tool architecture
   - Add usage examples
   - Setup instructions

---

## Benefits of This Architecture

✅ **Clear Separation**: Runtime vs Development concerns  
✅ **Maintainability**: Each tool has focused responsibility  
✅ **Scalability**: Tools can evolve independently  
✅ **Team Understanding**: Clear naming eliminates confusion  
✅ **Backward Compatibility**: Nova implementation preserved  

---

## Questions?

For questions about:
- **Nova (AI/ML)**: See `backend/services/bedrock_client.py`
- **DPK (Automation)**: See `backend/tools/dpk/`
- **Architecture**: This document

Last Updated: January 24, 2026
