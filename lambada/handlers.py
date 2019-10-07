"""
Handlers for lambada commands
"""

import argparse

import boto3
from simiotics.client import client_from_env, Simiotics

AWSLambdaTrustedEntity = """
{
    "Version": "2012-10-17",
    "Statement": [
        {
        "Sid": "",
        "Effect": "Allow",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
        }
    ]
}
""".strip()

SimioticsPath = '/simiotics/'

def register(args: argparse.Namespace) -> None:
    """
    Handler for `lambada register`, which registers a new lambada function against a simiotics
    registry

    Args:
    args
        `argparse.Namespace` object containing parameters to the `register` command

    Returns: None, prints key of registered function
    """
    simiotics = client_from_env()

    tags = {
        'runtime': args.runtime,
        'handler': args.handler,
        'requirements': args.requirements,
        'iam_policy': args.iam_policy,
    }

    simiotics.register_function(args.key, args.code, tags, args.overwrite)

    print(args.key)

def create_role(args: argparse.Namespace) -> None:
    """
    Handler for `lambada create_role`, which creates an AWS IAM role that an AWS Lambda implementing
    the specified Simiotics Function Registry function can use in its execution

    Args:
    args
        `argparse.Namespace` object containing parameters to the `create_role` command

    Returns: None, prints IAM role name
    """
    iam_client = boto3.client('iam')

    response = iam_client.create_role(
        Path=SimioticsPath,
        RoleName=args.name,
        AssumeRolePolicyDocument=AWSLambdaTrustedEntity,
        Description='AWS Lambda execution role for Simiotics function: {}'.format(args.key),
        Tags=[
            {'Key': 'Creator', 'Value': 'simiotics'},
        ]
    )

    role_name = response['Role']['RoleName']

    simiotics = client_from_env()
    registered_function = simiotics.get_registered_function(args.key)
    iam_policy = registered_function.tags['iam_policy']
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName='{}Policy'.format(role_name),
        PolicyDocument=iam_policy,
    )

    tags = registered_function.tags
    tags['iam_role_name'] = role_name
    simiotics.register_function(
        key=registered_function.key,
        code=registered_function.code,
        tags=tags,
        overwrite=True,
    )

    print(role_name)
