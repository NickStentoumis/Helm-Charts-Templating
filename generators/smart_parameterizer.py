# generators/smart_parameterizer.py
"""
Intelligently replaces only service-specific references
Preserves all other content including hardcoded values (moves them to values.yaml reference)
"""

import re
from typing import Dict, Set


class SmartParameterizer:
    """
    Converts service-specific YAML to parameterized template.
    
    Key principle: Replace references, preserve structure
    """
    
    def __init__(self, chart_name: str = "helm"):
        self.chart_name = chart_name
        self.detected_patterns = {
            'has_env_vars': False,
            'has_ports': False,
            'has_probes': False,
            'has_resources': False,
            'has_volumes': False,
        }
    
    def parameterize_deployment(self, deployment_yaml: str, service_name: str) -> str:
        """
        Convert deployment YAML to parameterized template.
        
        Strategy:
        1. Replace service-specific value paths: .Values.servicename.X → .Values.X
        2. Replace name references: servicename → {{ .serviceName }}
        3. Replace chart references: . → .root
        4. Keep ALL structure and content (including hardcoded values)
        """
        text = deployment_yaml
        
        # Step 1: Replace value references
        # Pattern: .Values.servicename.field → .Values.field
        text = re.sub(
            rf'\.Values\.{re.escape(service_name)}\.(\w+)',
            r'.Values.\1',
            text
        )
        
        # Step 2: Replace chart fullname helper calls
        # {{ include "chartname.fullname" . }}-servicename → {{ include "chartname.fullname" .root }}-{{ .serviceName }}
        text = re.sub(
            rf'\{{\{{\s*include\s+"{re.escape(self.chart_name)}\.fullname"\s+\.\s*\}}}}-{re.escape(service_name)}',
            '{{ include "' + self.chart_name + '.fullname" .root }}-{{ .serviceName }}',
            text
        )
        
        # Step 3: Replace context in helper calls
        # {{ include "chartname.labels" . }} → {{ include "chartname.labels" .root }}
        text = re.sub(
            rf'\{{\{{\s*include\s+"{re.escape(self.chart_name)}\.(labels|selectorLabels)"\s+\.\s+',
            '{{ include "' + self.chart_name + r'.\1" .root ',
            text
        )
        
        # Step 4: Replace .Chart references
        # .Chart.AppVersion → .root.Chart.AppVersion
        text = re.sub(
            r'\.Chart\.',
            '.root.Chart.',
            text
        )
        
        # Step 5: Replace app label with service name
        # app: servicename → app: {{ .serviceName }}
        text = re.sub(
            rf'^(\s*)app:\s*{re.escape(service_name)}\s*$',
            r'\1app: {{ .serviceName }}',
            text,
            flags=re.MULTILINE
        )
        
        # Step 6: Handle kubernetesClusterDomain
        text = re.sub(
            r'\.Values\.kubernetesClusterDomain',
            '.root.Values.kubernetesClusterDomain',
            text
        )
        
        return text
    
    def parameterize_service(self, service_yaml: str, service_name: str) -> str:
        """Convert service YAML to parameterized template."""
        text = service_yaml
        
        # Same transformations as deployment
        text = re.sub(
            rf'\.Values\.{re.escape(service_name)}\.(\w+)',
            r'.Values.\1',
            text
        )
        
        text = re.sub(
            rf'\{{\{{\s*include\s+"{re.escape(self.chart_name)}\.fullname"\s+\.\s*\}}}}-{re.escape(service_name)}',
            '{{ include "' + self.chart_name + '.fullname" .root }}-{{ .serviceName }}',
            text
        )
        
        text = re.sub(
            rf'\{{\{{\s*include\s+"{re.escape(self.chart_name)}\.(labels|selectorLabels)"\s+\.\s+',
            '{{ include "' + self.chart_name + r'.\1" .root ',
            text
        )
        
        text = re.sub(
            rf'^(\s*)app:\s*{re.escape(service_name)}\s*$',
            r'\1app: {{ .serviceName }}',
            text,
            flags=re.MULTILINE
        )
        
        return text
    
    def analyze_deployment(self, deployment_yaml: str) -> Dict[str, bool]:
        """
        Analyze deployment to detect what features it uses.
        This helps ensure the template includes all necessary fields.
        """
        features = {
            'has_replicas': False,
            'has_strategy': False,
            'has_env_vars': False,
            'has_ports': False,
            'has_liveness_probe': False,
            'has_readiness_probe': False,
            'has_startup_probe': False,
            'has_resources': False,
            'has_volume_mounts': False,
            'has_volumes': False,
            'has_init_containers': False,
            'has_pod_security_context': False,
            'has_container_security_context': False,
            'has_service_account': False,
            'has_termination_grace_period': False,
            'has_host_network': False,
            'has_dns_policy': False,
        }
        
        # Check for each feature
        if re.search(r'^\s*replicas:', deployment_yaml, re.MULTILINE):
            features['has_replicas'] = True
        
        if re.search(r'^\s*strategy:', deployment_yaml, re.MULTILINE):
            features['has_strategy'] = True
        
        if re.search(r'^\s*env:', deployment_yaml, re.MULTILINE):
            features['has_env_vars'] = True
        
        if re.search(r'^\s*ports:', deployment_yaml, re.MULTILINE):
            features['has_ports'] = True
        
        if re.search(r'^\s*livenessProbe:', deployment_yaml, re.MULTILINE):
            features['has_liveness_probe'] = True
        
        if re.search(r'^\s*readinessProbe:', deployment_yaml, re.MULTILINE):
            features['has_readiness_probe'] = True
        
        if re.search(r'^\s*startupProbe:', deployment_yaml, re.MULTILINE):
            features['has_startup_probe'] = True
        
        if re.search(r'^\s*resources:', deployment_yaml, re.MULTILINE):
            features['has_resources'] = True
        
        if re.search(r'^\s*volumeMounts:', deployment_yaml, re.MULTILINE):
            features['has_volume_mounts'] = True
        
        # Check for volumes at pod level (not volumeMounts)
        if re.search(r'^\s*volumes:', deployment_yaml, re.MULTILINE):
            # Make sure it's not inside volumeMounts
            lines = deployment_yaml.split('\n')
            for i, line in enumerate(lines):
                if re.match(r'^\s*volumes:', line):
                    # Check context - should be at pod spec level
                    indent = len(line) - len(line.lstrip())
                    # Look back for spec or template
                    for j in range(max(0, i-10), i):
                        if 'spec:' in lines[j] and indent > len(lines[j]) - len(lines[j].lstrip()):
                            features['has_volumes'] = True
                            break
        
        if re.search(r'^\s*initContainers:', deployment_yaml, re.MULTILINE):
            features['has_init_containers'] = True
        
        if re.search(r'^\s*serviceAccountName:', deployment_yaml, re.MULTILINE):
            features['has_service_account'] = True
        
        if re.search(r'^\s*terminationGracePeriodSeconds:', deployment_yaml, re.MULTILINE):
            features['has_termination_grace_period'] = True
        
        if re.search(r'^\s*hostNetwork:', deployment_yaml, re.MULTILINE):
            features['has_host_network'] = True
        
        if re.search(r'^\s*dnsPolicy:', deployment_yaml, re.MULTILINE):
            features['has_dns_policy'] = True
        
        # Detect security contexts
        # This is tricky - need to differentiate pod vs container security context
        pod_sec = re.search(r'template:.*?spec:.*?securityContext:', deployment_yaml, re.DOTALL)
        if pod_sec:
            # Check if it's before containers section
            containers_match = re.search(r'containers:', deployment_yaml)
            if containers_match and pod_sec.start() < containers_match.start():
                features['has_pod_security_context'] = True
        
        # Container security context is inside container definition
        if re.search(r'containers:.*?securityContext:', deployment_yaml, re.DOTALL):
            features['has_container_security_context'] = True
        
        return features
