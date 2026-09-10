# backend/tools/dpk/__init__.py
"""DPK (Development and Project Kit) Toolkit

DPK is a project automation and development toolkit for POLICYGUARD.
It provides utilities for:
- Configuration management
- Environment setup and validation
- Deployment automation
- Infrastructure management

NOTE: DPK is separate from Nova (AI/ML runtime).
- Nova handles AI model orchestration and inference
- DPK handles project automation and tooling
"""

from .config_manager import ConfigManager
from .env_setup import EnvironmentSetup
from .deployment import DeploymentAutomation

__version__ = "1.0.0"
__all__ = [
    "ConfigManager",
    "EnvironmentSetup",
    "DeploymentAutomation",
]
