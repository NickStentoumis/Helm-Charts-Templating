# models/resource.py
"""
Store complete original YAML per service
No parsing, No extraction just preserve everything as is
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ServiceResources:
    """All resources for one service  stored as original YAML text."""
    
    service_name: str
    
    # Original YAML text from helmify (complete, unmodified)
    deployment_yaml: str = ""
    service_yaml: str = ""
    service_account_yaml: str = ""
    
    # Additional resources (ConfigMaps, Secrets, etc.)
    other_resources: List[str] = field(default_factory=list)
    
    def has_deployment(self) -> bool:
        return bool(self.deployment_yaml.strip())
    
    def has_service(self) -> bool:
        return bool(self.service_yaml.strip())
    
    def has_service_account(self) -> bool:
        return bool(self.service_account_yaml.strip())


@dataclass
class ChartInfo:
    """Information about the Helm chart."""
    
    chart_name: str = "helm"
    chart_version: str = "0.1.0"
    app_version: str = "0.1.0"
    
    # Detected patterns
    uses_fullname_helper: bool = True
    uses_labels_helper: bool = True
    uses_selector_labels_helper: bool = True
