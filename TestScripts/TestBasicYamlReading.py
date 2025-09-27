"""
Test parsing Helm templates from helmify
This handles the Helm template syntax that causes YAML parsing to fail
"""

import re
from pathlib import Path

def parse_helm_template(file_path: Path):
    """Parse a Helm template file without choking on template syntax"""
    
    print(f"\nParsing: {file_path.name}")
    print("="*50)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace tabs with spaces
    content = content.replace('\t', '  ')
    
    # Split by document separator
    documents = content.split('\n---\n')
    
    resources = []
    
    for i, doc in enumerate(documents):
        if not doc.strip():
            continue
        
        print(f"\nDocument {i+1}:")
        
        # Extract basic info using regex
        resource = {}
        
        # Get apiVersion
        api_match = re.search(r'apiVersion:\s*([^\n]+)', doc)
        if api_match:
            resource['apiVersion'] = api_match.group(1).strip()
            print(f"  API Version: {resource['apiVersion']}")
        
        # Get kind
        kind_match = re.search(r'kind:\s*([^\n]+)', doc)
        if kind_match:
            resource['kind'] = kind_match.group(1).strip()
            print(f"  Kind: {resource['kind']}")
        
        # Get name - handle Helm templates
        name = None
        name_patterns = [
            r'name:\s*\{\{\s*include\s+"[^"]+"\s+\.\s*\}\}-([^\n\s]+)',  # {{ include "..." . }}-servicename
            r'app:\s*([^\n\{\s]+)',  # from labels
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, doc)
            if name_match:
                name = name_match.group(1).strip()
                break
        
        if name:
            resource['name'] = name
            print(f"  Name: {name}")
        
        # Additional parsing based on kind
        if resource.get('kind') == 'Deployment':
            # Get replicas
            replicas_match = re.search(r'replicas:\s*(\d+)', doc)
            if replicas_match:
                resource['replicas'] = int(replicas_match.group(1))
                print(f"  Replicas: {resource['replicas']}")
            
            # Count containers
            containers = re.findall(r'- name:\s*([^\n]+)', doc)
            if containers:
                resource['containers'] = containers
                print(f"  Containers: {containers}")
            
            # Get service account
            sa_match = re.search(r'serviceAccountName:\s*\{\{[^}]+\}\}-([^\n\s]+)', doc)
            if sa_match:
                resource['serviceAccount'] = sa_match.group(1).strip()
                print(f"  Service Account: {resource['serviceAccount']}")
        
        elif resource.get('kind') == 'Service':
            # Get service type
            type_match = re.search(r'type:\s*([^\n\{\s]+)', doc)
            if type_match:
                resource['type'] = type_match.group(1).strip()
                print(f"  Type: {resource['type']}")
            
            # Get ports (simplified)
            ports = re.findall(r'port:\s*(\d+)', doc)
            if ports:
                resource['ports'] = ports
                print(f"  Ports: {ports}")
        
        elif resource.get('kind') == 'ServiceAccount':
            print(f"  ServiceAccount for: {name}")
        
        resources.append(resource)
    
    return resources

def main():
    """Main test function"""
    file_path = input("Enter path to a helmify YAML file (e.g., adservice.yaml): ").strip()
    
    if not file_path:
        print("No file specified")
        return
    
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    try:
        resources = parse_helm_template(file_path)
        
        print("\n" + "="*50)
        print("SUMMARY")
        print("="*50)
        print(f"Total resources found: {len(resources)}")
        
        by_kind = {}
        for r in resources:
            kind = r.get('kind', 'Unknown')
            by_kind[kind] = by_kind.get(kind, 0) + 1
        
        for kind, count in by_kind.items():
            print(f"  {kind}: {count}")
        
        print("\n✅ Successfully parsed Helm template!")
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*60)
    print("HELM TEMPLATE PARSER TEST")
    print("="*60)
    main()