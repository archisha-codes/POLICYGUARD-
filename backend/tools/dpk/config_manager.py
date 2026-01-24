# backend/tools/dpk/config_manager.py
"""Configuration Management Module for DPK

Handles project configuration, settings management, and config validation.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages POLICYGUARD configuration files and environment-specific settings."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize ConfigManager.
        
        Args:
            config_dir: Path to config directory (defaults to project root/config/)
        """
        self.config_dir = Path(config_dir) if config_dir else self._find_config_dir()
        self._config_cache = {}
    
    def _find_config_dir(self) -> Path:
        """Find the project config directory."""
        current = Path.cwd()
        while current != current.parent:
            config_path = current / "config"
            if config_path.exists():
                return config_path
            current = current.parent
        # Default to creating in current directory
        return Path.cwd() / "config"
    
    def load_config(self, config_name: str, env: str = "development") -> Dict[str, Any]:
        """Load configuration file.
        
        Args:
            config_name: Name of config file (without extension)
            env: Environment (development, staging, production)
        
        Returns:
            Configuration dictionary
        """
        cache_key = f"{config_name}:{env}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        # Try loading environment-specific config first
        env_config_path = self.config_dir / f"{config_name}.{env}.yaml"
        if env_config_path.exists():
            config = self._load_yaml(env_config_path)
        else:
            # Fall back to default config
            default_path = self.config_dir / f"{config_name}.yaml"
            if default_path.exists():
                config = self._load_yaml(default_path)
            else:
                config = {}
        
        self._config_cache[cache_key] = config
        return config
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file."""
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def save_config(self, config_name: str, data: Dict[str, Any], env: str = "development"):
        """Save configuration to file.
        
        Args:
            config_name: Name of config file
            data: Configuration data
            env: Environment name
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_path = self.config_dir / f"{config_name}.{env}.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        
        # Invalidate cache
        cache_key = f"{config_name}:{env}"
        self._config_cache.pop(cache_key, None)
    
    def get_aws_config(self, env: str = "development") -> Dict[str, Any]:
        """Get AWS-specific configuration.
        
        Returns:
            AWS configuration including regions, service endpoints, etc.
        """
        return self.load_config("aws", env)
    
    def get_database_config(self, env: str = "development") -> Dict[str, Any]:
        """Get database configuration.
        
        Returns:
            Database connection settings
        """
        return self.load_config("database", env)
    
    def validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate configuration against schema.
        
        Args:
            config: Configuration to validate
            schema: Expected schema
        
        Returns:
            True if valid, raises exception otherwise
        """
        for key, expected_type in schema.items():
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
            if not isinstance(config[key], expected_type):
                raise TypeError(f"Config key '{key}' should be {expected_type.__name__}")
        return True


# Singleton instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get or create global ConfigManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
