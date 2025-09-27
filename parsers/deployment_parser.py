# parsers/deployment_parser.py
from typing import Dict, Any, List, Optional
from .base_parser import BaseParser
from models import Deployment, Container, ResourceMetadata


class DeploymentParser(BaseParser):
    """Parser for Kubernetes Deployment resources"""
    
    def parse(self, yaml_content: str) -> List[Deployment]:
        """Parse YAML content and return Deployment objects"""
        deployments = []
        documents = self.split_documents(yaml_content)
        
        for doc in documents:
            if self.can_parse(doc):
                deployment = self._parse_deployment(doc)
                if deployment:
                    deployments.append(deployment)
        
        return deployments
    
    def can_parse(self, yaml_dict: Dict[str, Any]) -> bool:
        """Check if this parser can handle the given resource"""
        return yaml_dict.get('kind') == 'Deployment'
    
    def _parse_deployment(self, doc: Dict[str, Any]) -> Optional[Deployment]:
        """Parse a single deployment document"""
        try:
            metadata = self._parse_metadata(doc.get('metadata', {}))
            spec = doc.get('spec', {})
            template = spec.get('template', {})
            template_spec = template.get('spec', {})
            
            deployment = Deployment(
                api_version=doc.get('apiVersion', 'apps/v1'),
                kind='Deployment',
                metadata=metadata,
                original_yaml=doc,
                replicas=spec.get('replicas', 1),
                selector=spec.get('selector', {}),
                pod_security_context=template_spec.get('securityContext', {}),
                service_account_name=template_spec.get('serviceAccountName'),
                containers=self._parse_containers(template_spec.get('containers', [])),
                init_containers=self._parse_containers(template_spec.get('initContainers', [])),
                volumes=template_spec.get('volumes', []),
                termination_grace_period=template_spec.get('terminationGracePeriodSeconds')
            )
            
            return deployment
        except Exception as e:
            print(f"Error parsing deployment: {e}")
            return None
    
    def _parse_metadata(self, metadata: Dict[str, Any]) -> ResourceMetadata:
        """Parse resource metadata"""
        return ResourceMetadata(
            name=metadata.get('name', ''),
            labels=metadata.get('labels', {}),
            annotations=metadata.get('annotations', {})
        )
    
    def _parse_containers(self, containers: List[Dict[str, Any]]) -> List[Container]:
        """Parse container specifications"""
        parsed_containers = []
        for cont in containers:
            container = Container(
                name=cont.get('name', ''),
                image=cont.get('image', ''),
                ports=cont.get('ports', []),
                env=cont.get('env', []),
                resources=cont.get('resources', {}),
                security_context=cont.get('securityContext', {}),
                liveness_probe=cont.get('livenessProbe'),
                readiness_probe=cont.get('readinessProbe'),
                volume_mounts=cont.get('volumeMounts', [])
            )
            parsed_containers.append(container)
        return parsed_containers
