import sys

import yaml

try:
    with open("openapi.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    print("✓ YAML syntax is valid")
    print(f"✓ OpenAPI version: {data.get('openapi')}")
    print(f"✓ Title: {data.get('info', {}).get('title')}")
    print(f"✓ Paths: {len(data.get('paths', {}))} endpoints")
    print(f"✓ Schemas: {len(data.get('components', {}).get('schemas', {}))} schemas")
    print(
        f"✓ Responses: {len(data.get('components', {}).get('responses', {}))} responses"
    )
    print(
        f"✓ Security Schemes: {len(data.get('components', {}).get('securitySchemes', {}))} schemes"
    )

    # Count endpoints with authentication based on explicit security declarations
    auth_endpoints = 0
    public_endpoints = 0

    for _path, methods in data.get("paths", {}).items():
        for _method, details in methods.items():
            if isinstance(details, dict):
                operation_security = details.get("security", None)
                # If operation explicitly sets security to [], it's public
                if operation_security == []:
                    public_endpoints += 1
                else:
                    # Inherits global security or has its own security definition
                    auth_endpoints += 1

    print(f"✓ Endpoints with authentication: {auth_endpoints}")
    print(f"✓ Public endpoints (no auth): {public_endpoints}")
    print("\nNote: Some endpoints may require authentication via dependencies")
    print("      even if not explicitly marked in the OpenAPI spec.")

    # List all endpoints
    print("\nEndpoints found:")
    for path in sorted(data.get("paths", {}).keys()):
        methods = [
            m.upper()
            for m in data["paths"][path].keys()
            if m in ["get", "post", "put", "patch", "delete"]
        ]
        print(f"  {', '.join(methods)} {path}")

    sys.exit(0)

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
