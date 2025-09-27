# parsers/base_parser.py
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
        
        return self.parse(content)
    
    def _fix_yaml_formatting(self, content: str) -> str:
        """Fix common YAML formatting issues"""
        # Replace tabs with spaces
        content = content.replace('\t', '  ')
        return content
    
    def split_documents(self, yaml_content: str) -> List[Dict[str, Any]]:
        """Split multi-document YAML into separate documents"""
        documents = []
        for doc in yaml.safe_load_all(yaml_content):
            if doc:
                documents.append(doc)
        return documents
    
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