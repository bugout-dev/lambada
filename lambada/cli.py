"""
Lambada command-line interface
"""

import argparse
import os
from typing import Any, Callable

from simiotics.cli import read_string_from_file
from simiotics.client import client_from_env, Simiotics

from . import handlers

LambdaBasicExecutionRolePolicy = """
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
""".strip()

def generate_cli() -> argparse.ArgumentParser:
    """
    Generates the lambada CLI

    Args: None

    Returns: argparse.ArgumentParser object representing the lambada CLI
    """
    parser = argparse.ArgumentParser(
        description='lambada: AWS Lambda management via Simiotics Function Registries'
    )

    subparsers = parser.add_subparsers(title='Commands')

    register = subparsers.add_parser(
        'register',
        help='Register a new Lambda function against a Simiotics Function Registry',
    )
    register.add_argument(
        '--runtime',
        choices=['python3.6', 'python3.7'],
        default='python3.7',
        help='Python runtime to use for the given function (default: python3.7)',
    )
    register.add_argument(
        '-k',
        '--key',
        type=str,
        required=True,
        help='Key under which function should be registered against function registry',
    )
    register.add_argument(
        '-c',
        '--code',
        type=read_string_from_file,
        required=True,
        help='Path to file containing the function code',
    )
    register.add_argument(
        '--handler',
        type=str,
        required=True,
        help='Python specification of handler',
    )
    register.add_argument(
        '--requirements',
        type=read_string_from_file,
        default='',
        help='Path to file specifying requirements for the function (optional)',
    )
    register.add_argument(
        '--iam-policy',
        type=str,
        default=LambdaBasicExecutionRolePolicy,
        help=(
            'IAM policy that should be granted to an AWS Lambda running the given function '
            '(default: allows Lambda to log usage in CloudWatch)'
        ),
    )
    register.add_argument(
        '--overwrite',
        action='store_true',
        help='If a function has already been registered under the given key, overwrite it',
    )
    register.set_defaults(func=handlers.register)

    create_role = subparsers.add_parser(
        'create_role',
        help=(
            'Create IAM role to be assumed by AWS Lambda deployment of function from Simiotics '
            'Function Registry'
        )
    )
    create_role.add_argument(
        '-k',
        '--key',
        type=str,
        required=True,
        help='Key of function in Simiotics Function Registry for which to create IAM role',
    )
    create_role.add_argument(
        '-n',
        '--name',
        type=str,
        help='Name for IAM role',
    )
    create_role.set_defaults(func=handlers.create_role)

    return parser

def main() -> None:
    """
    Runs the lambada tool

    Args: None

    Returns: None
    """

    if os.environ.get('SIMIOTICS_FUNCTION_REGISTRY') is None:
        raise ValueError('SIMIOTICS_FUNCTION_REGISTRY environment variable undefined')

    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
