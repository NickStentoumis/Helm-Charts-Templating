#!/usr/bin/env python3
"""
Test the DeploymentParser class
"""

# Standard library imports
import sys
from pathlib import Path

# Fix the import path FIRST before any other imports
current_file = Path(__file__)
parent_dir = current_file.parent.parent
sys.path.insert(0, str(parent_dir))

# Now import our modules (these will work because we fixed the path)
from models.base import ResourceMetadata
from models.deployment import Deployment, Container
from parsers.deployment_parser import DeploymentParser

def test_deployment_parser():
    """Test the DeploymentParser"""
    
    # Try to find helmify files
    print(f"Current directory: {Path.cwd()}")
    print(f"Script location: {current_file}")
    print(f"Looking for files in parent: {parent_dir}")
    
    file_path = input("\nEnter path to a deployment YAML file (e.g., adservice.yaml): ").strip()
    
    # If no path given, try to find it
    if not file_path:
        # Look in common locations
        possible_locations = [
            parent_dir / "adservice.yaml",
            parent_dir / "helmify-output" / "adservice.yaml",
            Path.cwd() / "adservice.yaml",
        ]
        
        for possible_path in possible_locations:
            if possible_path.exists():
                file_path = str(possible_path)
                print(f"Found file at: {file_path}")
                break
    
    file_path = Path(file_path) if file_path else None
    
    if not file_path or not file_path.exists():
        print(f"\n File not found: {file_path}")
        print("Please provide the full path to your YAML file.")
        return
    
    print(f"\n1. Creating DeploymentParser...")
    parser = DeploymentParser()
    
    print(f"2. Parsing {file_path.name}...")
    try:
        deployments = parser.parse_file(file_path)
        
        if not deployments:
            print("   No deployments found in file")
            return
        
        print(f" Found {len(deployments)} deployment(s)")
        
        for dep in deployments:
            print(f"\n   📦 Deployment: {dep.metadata.name}")
            print(f"      API Version: {dep.api_version}")
            print(f"      Replicas: {dep.replicas}")
            print(f"      Service Account: {dep.service_account_name}")
            print(f"      Containers: {len(dep.containers)}")
            
            for cont in dep.containers:
                print(f"        • {cont.name}: {cont.image}")
                if cont.ports:
                    print(f"          Ports: {[p.get('containerPort') for p in cont.ports if isinstance(p, dict)]}")
                if cont.env:
                    print(f"          Env vars: {len(cont.env)} defined")
            
            if dep.pod_security_context:
                print(f"      Security Context: Present")
                if 'runAsNonRoot' in dep.pod_security_context:
                    print(f"        - runAsNonRoot: {dep.pod_security_context['runAsNonRoot']}")
                if 'fsGroup' in dep.pod_security_context:
                    print(f"        - fsGroup: {dep.pod_security_context['fsGroup']}")
            
            # Test getting template params
            params = dep.get_template_params()
            print(f"      Template params available: {len(params)} keys")
            
            # Test getting patterns
            patterns = dep.get_common_patterns()
            print(f"      Pattern analysis: {patterns}")
        
        print("\n DeploymentParser test successful!")
        return deployments
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        print("\nDetailed error trace:")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("="*60)
    print("DEPLOYMENT PARSER TEST")
    print("="*60)
    test_deployment_parser()
    print("="*60)