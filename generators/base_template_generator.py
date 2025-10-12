# generators/base_template_generator.py
from typing import Dict, Any, List
from pathlib import Path
import yaml
from jinja2 import Template


class BaseTemplateGenerator:
    """Generate base templates for common Kubernetes resources"""
    
    def __init__(self, patterns: Dict[str, Any]):
        self.patterns = patterns
        self.base_templates = {}
    
    def generate_all_templates(self) -> Dict[str, str]:
        """Generate all base templates"""
        self.base_templates = {
            'deployment': self._generate_deployment_template(),
            'service': self._generate_service_template(),
            'serviceaccount': self._generate_service_account_template()
        }
        return self.base_templates
    
    def _generate_deployment_template(self) -> str:
        """Generate base deployment template"""
        template = '''{{- define "{{ template_name }}.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ "{{ include \"" }}{{ chart_name }}{{ ".fullname\" . }}-{{ .serviceName }}" }}
  labels:
    app: {{ "{{ .serviceName }}" }}
  {{- "{{ include \"" }}{{ chart_name }}{{ ".labels\" . | nindent 4 }}" }}
spec:
  {{- "{{ if .replicas }}" }}
  replicas: {{ "{{ .replicas }}" }}
  {{- "{{ end }}" }}
  selector:
    matchLabels:
      app: {{ "{{ .serviceName }}" }}
    {{- "{{ include \"" }}{{ chart_name }}{{ ".selectorLabels\" . | nindent 6 }}" }}
  template:
    metadata:
      labels:
        app: {{ "{{ .serviceName }}" }}
      {{- "{{ include \"" }}{{ chart_name }}{{ ".selectorLabels\" . | nindent 8 }}" }}
      {{- "{{ with .podAnnotations }}" }}
      annotations:
        {{- "{{ toYaml . | nindent 8 }}" }}
      {{- "{{ end }}" }}
    spec:
      {{- "{{ with .containers }}" }}
      containers:
      {{- "{{ range . }}" }}
      - name: {{ "{{ .name }}" }}
        image: {{ "{{ .image }}" }}
        {{- "{{ with .env }}" }}
        env:
        {{- "{{ toYaml . | nindent 8 }}" }}
        {{- "{{ end }}" }}
        {{- "{{ with .ports }}" }}
        ports:
        {{- "{{ toYaml . | nindent 8 }}" }}
        {{- "{{ end }}" }}
        {{- "{{ with .livenessProbe }}" }}
        livenessProbe:
          {{- "{{ toYaml . | nindent 10 }}" }}
        {{- "{{ end }}" }}
        {{- "{{ with .readinessProbe }}" }}
        readinessProbe:
          {{- "{{ toYaml . | nindent 10 }}" }}
        {{- "{{ end }}" }}
        {{- "{{ with .resources }}" }}
        resources:
          {{- "{{ toYaml . | nindent 10 }}" }}
        {{- "{{ end }}" }}
        {{- "{{ with .securityContext }}" }}
        securityContext:
          {{- "{{ toYaml . | nindent 10 }}" }}
        {{- "{{ end }}" }}
        {{- "{{ with .volumeMounts }}" }}
        volumeMounts:
        {{- "{{ toYaml . | nindent 8 }}" }}
        {{- "{{ end }}" }}
      {{- "{{ end }}" }}
      {{- "{{ end }}" }}
      {{- "{{ with .initContainers }}" }}
      initContainers:
      {{- "{{ toYaml . | nindent 6 }}" }}
      {{- "{{ end }}" }}
      {{- "{{ with .podSecurityContext }}" }}
      securityContext:
        {{- "{{ toYaml . | nindent 8 }}" }}
      {{- "{{ end }}" }}
      {{- "{{ if .serviceAccountName }}" }}
      serviceAccountName: {{ "{{ .serviceAccountName }}" }}
      {{- "{{ end }}" }}
      {{- "{{ with .terminationGracePeriodSeconds }}" }}
      terminationGracePeriodSeconds: {{ "{{ . }}" }}
      {{- "{{ end }}" }}
      {{- "{{ with .volumes }}" }}
      volumes:
      {{- "{{ toYaml . | nindent 6 }}" }}
      {{- "{{ end }}" }}
{{- "{{ end }}" -}}'''
        return template
    
    def _generate_service_template(self) -> str:
        """Generate base service template"""
        template = '''{{- define "{{ template_name }}.service" -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ "{{ include \"" }}{{ chart_name }}{{ ".fullname\" . }}-{{ .serviceName }}" }}
  labels:
    app: {{ "{{ .serviceName }}" }}
  {{- "{{ include \"" }}{{ chart_name }}{{ ".labels\" . | nindent 4 }}" }}
spec:
  type: {{ "{{ .type | default \"ClusterIP\" }}" }}
  selector:
    app: {{ "{{ .serviceName }}" }}
  {{- "{{ include \"" }}{{ chart_name }}{{ ".selectorLabels\" . | nindent 4 }}" }}
  {{- "{{ with .ports }}" }}
  ports:
  {{- "{{ toYaml . | nindent 2 }}" }}
  {{- "{{ end }}" }}
{{- "{{ end }}" -}}'''
        return template
    
    def _generate_service_account_template(self) -> str:
        """Generate base service account template"""
        template = '''{{- define "{{ template_name }}.serviceaccount" -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ "{{ include \"" }}{{ chart_name }}{{ ".fullname\" . }}-{{ .serviceName }}" }}
  labels:
  {{- "{{ include \"" }}{{ chart_name }}{{ ".labels\" . | nindent 4 }}" }}
  {{- "{{ with .annotations }}" }}
  annotations:
    {{- "{{ toYaml . | nindent 4 }}" }}
  {{- "{{ end }}" }}
{{- "{{ end }}" -}}'''
        return template
    
    def save_templates(self, output_dir: Path):
        """Save templates to files"""
        templates_dir = output_dir / 'templates' / '_base'
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        for name, content in self.base_templates.items():
            file_path = templates_dir / f'{name}.yaml'
            # Replace placeholders with actual values
            content = content.replace('{{ template_name }}', 'microservice')
            content = content.replace('{{ chart_name }}', 'helm')
            
            with open(file_path, 'w') as f:
                f.write(content)