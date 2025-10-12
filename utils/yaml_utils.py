# utils/yaml_utils.py
import yaml
import re
from typing import Dict, Any, List
from pathlib import Path


class YamlUtils:
    """Utility functions for YAML processing"""
    
    @staticmethod
    def fix_yaml_formatting(content: str) -> str:
        """Fix common YAML formatting issues"""
        # Replace tabs with spaces
        content = content.replace('\t', '  ')
        
        # Fix ports indentation issue
        lines = content.split('\n')
        fixed_lines = []
        for i, line in enumerate(lines):
            if 'ports:' in line and '\t{{' in line:
                # Fix the indentation issue with ports
                line = line.replace('\t{{', '  {{')
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    @staticmethod
    def load_yaml_file(file_path: Path) -> List[Dict[str, Any]]:
        """Load YAML file and return list of documents"""
        with open(file_path, 'r') as f:
            content = f.read()
        
        content = YamlUtils.fix_yaml_formatting(content)
        documents = []
        
        for doc in yaml.safe_load_all(content):
            if doc:
                documents.append(doc)
        
        return documents
    
    @staticmethod
    def extract_service_name(file_name: str) -> str:
        """Extract service name from file name"""
        # Remove .yaml extension
        name = file_name.replace('.yaml', '')
        # Remove common suffixes
        name = name.replace('service', '').replace('-', '')
        return name if name else file_name.replace('.yaml', '')
    
    @staticmethod
    def is_helm_template(content: str) -> bool:
        """Check if content contains Helm template directives"""
        helm_patterns = [
            r'\{\{',  # Opening Helm template
            r'\.Values\.',  # Values reference
            r'include\s+"',  # Include statement
        ]
        
        for pattern in helm_patterns:
            if re.search(pattern, content):
                return True
        return False
    
    @staticmethod
    def extract_helm_variables(content: str) -> List[str]:
        """Extract Helm variable references from content"""
        pattern = r'\{\{\s*\.Values\.([^\s}]+)\s*\}\}'
        matches = re.findall(pattern, content)
        return list(set(matches))