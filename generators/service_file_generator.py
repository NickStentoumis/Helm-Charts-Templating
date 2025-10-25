# generators/service_file_generator.py
"""
Service File Generator: Creates refactored service files
"""

from pathlib import Path
from models.resource import ServiceResources


class ServiceFileGenerator:
    """Generate refactored service files using template includes."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, service: ServiceResources):
        """Generate refactored YAML file for one service."""
        parts = []
        
        # Deployment (if exists)
        if service.has_deployment():
            parts.append(
                '{{- include "microservice.deployment.helmify" '
                f'(dict "Values" .Values.{service.service_name} "root" . "serviceName" "{service.service_name}") }}}}'
            )
        
        # Service (if exists)
        if service.has_service():
            if parts:
                parts.append('---')
            parts.append(
                '{{- include "microservice.service.helmify" '
                f'(dict "Values" .Values.{service.service_name} "root" . "serviceName" "{service.service_name}") }}}}'
            )
        
        # ServiceAccount (if exists) - preserved as-is
        if service.has_service_account():
            if parts:
                parts.append('---')
            parts.append(service.service_account_yaml.strip())
        
        # Other resources (ConfigMaps, Secrets, etc.) - preserved as-is
        for resource_yaml in service.other_resources:
            if parts:
                parts.append('---')
            parts.append(resource_yaml.strip())
        
        # Write file
        if parts:
            content = '\n'.join(parts) + '\n'
            output_file = self.output_dir / f"{service.service_name}.yaml"
            output_file.write_text(content, encoding='utf-8')
            
            # Calculate stats
            original_lines = 0
            if service.deployment_yaml:
                original_lines += len(service.deployment_yaml.split('\n'))
            if service.service_yaml:
                original_lines += len(service.service_yaml.split('\n'))
            new_lines = len(content.split('\n'))
            
            if original_lines > 0:
                reduction = ((original_lines - new_lines) / original_lines) * 100
                print(f"  Generated: {service.service_name}.yaml ({original_lines} -> {new_lines} lines, {reduction:.0f}% reduction)")
            else:
                print(f"  Generated: {service.service_name}.yaml")
