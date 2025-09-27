# models/deployment.py
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .base import KubernetesResource, ResourceMetadata


@dataclass
class Container:
    name: str
    image: str
    ports: List[Dict[str, Any]] = field(default_factory=list)
    env: List[Dict[str, Any]] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    security_context: Dict[str, Any] = field(default_factory=dict)
    liveness_probe: Optional[Dict[str, Any]] = None
    readiness_probe: Optional[Dict[str, Any]] = None
    volume_mounts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Deployment(KubernetesResource):
    """Kubernetes Deployment resource model"""
    replicas: int = 1
    selector: Dict[str, Any] = field(default_factory=dict)
    pod_security_context: Dict[str, Any] = field(default_factory=dict)
    service_account_name: Optional[str] = None
    containers: List[Container] = field(default_factory=list)
    init_containers: List[Container] = field(default_factory=list)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    termination_grace_period: Optional[int] = None
    
    def get_template_params(self) -> Dict[str, Any]:
        """Extract parameters for template generation"""
        return {
            'name': self.metadata.name,
            'labels': self.metadata.labels,
            'replicas': self.replicas,
            'selector': self.selector,
            'containers': [self._container_to_dict(c) for c in self.containers],
            'init_containers': [self._container_to_dict(c) for c in self.init_containers],
            'volumes': self.volumes,
            'service_account_name': self.service_account_name,
            'pod_security_context': self.pod_security_context,
            'termination_grace_period': self.termination_grace_period
        }
    
    def _container_to_dict(self, container: Container) -> Dict[str, Any]:
        return {
            'name': container.name,
            'image': container.image,
            'ports': container.ports,
            'env': container.env,
            'resources': container.resources,
            'security_context': container.security_context,
            'liveness_probe': container.liveness_probe,
            'readiness_probe': container.readiness_probe,
            'volume_mounts': container.volume_mounts
        }
    
    def get_common_patterns(self) -> Dict[str, Any]:
        """Identify common patterns that can be extracted"""
        patterns = {
            'has_probes': any(c.liveness_probe or c.readiness_probe for c in self.containers),
            'has_volumes': bool(self.volumes),
            'has_init_containers': bool(self.init_containers),
            'security_context_type': self._classify_security_context()
        }
        return patterns
    
    def _classify_security_context(self) -> str:
        """Classify the type of security context"""
        if self.pod_security_context:
            if self.pod_security_context.get('runAsNonRoot'):
                return 'non-root'
        return 'standard'