# generators/values_transformer.py
"""
Restructures values.yaml AND injects probe configs

Key transformations:
1. FROM: servicename.server.field → TO: servicename.containers.server.field
2. Inject probe configs extracted from deployment YAML
3. Inject containerPort if not present
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from models.resource import ServiceResources
from utils.probe_extractor import ProbeExtractor


class ValuesTransformer:
    """Transform values.yaml to match new template structure and inject missing configs."""
    
    def __init__(self):
        self.probe_extractor = ProbeExtractor()
    
    def transform_values_file(self, input_file: Path, output_file: Path, services: List[ServiceResources] = None):
        """
        Transform values.yaml to new structure AND inject probe configs.
        
        Old structure:
          adservice:
            server:
              image: ...
              env: ...
            ports: ...
        
        New structure:
          adservice:
            containers:
              server:
                image: ...
                env: ...
                livenessProbe: ...       INJECTED from deployment YAML
                readinessProbe: ...      INJECTED from deployment YAML
                resources: ...
            ports: ...
            serviceAccountName: true
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                values = yaml.safe_load(f)
            
            if not values:
                print("  Warning: values.yaml is empty")
                return
            
            print("\n  Transforming values.yaml structure...")
            
            transformed = self._transform_values(values, services)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(transformed, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            print(f"  Transformed: values.yaml")
            print(f"  Injected probe configs from deployment YAMLs")
            
        except Exception as e:
            print(f"  Error transforming values.yaml: {e}")
            import traceback
            traceback.print_exc()
            # Copy as-is if transformation fails
            import shutil
            shutil.copy2(input_file, output_file)
            print(f"  Copied original values.yaml (transformation failed)")
    
    def _transform_values(self, values: Dict[str, Any], services: List[ServiceResources] = None) -> Dict[str, Any]:
        """Transform values structure AND inject probe configs."""
        transformed = {}
        
        # Keep global values (like kubernetesClusterDomain)
        global_keys = ['kubernetesClusterDomain']
        for key in global_keys:
            if key in values:
                transformed[key] = values[key]
        
        # Create service name to ServiceResources mapping
        service_map = {}
        if services:
            service_map = {s.service_name: s for s in services}
        
        # Transform each service
        for service_name, service_config in values.items():
            if service_name in global_keys:
                continue
            
            if not isinstance(service_config, dict):
                transformed[service_name] = service_config
                continue
            
            new_config = {}
            
            # Find container configurations (server, redis, main, etc.)
            container_configs = {}
            other_configs = {}
            
            for key, value in service_config.items():
                if isinstance(value, dict) and 'image' in value:
                    # This looks like a container config
                    container_configs[key] = value
                else:
                    other_configs[key] = value
            
            # If we found containers, restructure
            if container_configs:
                new_config['containers'] = container_configs
                new_config.update(other_configs)
                
                # Add serviceAccountName flag if serviceAccount exists
                if 'serviceAccount' in other_configs:
                    new_config['serviceAccountName'] = True
                
                # Inject probe configs from deployment YAML
                if service_name in service_map:
                    service_resource = service_map[service_name]
                    if service_resource.has_deployment():
                        print(f"    Injecting probes for {service_name}...")
                        self._inject_probe_configs(
                            new_config['containers'],
                            service_resource.deployment_yaml
                        )
            else:
                # No containers found, keep as-is
                new_config = service_config
            
            transformed[service_name] = new_config
        
        return transformed
    
    def _inject_probe_configs(self, containers: Dict[str, Any], deployment_yaml: str):
        """
        Inject probe configurations into container configs.
        
        Extracts probes from deployment YAML and adds them to containers dict.
        """
        # Extract probe configs from deployment YAML
        try:
            container_probes = self.probe_extractor.extract_all_from_deployment(deployment_yaml)
            
            # Inject into containers
            for container_name, probe_configs in container_probes.items():
                if container_name in containers:
                    container = containers[container_name]
                    
                    # Inject liveness probe
                    if probe_configs.get('livenessProbe'):
                        container['livenessProbe'] = probe_configs['livenessProbe']
                        print(f"      Injected livenessProbe for {container_name}")
                    
                    # Inject readiness probe
                    if probe_configs.get('readinessProbe'):
                        container['readinessProbe'] = probe_configs['readinessProbe']
                        print(f"      Injected readinessProbe for {container_name}")
                    
                    # Inject startup probe
                    if probe_configs.get('startupProbe'):
                        container['startupProbe'] = probe_configs['startupProbe']
                        print(f"      Injected startupProbe for {container_name}")
                else:
                    print(f"      Container '{container_name}' not found in values.yaml")
        
        except Exception as e:
            print(f"      Failed to inject probes: {e}")

