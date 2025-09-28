# standard library imports
import sys
from pathlib import Path

current_file = Path(__file__)
parent_dir = current_file.parent.parent
sys.path.insert(0, str(parent_dir))

from typing import Any, Dict, List, Optional
from models.service import Service, ServicePort
from parsers.service_parser import ServiceParser

def test_service_parser():
    """Test the ServiceParser and Models"""

    # Try to find output from helmify
    print(f"Current directory: {Path.cwd()}")

    try:
        file_path = input("\nEnter path to a service YAML file (e.g., adservice.yaml): ").strip()

        if not file_path:
            print("No file path provided. Exiting test.")
            return
        file_path = Path(file_path)
    except Exception as e:
        print(f"Error reading input: {e}")
        return
    
    print(f"\n1. Creating ServiceParser...")
    service = ServiceParser()

    print(f"2. Parsing {file_path.name}...")
    try:
        services = service.parse_file(file_path)
        if not services:
            print("   No services found in file")
            return
        else:
            print(f"   Found {len(services)} service(s)")
            
            for svc in services:
                print(f"\n Service: {svc}")
                print(f"\n Service Name: {svc.metadata.name}")
                print(f" Service Type: {svc.service_type}")
                print(f" Selector: {svc.selector}")

                if not svc.ports:
                    print(f"\nNo ports defined for {svc.metadata.name}")
                else:
                    print(" Ports:")
                    for port in svc.ports:
                        print(f"  - {port.name}: {port.port} -> {port.target_port} ({port.protocol})")


    except Exception as e:
        print(f"Error parsing file: {e}")
        print("\nDetailed error trace:")
        import traceback
        traceback.print_exc()
        return None
    

if __name__ == "__main__":
    test_service_parser()