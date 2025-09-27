# Helm-Charts-Templating
Tool that takes output from Helmify and creates templates


# Project Structure
```
helm-template-refactor/
│
├── main.py                     # Main entry point
├── requirements.txt            # Dependencies
│
├── models/                     # Domain models
│   ├── __init__.py
│   ├── base.py                # Base classes
│   ├── deployment.py          # Deployment model
│   ├── service.py             # Service model
│   └── service_account.py     # ServiceAccount model
│
├── parsers/                    # YAML parsers for each resource type
│   ├── __init__.py
│   ├── base_parser.py         # Abstract base parser
│   ├── deployment_parser.py   # Deployment parser
│   ├── service_parser.py      # Service parser
│   └── service_account_parser.py
│
├── extractors/                 # Pattern extraction logic
│   ├── __init__.py
│   └── pattern_extractor.py   # Extracts common patterns
│
├── generators/                 # Template generators
│   ├── __init__.py
│   ├── base_template_generator.py
│   └── refactored_template_generator.py
│
└── utils/                      # Utility functions
    ├── __init__.py
    └── yaml_utils.py
```

# requirements.txt
```
PyYAML>=6.0
Jinja2>=3.1.0
```