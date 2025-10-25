# utils/probe_extractor.py
"""
Extract probe configurations from helmify YAML
Handles YAML that contains Go template syntax
"""

import re
import yaml
from typing import Dict, Any, Optional


class ProbeExtractor:
    """
    Extract probe and port configurations from deployment YAML.
    """
    
    def extract_from_deployment(self, deployment_yaml: str) -> Dict[str, Any]:
        """
        Extract probe configs and ports from deployment YAML.
        
        Returns: {
            'livenessProbe': {...} or None,
            'readinessProbe': {...} or None,
            'startupProbe': {...} or None,
            'containerPort': 9555 or None
        }
        """
        result = {
            'livenessProbe': None,
            'readinessProbe': None,
            'startupProbe': None,
            'containerPort': None,
        }
        
        # Extract liveness probe
        result['livenessProbe'] = self._extract_probe(deployment_yaml, 'livenessProbe')
        
        # Extract readiness probe
        result['readinessProbe'] = self._extract_probe(deployment_yaml, 'readinessProbe')
        
        # Extract startup probe
        result['startupProbe'] = self._extract_probe(deployment_yaml, 'startupProbe')
        
        # Extract containerPort
        result['containerPort'] = self._extract_container_port(deployment_yaml)
        
        return result
    
    def _extract_probe(self, yaml_text: str, probe_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract a probe configuration (liveness/readiness/startup).
        
        Uses line-by-line parsing to handle indentation correctly.
        """
        lines = yaml_text.split('\n')
        
        # Find the probe line
        probe_line_idx = None
        probe_indent = None
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith(f'{probe_name}:'):
                probe_line_idx = i
                probe_indent = len(line) - len(stripped)
                break
        
        if probe_line_idx is None:
            return None
        
        # Extract all lines that belong to this probe (more indented than probe line)
        probe_lines = [lines[probe_line_idx]]
        
        for i in range(probe_line_idx + 1, len(lines)):
            line = lines[i]
            if not line.strip():  # Skip empty lines
                continue
            
            line_indent = len(line) - len(line.lstrip())
            
            # If this line is more indented than probe line, it belongs to the probe
            if line_indent > probe_indent:
                probe_lines.append(line)
            else:
                # Less or equal indent = end of probe block
                break
        
        # Now parse this block as YAML
        probe_yaml_text = '\n'.join(probe_lines)
        
        # Check for Go templates
        if '{{' in probe_yaml_text:
            # Has Go templates - manual extraction
            return self._extract_probe_manual(probe_yaml_text, probe_name)
        
        # No Go templates - try YAML parsing
        try:
            parsed = yaml.safe_load(probe_yaml_text)
            if parsed and probe_name in parsed:
                return parsed[probe_name]
        except yaml.YAMLError as e:
            print(f"      YAML parse error for {probe_name}: {e}")
            return self._extract_probe_manual(probe_yaml_text, probe_name)
        
        return None
    
    def _extract_probe_manual(self, probe_block: str, probe_name: str) -> Optional[Dict[str, Any]]:
        """
        Manually extract probe config when YAML parsing fails.
        
        Extracts common probe fields:
        - httpGet (path, port, scheme, httpHeaders)
        - tcpSocket (port)
        - grpc (port, service)
        - exec (command)
        - initialDelaySeconds, periodSeconds, timeoutSeconds, etc.
        """
        probe_config = {}
        
        lines = probe_block.split('\n')
        current_indent = None
        current_key = None
        
        for line in lines:
            if not line.strip():
                continue
            
            # Calculate indent
            indent = len(line) - len(line.lstrip())
            
            # Skip the probe name line itself
            if probe_name in line:
                current_indent = indent
                continue
            
            # Parse key-value pairs
            if ':' in line:
                key, _, value = line.partition(':')
                key = key.strip()
                value = value.strip()
                
                # Detect probe type
                if key in ['httpGet', 'tcpSocket', 'grpc', 'exec']:
                    probe_config['type'] = key
                    probe_config[key] = {}
                    current_key = key
                elif key in ['initialDelaySeconds', 'periodSeconds', 'timeoutSeconds', 
                            'successThreshold', 'failureThreshold']:
                    try:
                        probe_config[key] = int(value) if value and value.isdigit() else value
                    except:
                        probe_config[key] = value
                elif current_key and indent > current_indent:
                    # Sub-field of probe type (e.g., httpGet.port)
                    if value:
                        try:
                            # Try to convert to int if it looks like a number
                            probe_config[current_key][key] = int(value) if value.isdigit() else value
                        except:
                            probe_config[current_key][key] = value
                    else:
                        probe_config[current_key][key] = None
        
        return probe_config if probe_config else None
    
    def _extract_container_port(self, yaml_text: str) -> Optional[int]:
        """
        Extract containerPort value.
        
        Looks for: "containerPort: 9555"
        """
        # Find containerPort line
        match = re.search(r'containerPort:\s*(\d+)', yaml_text)
        if match:
            return int(match.group(1))
        
        return None
    
    def extract_all_from_deployment(self, deployment_yaml: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract configurations for all containers in deployment.
        
        Returns: {
            'server': {
                'livenessProbe': {...},
                'readinessProbe': {...},
                'containerPort': 9555
            }
        }
        
        Note: Currently assumes single container. For multi-container pods,
        this would need enhancement.
        """
        # For now, extract from the first/main container
        # In real scenarios, you'd need to identify container by name
        
        configs = self.extract_from_deployment(deployment_yaml)
        
        # Determine container name from YAML
        container_name = self._extract_container_name(deployment_yaml)
        
        return {container_name: configs}
    
    def _extract_container_name(self, yaml_text: str) -> str:
        """Extract container name from deployment YAML."""
        # Look for "name: server" or similar after "containers:"
        # Pattern: After "containers:" block, find "- name: xxx"
        
        match = re.search(r'containers:\s*\n\s*-[^:]*name:\s*(\w+)', yaml_text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Default
        return 'server'
