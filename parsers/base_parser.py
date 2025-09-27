# parsers/base_parser.py - FIXED VERSION
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import yaml
import re
from pathlib import Path


class BaseParser(ABC):
    """Abstract base parser for Kubernetes resources"""
    
    def __init__(self):
        self.resources = []
    
    @abstractmethod
    def parse(self, yaml_content: str) -> List[Any]:
        """Parse YAML content and return resource objects"""
        pass
    
    @abstractmethod
    def can_parse(self, yaml_dict: Dict[str, Any]) -> bool:
        """Check if this parser can handle the given resource"""
        pass
    
    def parse_file(self, file_path: Path) -> List[Any]:
        """Parse a YAML file"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Fix common formatting issues (like tabs in ports section)
        content = self._fix_yaml_formatting(content)

        print("Fixed Content:::\n", content)
        
        return self.parse(content)
    
    def _fix_yaml_formatting(self, content: str) -> str:
        """Fix common YAML formatting issues"""
        # Replace tabs with spaces
        content = content.replace('\t', '  ')
        return content
    
    def split_documents(self, yaml_content: str) -> List[Dict[str, Any]]:
        """Split multi-document YAML into separate documents"""
        documents = []
        
        # First, try to handle as Helm template
        if self._is_helm_template(yaml_content):
            documents = self._parse_helm_template(yaml_content)
        else:
            # Regular YAML parsing
            try:
                for doc in yaml.safe_load_all(yaml_content):
                    if doc:
                        documents.append(doc)
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse as pure YAML, attempting template extraction: {e}")
                documents = self._parse_helm_template(yaml_content)
        
        return documents
    
    def _is_helm_template(self, content: str) -> bool:
        """Check if content contains Helm template syntax"""
        helm_patterns = [r'\{\{', r'\}\}', r'include\s+"', r'\.Values\.']
        return any(re.search(pattern, content) for pattern in helm_patterns)
    
    def _parse_helm_template(self, content: str) -> List[Dict[str, Any]]:
        """Parse Helm template by extracting structure"""
        documents = []
        
        # Split by document separator
        doc_parts = content.split('\n---\n')
        
        for part in doc_parts:
            if not part.strip():
                continue
            
            # Extract basic structure from template
            doc_structure = self._extract_template_structure(part)
            if doc_structure:
                documents.append(doc_structure)
        
        return documents
    
    def _extract_template_structure(self, template: str) -> Optional[Dict[str, Any]]:
        """Extract basic structure from a Helm template"""
        structure = {}
        

        # Extract apiVersion
        api_match = re.search(r'apiVersion:\s*([^\n]+)', template)
        if api_match:
            structure['apiVersion'] = api_match.group(1).strip()
        
        # Extract kind
        kind_match = re.search(r'kind:\s*([^\n]+)', template)
        if kind_match:
            structure['kind'] = kind_match.group(1).strip()
        
        # Extract metadata
        metadata = {}
        
        # Extract name (handling Helm templates)
        name_patterns = [
            r'name:\s*\{\{\s*include\s+"[^"]+"\s+\.\s*\}\}-([^\n\s]+)',  # {{ include "..." . }}-servicename
            r'name:\s*\{\{[^}]+\}\}-([^\n\s]+)',  # {{ ... }}-servicename
            r'name:\s*([^\{\n]+)',  # plain name
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, template)
            if name_match:
                service_name = name_match.group(1).strip()
                metadata['name'] = service_name
                break
        
        # If no name found, try to extract from labels
        label_match = re.search(r'app:\s*([^\n\{\s]+)', template)
        if label_match and 'name' not in metadata:
            metadata['name'] = label_match.group(1).strip()
        
        if metadata:
            structure['metadata'] = metadata
        
        # Extract spec section
        spec_match = re.search(r'spec:(.*?)(?=\n[a-zA-Z]|\Z)', template, re.DOTALL)
        if spec_match:
            spec_content = spec_match.group(1)
            spec = self._extract_spec_basics(spec_content, structure.get('kind'))
            if spec:
                structure['spec'] = spec
        
        return structure if structure.get('kind') else None
    
    def _extract_spec_basics(self, spec_content: str, kind: str) -> Dict[str, Any]:
        """Extract basic spec information based on resource kind"""
        spec = {}
        
        if kind == 'Deployment':
            # Extract replicas
            replicas_match = re.search(r'replicas:\s*(\d+)', spec_content)
            if replicas_match:
                spec['replicas'] = int(replicas_match.group(1))
            else:
                spec['replicas'] = 1  # Default
            
            # Extract selector
            selector_match = re.search(r'selector:.*?app:\s*([^\n\s]+)', spec_content, re.DOTALL)
            if selector_match:
                spec['selector'] = {'matchLabels': {'app': selector_match.group(1).strip()}}
            
            # Extract template.spec
            template_spec = {}
            
            # Look for containers
            containers_match = re.search(r'containers:(.*?)(?=\n\s{0,4}[a-zA-Z]|\Z)', spec_content, re.DOTALL)
            if containers_match:
                containers = self._extract_containers(containers_match.group(1))
                template_spec['containers'] = containers
            
            # Look for serviceAccountName
            sa_patterns = [
                r'serviceAccountName:\s*\{\{[^}]+\}\}-([^\n\s]+)',
                r'serviceAccountName:\s*([^\{\n]+)',
            ]
            for pattern in sa_patterns:
                sa_match = re.search(pattern, spec_content)
                if sa_match:
                    template_spec['serviceAccountName'] = sa_match.group(1).strip()
                    break
            
            # Look for securityContext
            if 'securityContext:' in spec_content:
                template_spec['securityContext'] = {'runAsNonRoot': True}  # Simplified
            
            spec['template'] = {'spec': template_spec}
            
        elif kind == 'Service':
            # Extract type
            type_match = re.search(r'type:\s*([^\n\{\s]+)', spec_content)
            if type_match:
                spec['type'] = type_match.group(1).strip()
            
            # Extract selector
            selector_match = re.search(r'selector:.*?app:\s*([^\n\s]+)', spec_content, re.DOTALL)
            if selector_match:
                spec['selector'] = {'app': selector_match.group(1).strip()}
            
            # Extract ports (simplified)
            spec['ports'] = []  # Would need more complex parsing
        
        return spec
    
    def _extract_containers(self, containers_content: str) -> List[Dict[str, Any]]:
        """Extract container information"""
        containers = []
        
        # Simple extraction - look for container names and images
        container_blocks = re.split(r'\n\s*-\s*(?=name:|env:)', containers_content)
        
        for block in container_blocks:
            if not block.strip():
                continue
            
            container = {}
            
            # Extract name
            name_match = re.search(r'name:\s*([^\n]+)', block)
            if name_match:
                container['name'] = name_match.group(1).strip()
            
            # Extract image (handling Helm templates)
            image_patterns = [
                r'image:\s*\{\{[^}]+\}\}:?\{\{[^}]+\}\}',  # Full template
                r'image:\s*([^\{\n]+)',  # Plain image
            ]
            
            for pattern in image_patterns:
                image_match = re.search(pattern, block)
                if image_match:
                    if '{{' in image_match.group(0):
                        container['image'] = 'helm-template'
                    else:
                        container['image'] = image_match.group(1).strip()
                    break
            
            # Extract ports
            port_match = re.search(r'containerPort:\s*(\d+)', block)
            if port_match:
                container['ports'] = [{'containerPort': int(port_match.group(1))}]
            
            if container.get('name'):
                containers.append(container)
        
        return containers if containers else [{'name': 'server', 'image': 'helm-template'}]
    
    def extract_helm_values(self, value: Any) -> Dict[str, Any]:
        """Extract Helm template variables from values"""
        helm_vars = {}
        if isinstance(value, str):
            # Find patterns like {{ .Values.something }}
            pattern = r'\{\{\s*\.Values\.([^\s}]+)\s*\}\}'
            matches = re.findall(pattern, value)
            for match in matches:
                helm_vars[match] = value
        elif isinstance(value, dict):
            for k, v in value.items():
                sub_vars = self.extract_helm_values(v)
                helm_vars.update(sub_vars)
        elif isinstance(value, list):
            for item in value:
                sub_vars = self.extract_helm_values(item)
                helm_vars.update(sub_vars)
        return helm_vars