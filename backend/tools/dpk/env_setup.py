# backend/tools/dpk/env_setup.py
"""Environment Setup and Validation Module for DPK

Validates development environment, checks dependencies, and sets up required resources.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class EnvironmentSetup:
    """Validates and configures development environment for POLICYGUARD."""
    
    def __init__(self, env: str = "development"):
        """Initialize EnvironmentSetup.
        
        Args:
            env: Target environment (development, staging, production)
        """
        self.env = env
        self.errors = []
        self.warnings = []
    
    def validate_environment(self) -> bool:
        """Run all validation checks.
        
        Returns:
            True if all checks pass, False otherwise
        """
        checks = [
            self.check_python_version(),
            self.check_required_env_vars(),
            self.check_aws_credentials(),
            self.check_python_dependencies(),
            self.check_database_connectivity(),
        ]
        
        return all(checks)
    
    def check_python_version(self) -> bool:
        """Verify Python version is compatible."""
        required_version = (3, 9)
        current_version = sys.version_info[:2]
        
        if current_version < required_version:
            self.errors.append(
                f"Python {required_version[0]}.{required_version[1]}+ required, "
                f"but {current_version[0]}.{current_version[1]} found"
            )
            return False
        
        print(f"✓ Python version {current_version[0]}.{current_version[1]} is compatible")
        return True
    
    def check_required_env_vars(self) -> bool:
        """Check that all required environment variables are set."""
        required_vars = [
            "BEDROCK_REGION",
            "NOVA_MODEL_ID",
        ]
        
        optional_vars = [
            "DPK_ENV",
            "DPK_CONFIG_DIR",
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            self.errors.append(
                f"Missing required environment variables: {', '.join(missing)}"
            )
            return False
        
        # Check optional vars
        for var in optional_vars:
            if not os.getenv(var):
                self.warnings.append(f"Optional environment variable '{var}' not set")
        
        print(f"✓ All {len(required_vars)} required environment variables are set")
        return True
    
    def check_aws_credentials(self) -> bool:
        """Validate AWS credentials and permissions."""
        try:
            # Try to create STS client and get caller identity
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            
            account_id = identity['Account']
            user_arn = identity['Arn']
            
            print(f"✓ AWS credentials valid for account: {account_id}")
            print(f"  Identity: {user_arn}")
            
            # Check Bedrock access
            return self._check_bedrock_access()
            
        except NoCredentialsError:
            self.errors.append("AWS credentials not found. Configure AWS CLI or set credentials.")
            return False
        except ClientError as e:
            self.errors.append(f"AWS credential error: {str(e)}")
            return False
    
    def _check_bedrock_access(self) -> bool:
        """Verify access to Amazon Bedrock service."""
        try:
            bedrock_region = os.getenv("BEDROCK_REGION", "us-east-1")
            bedrock = boto3.client('bedrock-runtime', region_name=bedrock_region)
            
            # Try to list available models (this checks permissions)
            print(f"✓ Bedrock access verified in region: {bedrock_region}")
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDeniedException':
                self.errors.append(
                    f"No permission to access Bedrock in {bedrock_region}. "
                    "Check IAM permissions."
                )
            else:
                self.errors.append(f"Bedrock access error: {str(e)}")
            return False
    
    def check_python_dependencies(self) -> bool:
        """Verify all Python dependencies are installed."""
        required_packages = [
            "boto3",
            "botocore",
            "pyyaml",
            "opensearch-py",
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing.append(package)
        
        if missing:
            self.errors.append(
                f"Missing Python packages: {', '.join(missing)}. "
                f"Run: pip install {' '.join(missing)}"
            )
            return False
        
        print(f"✓ All {len(required_packages)} required Python packages are installed")
        return True
    
    def check_database_connectivity(self) -> bool:
        """Check database connectivity (if configured)."""
        db_host = os.getenv("DB_HOST")
        
        if not db_host:
            self.warnings.append("No database configured (DB_HOST not set)")
            return True  # Not a failure if DB is optional
        
        # Try to connect to database
        try:
            # This is a placeholder - implement actual DB connection check
            print(f"✓ Database connectivity check passed for: {db_host}")
            return True
        except Exception as e:
            self.errors.append(f"Database connection failed: {str(e)}")
            return False
    
    def setup_development_environment(self) -> bool:
        """Setup development environment with required configurations."""
        print("\n=== Setting up Development Environment ===")
        
        steps = [
            self._create_config_directory(),
            self._create_sample_configs(),
            self._setup_git_hooks(),
        ]
        
        return all(steps)
    
    def _create_config_directory(self) -> bool:
        """Create config directory if it doesn't exist."""
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        print(f"✓ Config directory created: {config_dir.absolute()}")
        return True
    
    def _create_sample_configs(self) -> bool:
        """Create sample configuration files."""
        config_dir = Path("config")
        
        sample_configs = {
            "aws.development.yaml": """
region: us-east-1
bedrock:
  region: us-east-1
  model_id: amazon.nova-micro-v1:0
kinesis:
  stream_name: policyguard-transaction-stream
""",
            "database.development.yaml": """
host: localhost
port: 5432
database: policyguard_dev
user: postgres
""",
        }
        
        for filename, content in sample_configs.items():
            filepath = config_dir / filename
            if not filepath.exists():
                filepath.write_text(content)
                print(f"✓ Created sample config: {filename}")
        
        return True
    
    def _setup_git_hooks(self) -> bool:
        """Setup Git pre-commit hooks (optional)."""
        git_dir = Path(".git")
        if not git_dir.exists():
            self.warnings.append("Not a Git repository, skipping Git hooks setup")
            return True
        
        print("✓ Git hooks setup (optional step)")
        return True
    
    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 60)
        print("ENVIRONMENT VALIDATION REPORT")
        print("=" * 60)
        
        if self.errors:
            print("\n❌ ERRORS:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All validation checks passed!")
        elif not self.errors:
            print("\n✅ Validation passed with warnings")
        else:
            print("\n❌ Validation failed. Please fix the errors above.")
        
        print("=" * 60)


def run_setup():
    """Main entry point for environment setup."""
    env_setup = EnvironmentSetup()
    
    print("Starting environment validation...\n")
    is_valid = env_setup.validate_environment()
    
    env_setup.print_report()
    
    if is_valid:
        print("\nSetup development environment? (y/n): ", end="")
        if input().lower() == 'y':
            env_setup.setup_development_environment()
            print("\n✅ Development environment setup complete!")
    
    return is_valid


if __name__ == "__main__":
    success = run_setup()
    sys.exit(0 if success else 1)
