"""
Schema Validator for ECCOS Configuration Files
==============================================
Validates scenario and solver YAML files against the canonical JSON Schema
(config_schema.json) to ensure structural integrity and parameter compliance
prior to running long simulations.
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Tuple, List, Optional

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "config_schema.json"


def validate_yaml_config(
    file_path: str | Path, 
    schema_path: Optional[str | Path] = None
) -> Tuple[bool, List[str]]:
    """
    Validates a YAML configuration file against the ECCOS JSON schema.

    Args:
        file_path: Path to the YAML file to validate.
        schema_path: Optional path to the JSON Schema. If None, uses DEFAULT_SCHEMA_PATH.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list of error messages if any)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]

    schema_file = Path(schema_path) if schema_path else DEFAULT_SCHEMA_PATH
    if not schema_file.exists():
        return False, [f"Schema file not found: {schema_file}"]

    # 1. Parse YAML
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return False, [f"YAML syntax error: {str(e)}"]

    if not isinstance(data, dict):
        return False, ["Configuration file must contain a top-level YAML mapping/dictionary."]

    # 2. Parse Schema
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except Exception as e:
        return False, [f"Schema parsing error: {str(e)}"]

    # 3. Validate with jsonschema
    try:
        import jsonschema
        validator = jsonschema.Draft7Validator(schema)
        errors = []
        for err in validator.iter_errors(data):
            loc = " -> ".join(str(p) for p in err.absolute_path)
            loc_str = f" at '{loc}'" if loc else " at root"
            errors.append(f"{err.message}{loc_str}")

        if errors:
            return False, errors
        return True, []

    except ImportError:
        # Fallback check if jsonschema is unexpectedly missing
        missing_keys = []
        if "scenario_name" in data:
            for k in ["infrastructure", "app", "user"]:
                if k not in data:
                    missing_keys.append(f"Missing required section: {k}")
        elif "solver_name" in data:
            for k in ["setup", "trigger_policy"]:
                if k not in data:
                    missing_keys.append(f"Missing required section: {k}")
        if missing_keys:
            return False, missing_keys
        return True, ["(Validated using basic schema heuristics — install jsonschema for full check)"]


def validate_and_print(file_path: str | Path, schema_path: Optional[str | Path] = None) -> bool:
    """Validates a configuration file and prints human-readable status to console."""
    file_path = Path(file_path)
    is_valid, errors = validate_yaml_config(file_path, schema_path)

    if is_valid:
        print(f"[OK] {file_path} is valid.")
        return True
    else:
        print(f"[FAIL] {file_path} has validation errors:")
        for err in errors:
            print(f"   - {err}")
        return False


def main() -> None:
    """CLI entry point for standalone schema validation."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.schema_validator <config1.yaml> [config2.yaml ...]")
        print("       eccos --validate <config.yaml>")
        sys.exit(1)

    all_passed = True
    for arg in sys.argv[1:]:
        if not validate_and_print(arg):
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
