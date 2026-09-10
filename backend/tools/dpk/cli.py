"""Command-line interface for DPK toolkit.

Provides CLI commands for managing POLICYGUARD deployment,
configuration, and operations.
"""

import click
import json
import sys
from typing import Optional
from pathlib import Path
from .config_manager import ConfigManager
from .env_setup import EnvironmentValidator
from .deployment import DeploymentManager


@click.group()
@click.version_option(version='1.0.0')
def dpk():
    """DPK Toolkit - Development and deployment tools for POLICYGUARD."""
    pass


@dpk.group()
def config():
    """Manage configuration settings."""
    pass


@config.command('init')
@click.option('--environment', '-e', default='development',
              help='Environment to initialize (development, staging, production)')
@click.option('--config-file', '-c', type=click.Path(),
              help='Path to configuration file')
def config_init(environment: str, config_file: Optional[str]):
    """Initialize configuration for an environment."""
    click.echo(f"Initializing configuration for {environment}...")
    
    try:
        config_manager = ConfigManager(config_file)
        
        # Create default configuration if not exists
        if not config_manager.get(f"environments.{environment}"):
            default_config = {
                "name": environment,
                "region": "us-east-1",
                "lambda": {
                    "functions": [],
                    "runtime": "python3.9"
                },
                "api_gateway": {
                    "name": f"policyguard-api-{environment}"
                },
                "database": {
                    "type": "RDS",
                    "engine": "postgres"
                },
                "monitoring": {
                    "enabled": True,
                    "alarms": []
                }
            }
            config_manager.set(f"environments.{environment}", default_config)
            click.echo(f"✓ Created default configuration for {environment}")
        else:
            click.echo(f"Configuration for {environment} already exists")
            
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@config.command('get')
@click.argument('key')
@click.option('--config-file', '-c', type=click.Path(),
              help='Path to configuration file')
def config_get(key: str, config_file: Optional[str]):
    """Get a configuration value."""
    try:
        config_manager = ConfigManager(config_file)
        value = config_manager.get(key)
        
        if value is not None:
            click.echo(json.dumps(value, indent=2))
        else:
            click.echo(f"Key '{key}' not found", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.option('--config-file', '-c', type=click.Path(),
              help='Path to configuration file')
def config_set(key: str, value: str, config_file: Optional[str]):
    """Set a configuration value."""
    try:
        config_manager = ConfigManager(config_file)
        
        # Try to parse value as JSON
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value
        
        config_manager.set(key, parsed_value)
        click.echo(f"✓ Set {key} = {parsed_value}")
        
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@dpk.group()
def env():
    """Manage environment setup and validation."""
    pass


@env.command('validate')
@click.option('--config-file', '-c', type=click.Path(),
              help='Path to configuration file')
@click.option('--fix', is_flag=True,
              help='Attempt to fix validation issues')
def env_validate(config_file: Optional[str], fix: bool):
    """Validate environment setup."""
    click.echo("Validating environment...")
    
    try:
        config_manager = ConfigManager(config_file)
        validator = EnvironmentValidator(config_manager)
        
        result = validator.validate_all()
        
        # Display results
        all_passed = True
        for check_name, check_result in result.items():
            status = "✓" if check_result.get("valid") else "✗"
            click.echo(f"{status} {check_name}: {check_result.get('message', 'OK')}")
            if not check_result.get("valid"):
                all_passed = False
        
        if all_passed:
            click.echo("\n✓ All validation checks passed")
        else:
            click.echo("\n✗ Some validation checks failed", err=True)
            if fix:
                click.echo("\nAttempting to fix issues...")
                validator.setup_environment()
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@env.command('setup')
@click.option('--config-file', '-c', type=click.Path(),
              help='Path to configuration file')
def env_setup(config_file: Optional[str]):
    """Set up development environment."""
    click.echo("Setting up development environment...")
    
    try:
        config_manager = ConfigManager(config_file)
        validator = EnvironmentValidator(config_manager)
        
        result = validator.setup_environment()
        
        if result.get("status") == "success":
            click.echo("✓ Environment setup completed successfully")
        else:
            click.echo(f"✗ Setup failed: {result.get('error')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@dpk.group()
def deploy():
    """Manage deployments."""
    pass


@deploy.command('infrastructure')
@click.option('--environment', '-e', default='development',
              help='Target environment')
@click.option('--config-file', '-c', type=click.Path(),
              help='Path to configuration file')
def deploy_infrastructure(environment: str, config_file: Optional[str]):
    """Deploy infrastructure to specified environment."""
    click.echo(f"Deploying infrastructure to {environment}...")
    
    try:
        config_manager = ConfigManager(config_file)
        deployment_manager = DeploymentManager(config_manager)
        
        with click.progressbar(length=100, label='Deploying') as bar:
            result = deployment_manager.deploy_infrastructure(environment)
            bar.update(100)
        
        if result.get("status") == "success":
            click.echo("\n✓ Deployment completed successfully")
            click.echo(f"\nDeployed components:")
            for component, details in result.get("components", {}).items():
                click.echo(f"  • {component}: {details.get('status')}")
        else:
            click.echo(f"\n✗ Deployment failed: {result.get('error')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"\n✗ Error: {str(e)}", err=True)
        sys.exit(1)


@deploy.command('verify')
@click.option('--environment', '-e', default='development',
              help='Environment to verify')
@click.option('--config-file', '-c', type=click.Path(),
              help='Path to configuration file')
def deploy_verify(environment: str, config_file: Optional[str]):
    """Verify deployment health."""
    click.echo(f"Verifying deployment for {environment}...")
    
    try:
        config_manager = ConfigManager(config_file)
        deployment_manager = DeploymentManager(config_manager)
        
        result = deployment_manager.verify_deployment(environment)
        
        # Display health checks
        for check_name, check_result in result.get("checks", {}).items():
            status = "✓" if check_result.get("status") == "healthy" else "✗"
            click.echo(f"{status} {check_name}: {check_result.get('status')}")
        
        overall_status = result.get("status")
        if overall_status == "healthy":
            click.echo("\n✓ Deployment is healthy")
        else:
            click.echo("\n✗ Deployment has issues", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@deploy.command('rollback')
@click.argument('deployment-id')
@click.option('--config-file', '-c', type=click.Path(),
              help='Path to configuration file')
@click.confirmation_option(prompt='Are you sure you want to rollback?')
def deploy_rollback(deployment_id: str, config_file: Optional[str]):
    """Rollback a deployment."""
    click.echo(f"Rolling back deployment {deployment_id}...")
    
    try:
        config_manager = ConfigManager(config_file)
        deployment_manager = DeploymentManager(config_manager)
        
        result = deployment_manager.rollback_deployment(deployment_id)
        
        if result.get("status") == "success":
            click.echo("✓ Rollback completed successfully")
        else:
            click.echo(f"✗ Rollback failed: {result.get('error')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@dpk.command('info')
def info():
    """Display DPK toolkit information."""
    click.echo("""
DPK Toolkit v1.0.0
==================

Development and deployment automation tools for POLICYGUARD.

Commands:
  config      - Manage configuration settings
  env         - Manage environment setup
  deploy      - Manage deployments
  info        - Display this information

For more information on a command, run:
  dpk <command> --help

Documentation: See backend/tools/dpk/ARCHITECTURE.md
    """)


if __name__ == '__main__':
    dpk()
