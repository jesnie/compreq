"""Export distribution metadata.

This will be run as a stand-alone script, in a separate virtual environment.
"""

# Runs in a separate virtual environment, so Can ONLY depend on standard library:
import argparse
import json
from importlib.metadata import distribution
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description="Export metadata about an installed distribution.")
    parser.add_argument("distribution", help="The distribution to export metadata of.")
    args = parser.parse_args()
    dist = distribution(args.distribution)
    result: Any = {
        "name": dist.name,
        "version": dist.version,
        "requires_python": dist.metadata["Requires-Python"] or "",
        "requires": dist.requires or [],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
