# models/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ResourceMetadata:
    """Metadata for Kubernetes resources"""
    name: str
    labels: Dict[str, Any] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KubernetesResource(ABC):
    """Base class for all Kubernetes resources"""
    api_version: str
    kind: str
    metadata: ResourceMetadata
    original_yaml: Dict[str, Any] = field(default_factory=dict)
    
    @abstractmethod
    def get_template_params(self) -> Dict[str, Any]:
        """Extract parameters for template generation"""
        pass
    
    @abstractmethod
    def get_common_patterns(self) -> Dict[str, Any]:
        """Identify common patterns that can be extracted"""
        pass
