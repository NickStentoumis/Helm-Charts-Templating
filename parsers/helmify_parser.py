# parsers/helmify_parser.py
"""
Preserves everything from helmify output
Simply splits by resource type, no modification
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple
import yaml

from models.resource import ServiceResources, ChartInfo


class HelmifyParser:
    """Parse helmify output preserving all original content."""
    
    def __init__(self):
        self.chart_info = ChartInfo()
    
    def parse_directory(self, input_dir: Path) -> Tuple[List[ServiceResources], ChartInfo]:
        """Parse all YAML files in directory."""
        
        # Read Chart.yaml to get chart name
        chart_file = input_dir / "Chart.yaml"
        if chart_file.exists():
            self.chart_info = self._parse_chart_yaml(chart_file)
        
        # Find all YAML files (excluding Chart.yaml, values.yaml, _helpers.tpl)
        yaml_files = []
        for pattern in ['*.yaml', '*.yml']:
            yaml_files.extend(input_dir.glob(pattern))
        
        # Exclude metadata files
        yaml_files = [
            f for f in yaml_files 
            if f.name not in ['Chart.yaml', 'values.yaml', '_helpers.tpl']
        ]
        
        # Group resources by service
        services_dict: Dict[str, ServiceResources] = {}
        
        for yaml_file in yaml_files:
            print(f"  Reading: {yaml_file.name}")
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into documents
            documents = self._split_documents(content)
            
            for doc_text in documents:
                if not doc_text.strip():
                    continue
                
                # Determine resource type and service name
                kind = self._get_kind(doc_text)
                service_name = self._get_service_name(doc_text)
                
                if not service_name:
                    print(f"    Warning: Could not determine service name for {kind}")
                    continue
                
                # Initialize service resources if needed
                if service_name not in services_dict:
                    services_dict[service_name] = ServiceResources(service_name=service_name)
                
                # Store complete original YAML by type
                if kind == 'Deployment':
                    services_dict[service_name].deployment_yaml = doc_text
                elif kind == 'Service':
                    if not services_dict[service_name].service_yaml:
                        services_dict[service_name].service_yaml = doc_text
                    else:
                        # Additional service (e.g., frontend-external)
                        # Create separate service resource
                        ext_service_name = self._get_service_name(doc_text, use_metadata_name=True)
                        if ext_service_name and ext_service_name != service_name:
                            if ext_service_name not in services_dict:
                                services_dict[ext_service_name] = ServiceResources(service_name=ext_service_name)
                            services_dict[ext_service_name].service_yaml = doc_text
                        else:
                            services_dict[service_name].other_resources.append(doc_text)
                elif kind == 'ServiceAccount':
                    services_dict[service_name].service_account_yaml = doc_text
                else:
                    # Other resources (ConfigMap, Secret, etc.)
                    services_dict[service_name].other_resources.append(doc_text)
                
                print(f"    Found: {kind} for {service_name}")
        
        return list(services_dict.values()), self.chart_info
    
    def _parse_chart_yaml(self, chart_file: Path) -> ChartInfo:
        """Parse Chart.yaml to get chart metadata."""
        try:
            with open(chart_file, 'r') as f:
                chart_data = yaml.safe_load(f)
            
            return ChartInfo(
                chart_name=chart_data.get('name', 'helm'),
                chart_version=chart_data.get('version', '0.1.0'),
                app_version=chart_data.get('appVersion', '0.1.0')
            )
        except Exception as e:
            print(f"  Warning: Could not parse Chart.yaml: {e}")
            return ChartInfo()
    
    def _split_documents(self, content: str) -> List[str]:
        """Split YAML into multiple documents."""
        # Fix tabs
        content = content.replace('\t', '  ')
        
        documents = []
        current = []
        
        for line in content.split('\n'):
            if line.strip() == '---':
                if current:
                    documents.append('\n'.join(current))
                    current = []
            else:
                current.append(line)
        
        if current:
            documents.append('\n'.join(current))
        
        return documents
    
    def _get_kind(self, yaml_text: str) -> str:
        """Extract resource kind."""
        match = re.search(r'^kind:\s*(\w+)', yaml_text, re.MULTILINE)
        return match.group(1) if match else 'Unknown'
    
    def _get_service_name(self, yaml_text: str, use_metadata_name: bool = False) -> str:
        """
        Extract service name from YAML.
        
        Priority:
        1. From app label (most reliable)
        2. From metadata name (strip chart name prefix)
        """
        # Try app label first
        app_match = re.search(r'app:\s*(\S+)', yaml_text)
        if app_match and not use_metadata_name:
            return app_match.group(1)
        
        # Try metadata name
        # Pattern: {{ include "helm.fullname" . }}-servicename
        name_pattern = r'name:\s*\{\{\s*include\s+"[^"]+"\s+\.\s*\}\}-(\S+)'
        match = re.search(name_pattern, yaml_text)
        if match:
            return match.group(1)
        
        # Pattern: name: servicename (plain)
        name_match = re.search(r'metadata:\s*\n\s*name:\s*(\S+)', yaml_text, re.DOTALL)
        if name_match:
            name = name_match.group(1)
            # If it's a template, try to extract from labels
            if '{{' in name:
                if app_match:
                    return app_match.group(1)
            return name
        
        return None
