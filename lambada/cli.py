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
    description = """
lambada: Manage AWS Lambdas using Simiotics Function Registries
\n
Note: This tool uses the SIMIOTICS_FUNCTION_REGISTRY environment variable to determine the Function
Registry to communicate with. If the variable is not set, it will error out. You can use the public
Simiotics Function Registry by running:
```
$ export SIMIOTICS_FUNCTION_REGISTRY=registry-alpha.simiotics.com:7011
```
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(title='Commands')

    register = subparsers.add_parser(
        'register',
        help='Register a lambada function against a Simiotics Function Registry and print its key',
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
        '--timeout',
        type=int,
        default=3,
        help='Timeout for execution of Lambda in seconds (default: 3)',
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
            'Function Registry and print its name'
        )
    )
    create_role.add_argument(
        '-k',
        '--key', type=str,
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

    deploy = subparsers.add_parser(
        'deploy',
        help='Deploy a Simiotics Function as an AWS Lambda and print its AWS Lambda ARN',
    )
    deploy.add_argument(
        '-n',
        '--name',
        type=str,
        default=None,
        help='Name of the AWS Lambda to deploy',
    )
    deploy.add_argument(
        '-k',
        '--key',
        type=str,
        required=True,
        help='Key for function in Simiotics Function Registry',
    )
    deploy.add_argument(
        '--keep-staging-dir',
        action='store_true',
        help='If set, keeps the deployment package temporary directory. Path is printed to stderr.'
    )
    deploy.set_defaults(func=handlers.deploy)

    down = subparsers.add_parser(
        'down',
        help='Take down an AWS Lambda deployed via lambada',
    )
    down.add_argument(
        '-k',
        '--key',
        type=str,
        required=True,
        help='Key for function in Simiotics Function Registry',
    )
    down.add_argument(
        '--teardown',
        action='store_true',
        help='All AWS resources associated with the Simiotics function should be removed'
    )
    down.set_defaults(func=handlers.down)

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
