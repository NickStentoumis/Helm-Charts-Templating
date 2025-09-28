from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .base import KubernetesResource, ResourceMetadata

@dataclass
class ServicePort:
    name: str
    port: int
    target_port: int
    protocol: str = 'TCP'

@dataclass
class Service(KubernetesResource):
    """Kubernetes Service resource model"""
    service_type: str = "ClusterIP"  # ClusterIP, NodePort, LoadBalancer
    selector: Dict[str, str] = field(default_factory=dict)
    ports: List[ServicePort] = field(default_factory=list)

    def get_template_params(self) -> Dict[str, Any]:
        """Extract parameters for template generation"""
        return {
            'name': self.metadata.name,
            'labels': self.metadata.labels,
            'type': self.service_type,
            'selector': self.selector,
            'ports': [self._port_to_dict(p) for p in self.ports]
        }
    
    def _port_to_dict(self, port: ServicePort) -> Dict[str, Any]:
        return {
            'name': port.name,
            'port': port.port,
            'target_port': port.target_port,
            'protocol': port.protocol
        }
    
    def get_common_patterns(self) -> Dict[str, Any]:
        """Identify common patterns that can be extracted"""
        return {
            'is_external': self.service_type == 'LoadBalancer',
            'is_internal': self.service_type == 'ClusterIP',
            'single_port': len(self.ports) == 1,
            'multi_port': len(self.ports) > 1
        }