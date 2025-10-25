# generators/template_builder.py
"""
V2 Template Builder: Analyzes ALL services to create comprehensive template
NO hardcoded values - everything comes from values.yaml
"""

from pathlib import Path
from typing import List, Dict, Set
from models.resource import ServiceResources, ChartInfo
from .smart_parameterizer import SmartParameterizer


class TemplateBuilder:
    """
    Builds comprehensive base templates by analyzing ALL services.
    
    Key strategy:
    - Analyze ALL deployments to find ALL possible fields
    - Create template with conditional blocks for each field
    - Use values.yaml for ALL data (no hardcoded values)
    """
    
    def __init__(self, chart_info: ChartInfo):
        self.chart_info = chart_info
        self.parameterizer = SmartParameterizer(chart_info.chart_name)
        
        # Aggregate features from ALL services
        self.all_features = {
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
            'has_command': False,
            'has_args': False,
            'has_image_pull_policy': False,
        }
    
    def build_templates(self, services: List[ServiceResources], output_dir: Path):
        """
        Build base templates by analyzing ALL services.
        """
        # Analyze ALL services to find ALL features
        print("\n  Analyzing all services to detect features...")
        for service in services:
            if service.has_deployment():
                features = self.parameterizer.analyze_deployment(service.deployment_yaml)
                # Merge features (OR operation - if ANY service has it, template should support it)
                for key, value in features.items():
                    if value:
                        self.all_features[key] = True
                        print(f"    {service.service_name}: has {key}")
        
        print(f"\n  Template will support {sum(self.all_features.values())} different features")
        
        # Generate deployment template
        deployment_template = self._generate_deployment_template()
        
        # Generate service template
        service_template = self._generate_service_template()
        
        # Combine into helpers file
        helpers_content = self._create_helpers_file(deployment_template, service_template)
        
        # Write to file
        output_file = output_dir / "_helpers-microservice.yaml"
        output_file.write_text(helpers_content, encoding='utf-8')
        print(f"\n  Generated: _helpers-microservice.yaml")
        print(f"  Template size: {len(helpers_content)} bytes")
    
    def _generate_deployment_template(self) -> str:
        """
        Generate comprehensive deployment template with ALL possible fields.
        
        CRITICAL: Uses values.yaml for ALL varying data (no hardcoded values)
        """
        lines = []
        
        # Header
        lines.append('{{/*')
        lines.append('Comprehensive deployment template for microservices')
        lines.append('Supports ALL fields found across all services')
        lines.append('NO hardcoded values - everything from values.yaml')
        lines.append('*/}}')
        lines.append('{{- define "microservice.deployment.helmify" -}}')
        lines.append('apiVersion: apps/v1')
        lines.append('kind: Deployment')
        lines.append('metadata:')
        lines.append('  name: {{ include "' + self.chart_info.chart_name + '.fullname" .root }}-{{ .serviceName }}')
        lines.append('  labels:')
        lines.append('    app: {{ .serviceName }}')
        lines.append('  {{- include "' + self.chart_info.chart_name + '.labels" .root | nindent 4 }}')
        lines.append('spec:')
        
        # Replicas (optional)
        if self.all_features['has_replicas']:
            lines.append('  {{- if .Values.replicas }}')
            lines.append('  replicas: {{ .Values.replicas }}')
            lines.append('  {{- end }}')
        
        # Strategy (optional)
        if self.all_features['has_strategy']:
            lines.append('  {{- with .Values.strategy }}')
            lines.append('  strategy:')
            lines.append('    {{- toYaml . | nindent 4 }}')
            lines.append('  {{- end }}')
        
        # Selector
        lines.append('  selector:')
        lines.append('    matchLabels:')
        lines.append('      app: {{ .serviceName }}')
        lines.append('    {{- include "' + self.chart_info.chart_name + '.selectorLabels" .root | nindent 6 }}')
        
        # Template
        lines.append('  template:')
        lines.append('    metadata:')
        lines.append('      labels:')
        lines.append('        app: {{ .serviceName }}')
        lines.append('      {{- include "' + self.chart_info.chart_name + '.selectorLabels" .root | nindent 8 }}')
        lines.append('    spec:')
        
        # Init containers (optional)
        if self.all_features['has_init_containers']:
            lines.append('      {{- with .Values.initContainers }}')
            lines.append('      initContainers:')
            lines.append('        {{- toYaml . | nindent 6 }}')
            lines.append('      {{- end }}')
        
        # Main containers section
        lines.append('      containers:')
        lines.append('      {{- range $containerName, $container := .Values.containers }}')
        lines.append('      - name: {{ $containerName }}')
        
        # Image (ALWAYS required)
        lines.append('        image: {{ $container.image.repository }}:{{ $container.image.tag | default $.root.Chart.AppVersion }}')
        
        # Image pull policy (optional)
        if self.all_features['has_image_pull_policy']:
            lines.append('        {{- if $container.image.pullPolicy }}')
            lines.append('        imagePullPolicy: {{ $container.image.pullPolicy }}')
            lines.append('        {{- end }}')
        
        # Command (optional)
        if self.all_features['has_command']:
            lines.append('        {{- with $container.command }}')
            lines.append('        command:')
            lines.append('          {{- toYaml . | nindent 10 }}')
            lines.append('        {{- end }}')
        
        # Args (optional)
        if self.all_features['has_args']:
            lines.append('        {{- with $container.args }}')
            lines.append('        args:')
            lines.append('          {{- toYaml . | nindent 10 }}')
            lines.append('        {{- end }}')
        
        # Environment variables (optional but common)
        if self.all_features['has_env_vars']:
            lines.append('        {{- if $container.env }}')
            lines.append('        env:')
            lines.append('        {{- range $key, $value := $container.env }}')
            lines.append('        - name: {{ $key | upper | replace "." "_" | replace "-" "_" }}')
            lines.append('          value: {{ $value | quote }}')
            lines.append('        {{- end }}')
            lines.append('        {{- if $.root.Values.kubernetesClusterDomain }}')
            lines.append('        - name: KUBERNETES_CLUSTER_DOMAIN')
            lines.append('          value: {{ quote $.root.Values.kubernetesClusterDomain }}')
            lines.append('        {{- end }}')
            lines.append('        {{- end }}')
        
        # Ports (optional but very common)
        if self.all_features['has_ports']:
            lines.append('        {{- if $.Values.ports }}')
            lines.append('        ports:')
            lines.append('        {{- range $.Values.ports }}')
            lines.append('        - containerPort: {{ .targetPort | default .port }}')
            lines.append('          {{- if .name }}')
            lines.append('          name: {{ .name }}')
            lines.append('          {{- end }}')
            lines.append('          {{- if .protocol }}')
            lines.append('          protocol: {{ .protocol }}')
            lines.append('          {{- end }}')
            lines.append('        {{- end }}')
            lines.append('        {{- end }}')
        
        # Liveness probe (optional)
        if self.all_features['has_liveness_probe']:
            lines.append('        {{- with $container.livenessProbe }}')
            lines.append('        livenessProbe:')
            lines.append('          {{- toYaml . | nindent 10 }}')
            lines.append('        {{- end }}')
        
        # Readiness probe (optional)
        if self.all_features['has_readiness_probe']:
            lines.append('        {{- with $container.readinessProbe }}')
            lines.append('        readinessProbe:')
            lines.append('          {{- toYaml . | nindent 10 }}')
            lines.append('        {{- end }}')
        
        # Startup probe (optional)
        if self.all_features['has_startup_probe']:
            lines.append('        {{- with $container.startupProbe }}')
            lines.append('        startupProbe:')
            lines.append('          {{- toYaml . | nindent 10 }}')
            lines.append('        {{- end }}')
        
        # Resources (optional but recommended)
        if self.all_features['has_resources']:
            lines.append('        {{- with $container.resources }}')
            lines.append('        resources:')
            lines.append('          {{- toYaml . | nindent 10 }}')
            lines.append('        {{- end }}')
        
        # Volume mounts (optional)
        if self.all_features['has_volume_mounts']:
            lines.append('        {{- with $container.volumeMounts }}')
            lines.append('        volumeMounts:')
            lines.append('          {{- toYaml . | nindent 10 }}')
            lines.append('        {{- end }}')
        
        # Container security context (optional)
        if self.all_features['has_container_security_context']:
            lines.append('        {{- with $container.securityContext }}')
            lines.append('        securityContext:')
            lines.append('          {{- toYaml . | nindent 10 }}')
            lines.append('        {{- end }}')
        
        lines.append('      {{- end }}')  # End containers range
        
        # Pod-level configurations
        
        # Pod security context (optional)
        if self.all_features['has_pod_security_context']:
            lines.append('      {{- with .Values.podSecurityContext }}')
            lines.append('      securityContext:')
            lines.append('        {{- toYaml . | nindent 8 }}')
            lines.append('      {{- end }}')
        
        # Service account (optional)
        if self.all_features['has_service_account']:
            lines.append('      {{- if .Values.serviceAccountName }}')
            lines.append('      serviceAccountName: {{ include "' + self.chart_info.chart_name + '.fullname" .root }}-{{ .serviceName }}')
            lines.append('      {{- end }}')
        
        # Termination grace period (optional)
        if self.all_features['has_termination_grace_period']:
            lines.append('      {{- if .Values.terminationGracePeriodSeconds }}')
            lines.append('      terminationGracePeriodSeconds: {{ .Values.terminationGracePeriodSeconds }}')
            lines.append('      {{- end }}')
        
        # Host network (optional)
        if self.all_features['has_host_network']:
            lines.append('      {{- if .Values.hostNetwork }}')
            lines.append('      hostNetwork: {{ .Values.hostNetwork }}')
            lines.append('      {{- end }}')
        
        # DNS policy (optional)
        if self.all_features['has_dns_policy']:
            lines.append('      {{- if .Values.dnsPolicy }}')
            lines.append('      dnsPolicy: {{ .Values.dnsPolicy }}')
            lines.append('      {{- end }}')
        
        # Volumes (optional)
        if self.all_features['has_volumes']:
            lines.append('      {{- with .Values.volumes }}')
            lines.append('      volumes:')
            lines.append('        {{- toYaml . | nindent 6 }}')
            lines.append('      {{- end }}')
        
        lines.append('{{- end }}')
        
        return '\n'.join(lines)
    
    def _generate_service_template(self) -> str:
        """Generate comprehensive service template."""
        lines = []
        
        lines.append('{{/*')
        lines.append('Comprehensive service template for microservices')
        lines.append('*/}}')
        lines.append('{{- define "microservice.service.helmify" -}}')
        lines.append('apiVersion: v1')
        lines.append('kind: Service')
        lines.append('metadata:')
        lines.append('  name: {{ include "' + self.chart_info.chart_name + '.fullname" .root }}-{{ .serviceName }}')
        lines.append('  labels:')
        lines.append('    app: {{ .serviceName }}')
        lines.append('  {{- include "' + self.chart_info.chart_name + '.labels" .root | nindent 4 }}')
        lines.append('spec:')
        lines.append('  type: {{ .Values.type | default "ClusterIP" }}')
        lines.append('  selector:')
        lines.append('    app: {{ .serviceName }}')
        lines.append('  {{- include "' + self.chart_info.chart_name + '.selectorLabels" .root | nindent 4 }}')
        lines.append('  {{- if .Values.ports }}')
        lines.append('  ports:')
        lines.append('  {{- range .Values.ports }}')
        lines.append('  - name: {{ .name }}')
        lines.append('    port: {{ .port }}')
        lines.append('    targetPort: {{ .targetPort | default .port }}')
        lines.append('    {{- if .protocol }}')
        lines.append('    protocol: {{ .protocol }}')
        lines.append('    {{- end }}')
        lines.append('    {{- if and (eq $.Values.type "NodePort") .nodePort }}')
        lines.append('    nodePort: {{ .nodePort }}')
        lines.append('    {{- end }}')
        lines.append('  {{- end }}')
        lines.append('  {{- end }}')
        lines.append('{{- end }}')
        
        return '\n'.join(lines)
    
    def _create_helpers_file(self, deployment_template: str, service_template: str) -> str:
        """Combine templates into helpers file."""
        parts = [
            '{{/*',
            'Base templates for microservices',
            'Auto-generated by analyzing ALL services in helmify output',
            '',
            'KEY FEATURES:',
            '- NO hardcoded values (everything from values.yaml)',
            '- Supports ALL fields found across all services',
            '- Conditional blocks for optional fields',
            '- Each service gets exactly what it needs',
            '*/',
            '',
            deployment_template,
            '',
            service_template,
        ]
        
        return '\n'.join(parts) + '\n'
