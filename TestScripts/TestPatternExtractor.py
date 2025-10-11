#!/usr/bin/env python3
"""
Debug script to figure out why pattern extraction is empty
"""

import sys
from pathlib import Path
from typing import List
import json

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from models.deployment import Deployment, Container
from models.service import Service, ServicePort
# from models.service_account import ServiceAccount  # SKIPPED
from models.base import ResourceMetadata
from parsers.deployment_parser import DeploymentParser
from parsers.service_parser import ServiceParser
# from parsers.service_account_parser import ServiceAccountParser  # SKIPPED
from extractors.pattern_extractor import PatternExtractor


def debug_parsing(directory_path: str):
    """Debug what's happening during parsing"""
    print("\n" + "="*60)
    print("DEBUGGING PARSING AND EXTRACTION")
    print("="*60)
    
    dir_path = Path(directory_path)
    if not dir_path.exists():
        print(f"❌ Directory not found: {directory_path}")
        return
    
    # Create parsers
    dep_parser = DeploymentParser()
    svc_parser = ServiceParser()
    # sa_parser = ServiceAccountParser()  # SKIPPED
    
    # Track everything
    all_deployments = []
    all_services = []
    # all_service_accounts = []  # SKIPPED
    all_resources = []
    
    yaml_files = list(dir_path.glob('*.yaml'))
    print(f"\nFound {len(yaml_files)} YAML files")
    
    # Parse each file with detailed output
    for file_path in yaml_files:
        print(f"\n📄 Processing: {file_path.name}")
        print("-" * 40)
        
        try:
            # Parse deployments
            deployments = dep_parser.parse_file(file_path)
            if deployments:
                print(f"  ✓ Found {len(deployments)} deployment(s)")
                for dep in deployments:
                    print(f"    - {dep.metadata.name if dep.metadata else 'NO NAME'}")
                    print(f"      Containers: {len(dep.containers)}")
                    print(f"      Security Context: {bool(dep.pod_security_context)}")
                    print(f"      Replicas: {dep.replicas}")
                    
                    # Check container details
                    for cont in dep.containers:
                        print(f"      Container '{cont.name}':")
                        print(f"        Image: {cont.image}")
                        print(f"        Resources: {bool(cont.resources)}")
                        if cont.resources:
                            print(f"          {cont.resources}")
                
                all_deployments.extend(deployments)
                all_resources.extend(deployments)
            
            # Parse services
            services = svc_parser.parse_file(file_path)
            if services:
                print(f"  ✓ Found {len(services)} service(s)")
                for svc in services:
                    print(f"    - {svc.metadata.name if svc.metadata else 'NO NAME'}")
                    print(f"      Type: {svc.service_type}")
                    print(f"      Ports: {len(svc.ports)}")
                    if svc.ports:
                        for port in svc.ports:
                            if isinstance(port, ServicePort):
                                print(f"        - {port.name}: {port.port}->{port.target_port}")
                
                all_services.extend(services)
                all_resources.extend(services)
            
            # SKIPPING SERVICE ACCOUNTS
            
            if not deployments and not services:
                print(f"  ⚠ No resources found in this file")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("PARSING SUMMARY")
    print("="*60)
    print(f"Total Deployments: {len(all_deployments)}")
    print(f"Total Services: {len(all_services)}")
    # print(f"Total ServiceAccounts: {len(all_service_accounts)}")  # SKIPPED
    print(f"Total Resources: {len(all_resources)}")
    
    if not all_resources:
        print("\n❌ NO RESOURCES WERE PARSED!")
        print("This explains why pattern extraction is empty.")
        print("\nPossible causes:")
        print("1. The parser isn't handling Helm templates correctly")
        print("2. The YAML structure is different than expected")
        print("3. The resource 'kind' field isn't being detected")
        return
    
    # Now test pattern extraction
    print("\n" + "="*60)
    print("TESTING PATTERN EXTRACTION")
    print("="*60)
    
    extractor = PatternExtractor()
    
    # Debug: Check what happens when adding resources
    print("\nAdding resources to extractor...")
    print(f"  Deployments in extractor before: {len(extractor.deployments)}")
    print(f"  Services in extractor before: {len(extractor.services)}")
    # print(f"  ServiceAccounts in extractor before: {len(extractor.service_accounts)}")  # SKIPPED
    
    extractor.add_resources(all_resources)
    
    print(f"  Deployments in extractor after: {len(extractor.deployments)}")
    print(f"  Services in extractor after: {len(extractor.services)}")
    # print(f"  ServiceAccounts in extractor after: {len(extractor.service_accounts)}")  # SKIPPED
    
    # Extract patterns with debug
    print("\nExtracting patterns...")
    patterns = extractor.extract_patterns()
    
    # Debug the extraction results
    print("\n" + "-"*40)
    print("EXTRACTION RESULTS DEBUG:")
    print("-"*40)
    
    # Check deployment patterns
    dep_patterns = patterns.get('deployment_patterns', {})
    print(f"\nDeployment Patterns:")
    print(f"  Common security context: {dep_patterns.get('common_security_context', {})}")
    print(f"  Common resources: {dep_patterns.get('common_resource_limits', {})}")
    print(f"  Common env vars: {dep_patterns.get('common_env_patterns', [])}")
    print(f"  Termination periods: {dep_patterns.get('termination_grace_periods', [])}")
    
    # Debug why security context might be empty
    if extractor.deployments:
        print("\nSecurity contexts found:")
        for dep in extractor.deployments[:3]:  # First 3 deployments
            print(f"  {dep.metadata.name}: {dep.pod_security_context}")
    
    # Check service patterns
    svc_patterns = patterns.get('service_patterns', {})
    print(f"\nService Patterns:")
    print(f"  Service types: {svc_patterns.get('service_types', {})}")
    print(f"  Port patterns: {svc_patterns.get('port_patterns', {})}")
    
    # Debug service types
    if extractor.services:
        print("\nService types found:")
        for svc in extractor.services[:3]:  # First 3 services
            print(f"  {svc.metadata.name}: {svc.service_type}")
    
    # Save detailed debug info
    debug_info = {
        'parsing_stats': {
            'files_processed': len(yaml_files),
            'deployments_parsed': len(all_deployments),
            'services_parsed': len(all_services),
            # 'service_accounts_parsed': len(all_service_accounts)  # SKIPPED
        },
        'extraction_stats': {
            'deployments_in_extractor': len(extractor.deployments),
            'services_in_extractor': len(extractor.services),
            # 'service_accounts_in_extractor': len(extractor.service_accounts)  # SKIPPED
        },
        'patterns': patterns,
        'sample_deployment': extractor.deployments[0].__dict__ if extractor.deployments else None,
        'sample_service': extractor.services[0].__dict__ if extractor.services else None
    }
    
    debug_file = Path('debug_pattern_extraction.json')
    with open(debug_file, 'w') as f:
        json.dump(debug_info, f, indent=2, default=str)
    
    print(f"\n💾 Debug info saved to: {debug_file}")
    
    return patterns


def main():
    """Main debug function"""
    print("="*60)
    print("PATTERN EXTRACTION DEBUGGER")
    print("="*60)
    
    directory = input("\nEnter directory path with helmify YAML files: ").strip()
    if not directory:
        print("No directory specified")
        return
    
    debug_parsing(directory)


if __name__ == "__main__":
    main()