# generators/refactored_template_generator.py
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml


class RefactoredTemplateGenerator:
    """Generate refactored templates that use base templates"""
    
    def __init__(self, base_templates: Dict[str, str]):
        self.base_templates = base_templates
    
    def generate_service_template(self, service_name: str, values: Dict[str, Any]) -> str:
        """Generate a refactored service template file"""
        template = f'''{{{{/*
{service_name}.yaml - Refactored to work with existing helmify values.yaml structure
Place this in templates/{service_name}.yaml
*/}}}}

{{{{- include "microservice.deployment.helmify" (dict "Values" .Values.{service_name} "root" . "serviceName" "{service_name}" "terminationGracePeriodSeconds" 5) }}}}
---
{{{{- include "microservice.service.helmify" (dict "Values" .Values.{service_name} "root" . "serviceName" "{service_name}") }}}}
---
{{{{- include "microservice.serviceAccount.helmify" (dict "Values" .Values.{service_name} "root" . "serviceName" "{service_name}") }}}}'''
        
        return template
    
    def generate_base_helpers(self) -> str:
        """Generate the base helper templates that work with helmify structure"""
        helpers = '''{{/*
Base deployment template for microservices - works with helmify values structure
*/}}
{{- define "microservice.deployment.helmify" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "helm.fullname" .root }}-{{ .serviceName }}
  labels:
    app: {{ .serviceName }}
  {{- include "helm.labels" .root | nindent 4 }}
spec:
  {{- if .Values.replicas }}
  replicas: {{ .Values.replicas }}
  {{- end }}
  selector:
    matchLabels:
      app: {{ .serviceName }}
    {{- include "helm.selectorLabels" .root | nindent 6 }}
  template:
    metadata:
      labels:
        app: {{ .serviceName }}
      {{- include "helm.selectorLabels" .root | nindent 8 }}
    spec:
      {{- with .Values.server }}
      containers:
      - name: server
        image: {{ .image.repository }}:{{ .image.tag | default $.root.Chart.AppVersion }}
        {{- if .env }}
        env:
        {{- range $key, $value := .env }}
        - name: {{ $key | upper | replace "." "_" }}
          value: {{ $value | quote }}
        {{- end }}
        - name: KUBERNETES_CLUSTER_DOMAIN
          value: {{ $.root.Values.kubernetesClusterDomain | quote }}
        {{- end }}
        {{- if $.Values.ports }}
        ports:
        {{- range $.Values.ports }}
        - containerPort: {{ .targetPort | default .port }}
        {{- if .name }}
          name: {{ .name }}
        {{- end }}
        {{- end }}
        {{- end }}
        {{- with .resources }}
        resources: {{- toYaml . | nindent 10 }}
        {{- end }}
        {{- with .containerSecurityContext }}
        securityContext: {{- toYaml . | nindent 10 }}
        {{- end }}
      {{- end }}
      {{- with .Values.podSecurityContext }}
      securityContext: {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "helm.fullname" .root }}-{{ .serviceName }}
      {{- if .terminationGracePeriodSeconds }}
      terminationGracePeriodSeconds: {{ .terminationGracePeriodSeconds }}
      {{- end }}
{{- end }}

{{/*
Base service template for microservices - works with helmify values structure
*/}}
{{- define "microservice.service.helmify" -}}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "helm.fullname" .root }}-{{ .serviceName }}
  labels:
    app: {{ .serviceName }}
  {{- include "helm.labels" .root | nindent 4 }}
spec:
  type: {{ .Values.type | default "ClusterIP" }}
  selector:
    app: {{ .serviceName }}
  {{- include "helm.selectorLabels" .root | nindent 4 }}
  ports:
  {{- .Values.ports | toYaml | nindent 2 }}
{{- end }}

{{/*
Base service account template - works with helmify values structure
*/}}
{{- define "microservice.serviceAccount.helmify" -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "helm.fullname" .root }}-{{ .serviceName }}
  labels:
  {{- include "helm.labels" .root | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}'''
        
        return helpers
    
    def save_refactored_templates(self, output_dir: Path, services: List[str]):
        """Save refactored templates"""
        templates_dir = output_dir / 'templates'
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Save base helpers
        helpers_path = templates_dir / '_helpers-microservice.yaml'
        with open(helpers_path, 'w') as f:
            f.write(self.generate_base_helpers())
        
        # Generate refactored templates for each service
        for service in services:
            service_name = service.replace('service', '').replace('-', '')
            if not service_name:
                service_name = service
            
            template = self.generate_service_template(service_name, {})
            file_path = templates_dir / f'{service_name}.yaml'
            
            with open(file_path, 'w') as f:
                f.write(template)
