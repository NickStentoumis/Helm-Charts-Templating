# extractors/pattern_extractor.py
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict
from models import Deployment, Service, KubernetesResource


class PatternExtractor:
    """Extract common patterns from Kubernetes resources"""
    
    def __init__(self):
        self.deployments: List[Deployment] = []
        self.services: List[Service] = []
        self.service_accounts: List[ServiceAccount] = []
        self.common_patterns: Dict[str, Any] = {}
    7
    def add_resources(self, resources: List[KubernetesResource]):
        """Add resources for pattern extraction"""
        for resource in resources:
            if isinstance(resource, Deployment):
                self.deployments.append(resource)
            elif isinstance(resource, Service):
                self.services.append(resource)
            elif isinstance(resource, ServiceAccount):
                self.service_accounts.append(resource)
    
    def extract_patterns(self) -> Dict[str, Any]:
        """Extract common patterns from all resources"""
        patterns = {
            'deployment_patterns': self._extract_deployment_patterns(),
            'service_patterns': self._extract_service_patterns(),
            'service_account_patterns': self._extract_service_account_patterns(),
            'cross_resource_patterns': self._extract_cross_resource_patterns()
        }
        return patterns
    
    def _extract_deployment_patterns(self) -> Dict[str, Any]:
        """Extract common patterns from deployments"""
        patterns = {
            'common_security_context': self._find_common_dict(
                [d.pod_security_context for d in self.deployments if d.pod_security_context]
            ),
            'common_resource_limits': self._find_common_container_resources(),
            'common_probes': self._find_common_probes(),
            'common_env_patterns': self._find_common_env_patterns(),
            'termination_grace_periods': list(set(
                d.termination_grace_period for d in self.deployments 
                if d.termination_grace_period
            ))
        }
        return patterns
    
    def _extract_service_patterns(self) -> Dict[str, Any]:
        """Extract common patterns from services"""
        service_types = defaultdict(int)
        port_patterns = defaultdict(list)
        
        for service in self.services:
            service_types[service.service_type] += 1
            for port in service.ports:
                port_patterns[port.name].append({
                    'port': port.port,
                    'target_port': port.target_port
                })
        
        return {
            'service_types': dict(service_types),
            'port_patterns': dict(port_patterns),
            'common_selectors': self._find_common_selector_patterns()
        }
    
    def _extract_service_account_patterns(self) -> Dict[str, Any]:
        """Extract common patterns from service accounts"""
        common_annotations = defaultdict(int)
        
        for sa in self.service_accounts:
            for key in sa.metadata.annotations.keys():
                common_annotations[key] += 1
        
        return {
            'common_annotations': dict(common_annotations),
            'all_have_annotations': all(
                sa.metadata.annotations for sa in self.service_accounts
            )
        }
    
    def _extract_cross_resource_patterns(self) -> Dict[str, Any]:
        """Extract patterns across different resource types"""
        service_names = {s.metadata.name for s in self.services}
        deployment_names = {d.metadata.name for d in self.deployments}
        sa_names = {sa.metadata.name for sa in self.service_accounts}
        
        # Extract service naming pattern (e.g., all end with 'service')
        naming_patterns = self._extract_naming_patterns(service_names)
        
        return {
            'matched_resources': len(service_names & deployment_names),
            'naming_patterns': naming_patterns,
            'service_account_coverage': len(sa_names & deployment_names) / len(deployment_names) if deployment_names else 0
        }
    
    def _find_common_dict(self, dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find common key-value pairs across dictionaries"""
        if not dicts:
            return {}
        
        common = dicts[0].copy()
        for d in dicts[1:]:
            common = {k: v for k, v in common.items() if k in d and d[k] == v}
        
        return common
    
    def _find_common_container_resources(self) -> Dict[str, Any]:
        """Find common resource configurations"""
        all_resources = []
        for deployment in self.deployments:
            for container in deployment.containers:
                if container.resources:
                    all_resources.append(container.resources)
        
        return self._find_common_dict(all_resources) if all_resources else {}
    
    def _find_common_probes(self) -> Dict[str, Any]:
        """Find common probe configurations"""
        liveness_probes = []
        readiness_probes = []
        
        for deployment in self.deployments:
            for container in deployment.containers:
                if container.liveness_probe:
                    liveness_probes.append(container.liveness_probe)
                if container.readiness_probe:
                    readiness_probes.append(container.readiness_probe)
        
        return {
            'common_liveness': self._find_common_dict(liveness_probes),
            'common_readiness': self._find_common_dict(readiness_probes)
        }
    
    def _find_common_env_patterns(self) -> List[str]:
        """Find commonly used environment variable names"""
        env_names = defaultdict(int)
        
        for deployment in self.deployments:
            for container in deployment.containers:
                for env in container.env:
                    if isinstance(env, dict) and 'name' in env:
                        env_names[env['name']] += 1
        
        # Return env vars that appear in more than half of containers
        total_containers = sum(len(d.containers) for d in self.deployments)
        common = [name for name, count in env_names.items() 
                 if count > total_containers / 2]
        
        return common
    
    def _find_common_selector_patterns(self) -> Dict[str, Any]:
        """Find common selector patterns in services"""
        selectors = [s.selector for s in self.services if s.selector]
        return self._find_common_dict(selectors) if selectors else {}
    
    def _extract_naming_patterns(self, names: Set[str]) -> Dict[str, Any]:
        """Extract naming patterns from resource names"""
        patterns = {
            'suffix_patterns': defaultdict(int),
            'prefix_patterns': defaultdict(int)
        }
        
        for name in names:
            parts = name.split('-')
            if len(parts) > 1:
                patterns['suffix_patterns'][parts[-1]] += 1
                patterns['prefix_patterns'][parts[0]] += 1
        
        return {
            'common_suffixes': dict(patterns['suffix_patterns']),
            'common_prefixes': dict(patterns['prefix_patterns'])
        }