"""
Lambada command-line interface
"""

import argparse
import os

def generate_cli() -> argparse.ArgumentParser:
    """
    Generates the lambada CLI

    Args: None

    Returns: argparse.ArgumentParser object representing the lambada CLI
    """
    parser = argparse.ArgumentParser(
        description='lambada: AWS Lambda management via Simiotics Function Registries'
    )

    return parser

def main() -> None:
    """
    Runs the lambada tool

    Args: None

    Returns: None
    """
    function_registry = os.environ.get('SIMIOTICS_FUNCTION_REGISTRY')
    if function_registry is None:
        raise ValueError('SIMIOTICS_FUNCTION_REGISTRY environment variable undefined')

    parser = generate_cli()
    args = parser.parse_args()
    print(args)

if __name__ == '__main__':
    main()
