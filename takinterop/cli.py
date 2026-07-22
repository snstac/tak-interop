from __future__ import annotations

import argparse
import json

from .validators import ValidationError, validate_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a TAK interoperability artifact")
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        result = validate_path(args.path)
    except ValidationError as error:
        parser.exit(1, f"invalid: {error}\n")
    print(json.dumps(result, sort_keys=True))
