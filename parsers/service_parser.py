# parsers/service_parser.py
from typing import Dict, Any, List, Optional
from .base_parser import BaseParser
from models import Service, ServicePort, ResourceMetadata

class ServiceParser(BaseParser):
    """Parser for Kubernetes Service resources"""
    
    def parse(self, yam_content: str) -> List[Service]:
        """Parse YAML content and return Service objects"""
        services = []
        documents = self.split_documents(yam_content)
        
        for doc in documents:
            if self.can_parse(doc):
                service = self._parse_service(doc)
                if service:
                    services.append(service)
        
        return services
    
    def can_parse(self, yaml_dict: Dict[str, Any]) -> bool:
        """Check if this parser can handle the given resource"""
        return yaml_dict.get('kind') == 'Service'
    
    def _parse_service(self, doc: Dict[str, Any]) -> Optional[Service]:
        """Parse a single service document"""
        try:
            metadata = self._parse_metadata(doc.get('metadata', {}))
            spec = doc.get('spec', {})
            
            service = Service(
                api_version=doc.get('apiVersion', 'v1'),
                kind='Service',
                metadata=metadata,
                original_yaml=doc,
                service_type=spec.get('type', 'ClusterIP'),
                selector=spec.get('selector', {}),
                ports=self._parse_ports(spec.get('ports', []))
            )
            
            return service
        except Exception as e:
            print(f"Error parsing service: {e}")
            return None
        
    def _parse_metadata(self, metadata: Dict[str, Any]) -> ResourceMetadata:
        """Parse resource metadata"""
        return ResourceMetadata(
            name=metadata.get('name', ''),
            labels=metadata.get('labels', {}),
            annotations=metadata.get('annotations', {})
        )
    
    def _parse_ports(self, ports: Any) -> List[ServicePort]:
        """Parse service ports"""
        parsed_ports = []
        
        # Handle the case where ports might be a string (Helm template)
        if isinstance(ports, str):
            return parsed_ports
        
        if isinstance(ports, list):
            for port in ports:
                if isinstance(port, dict):
                    service_port = ServicePort(
                        name=port.get('name', ''),
                        port=port.get('port', 0),
                        target_port=port.get('targetPort', port.get('port', 0)),
                        protocol=port.get('protocol', 'TCP')
                    )
                    parsed_ports.append(service_port)
        
        return parsed_ports