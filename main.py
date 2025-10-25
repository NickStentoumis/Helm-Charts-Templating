#!/usr/bin/env python3
"""
Helm Chart Refactoring Tool

Main Features::
1. No hardcoded values - everything from values.yaml
2. Analyzes ALL services to include ALL possible fields
3. **Extracts probe configs from YAML and injects into values.yaml**
4. Each service gets its CORRECT configuration
5. Zero functionality loss
"""

import sys
import argparse
from pathlib import Path
import shutil

from parsers.helmify_parser import HelmifyParser
from generators.template_builder import TemplateBuilder
from generators.service_file_generator import ServiceFileGenerator
from generators.values_transformer import ValuesTransformer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Refactor Helmify output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Main Features:
  - Analyzes ALL services to detect ALL fields
  - NO hardcoded values (everything from values.yaml)
  - Each service gets its correct configuration
  - Comprehensive template with conditional blocks

Examples:
  %(prog)s ./helmify-output ./refactored-chart
  %(prog)s ./helmify-output ./refactored-chart --verbose
  %(prog)s ./helmify-output ./refactored-chart --validate
        '''
    )
    
    parser.add_argument(
        'input_dir',
        type=Path,
        help='Input directory containing helmify output'
    )
    
    parser.add_argument(
        'output_dir',
        type=Path,
        help='Output directory for refactored chart'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate generated templates with helm'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without writing files'
    )
    
    parser.add_argument(
        '--no-transform-values',
        action='store_true',
        help='Do not transform values.yaml structure (use original)'
    )
    
    return parser.parse_args()


def validate_with_helm(output_dir: Path, verbose: bool = False):
    """Validate generated templates with helm."""
    import subprocess
    
    try:
        print("\n[Validation] Testing with helm template...")
        result = subprocess.run(
            ['helm', 'template', 'test-release', str(output_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("  Validation PASSED!")
            if verbose:
                print("\n  Sample output:")
                lines = result.stdout.split('\n')[:50]
                for line in lines:
                    print(f"    {line}")
            return True
        else:
            print("  Validation FAILED!")
            print("\n  Errors:")
            for line in result.stderr.split('\n'):
                print(f"    {line}")
            return False
    
    except FileNotFoundError:
        print("  helm command not found (skipping validation)")
        return None
    except subprocess.TimeoutExpired:
        print("  helm validation timed out")
        return None
    except Exception as e:
        print(f"  Could not validate: {e}")
        return None


def main():
    """Main execution function."""
    args = parse_arguments()
    
    input_dir = args.input_dir
    output_dir = args.output_dir
    
    # Validate input
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        sys.exit(1)
    
    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a directory")
        sys.exit(1)
    
    # Banner
    print("=" * 80)
    print("Helm Chart Refactoring Tool")
    print("=" * 80)
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    if args.dry_run:
        print("Mode:   DRY RUN (no files will be written)")
    print("-" * 80)
    
    # Create output directory
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = output_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
    else:
        templates_dir = output_dir / "templates"
    
    # Step 1: Parse helmify output
    print("\n[Step 1] Parsing helmify output...")
    print("  Strategy: Preserve ALL original YAML content")
    
    parser = HelmifyParser()
    services, chart_info = parser.parse_directory(input_dir)
    
    print(f"\n  Found {len(services)} services:")
    for service in services:
        resources = []
        if service.has_deployment():
            resources.append("Deployment")
        if service.has_service():
            resources.append("Service")
        if service.has_service_account():
            resources.append("ServiceAccount")
        if service.other_resources:
            resources.append(f"{len(service.other_resources)} other")
        print(f"    - {service.service_name}: {', '.join(resources)}")
    
    print(f"\n  Chart: {chart_info.chart_name} v{chart_info.chart_version}")
    
    if not services:
        print("\n Error: No services found!")
        sys.exit(1)
    
    # Step 2: Build comprehensive base templates
    print("\n[Step 2] Building comprehensive base templates...")
    print("  Strategy: Analyze ALL services to find ALL fields")
    print("  Result: No hardcoded values, everything from values.yaml")
    
    if not args.dry_run:
        builder = TemplateBuilder(chart_info)
        builder.build_templates(services, templates_dir)
    else:
        print("  (skipped in dry-run mode)")
    
    # Step 3: Generate refactored service files
    print("\n[Step 3] Generating refactored service files...")
    
    if not args.dry_run:
        generator = ServiceFileGenerator(templates_dir)
        for service in services:
            generator.generate(service)
    else:
        for service in services:
            print(f"  Would generate: {service.service_name}.yaml")
    
    # Step 4: Transform values.yaml
    print("\n[Step 4] Processing values.yaml...")
    
    values_file = input_dir / "values.yaml"
    if values_file.exists():
        if not args.dry_run:
            if args.no_transform_values:
                # Copy as-is
                shutil.copy2(values_file, output_dir / "values.yaml")
                print("  Copied: values.yaml (no transformation)")
            else:
                # Transform to new structure AND inject probe configs
                transformer = ValuesTransformer()
                transformer.transform_values_file(
                    values_file, 
                    output_dir / "values.yaml",
                    services  # Pass services so we can extract probes
                )
        else:
            action = "copy" if args.no_transform_values else "transform"
            print(f"  Would {action}: values.yaml")
    else:
        print("  Warning: values.yaml not found")
    
    # Step 5: Copy supporting files
    print("\n[Step 5] Copying supporting files...")
    
    files_to_copy = [
        ('Chart.yaml', 'Chart.yaml'),
        ('_helpers.tpl', 'templates/_helpers.tpl'),
        ('templates/_helpers.tpl', 'templates/_helpers.tpl'),
    ]
    
    copied_count = 0
    for src_path, dst_path in files_to_copy:
        src = input_dir / src_path
        if src.exists():
            if not args.dry_run:
                dst = output_dir / dst_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print(f"  Copied: {src_path}")
                copied_count += 1
            else:
                print(f"  Would copy: {src_path}")
                copied_count += 1
    
    if copied_count == 0:
        print("  Warning: No supporting files found")
    
    # Step 6: Validation (optional)
    if args.validate and not args.dry_run:
        validate_with_helm(output_dir, verbose=args.verbose)
    
    # Summary
    print("\n" + "=" * 80)
    if args.dry_run:
        print("DRY RUN COMPLETE - No files were written")
    else:
        print(" REFACTORING COMPLETE!")
        print(f"\nOutput: {output_dir}")
        print("\nWhat was generated:")
        print(f"  - Base template with {sum(builder.all_features.values())} conditional features")
        print(f"  - {len(services)} refactored service files")
        print(f"  - Transformed values.yaml (containers structure)")
        print(f"  - {copied_count} supporting files")
        
        
        if not args.validate:
            print("\nTip: Run with --validate to test with helm")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
