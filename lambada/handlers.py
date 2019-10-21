"""
Handlers for lambada commands
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

from typing import Dict

import boto3
from simiotics.client import client_from_env

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

LambadaManagerKey = 'manager'
LambadaManager = 'lambada'

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
        'timeout': str(args.timeout),
        'env': args.env,
        LambadaManagerKey: LambadaManager,
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
    simiotics = client_from_env()
    registered_function = simiotics.get_registered_function(args.key)
    if registered_function.tags.get(LambadaManagerKey) != LambadaManager:
        raise ValueError('Simiotics function with key={} not managed by lambada'.format(args.key))

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
    role_arn = response['Role']['Arn']

    iam_policy = registered_function.tags['iam_policy']
    policy_name = 'lambada_policy_{}'.format(role_name)
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName=policy_name,
        PolicyDocument=iam_policy,
    )

    tags = registered_function.tags
    tags['iam_role_name'] = role_name
    tags['iam_role_arn'] = role_arn
    tags['iam_role_policy'] = policy_name
    simiotics.register_function(
        key=registered_function.key,
        code=registered_function.code,
        tags=tags,
        overwrite=True,
    )

    print(role_name)

def deploy(args: argparse.Namespace) -> None:
    """
    Handler for `lambada deploy`, which creates an AWS Lambda from a Simiotics function

    Args:
    args
        `argparse.Namespace` object containing parameters to the `deploy` command

    Returns: None, prints AWS Lambda ARN
    """
    simiotics = client_from_env()
    registered_function = simiotics.get_registered_function(args.key)
    if registered_function.tags.get(LambadaManagerKey) != LambadaManager:
        raise ValueError('Simiotics function with key={} not managed by lambada'.format(args.key))

    environment_variables: Dict[str, str] = json.loads(registered_function.tags.get('env', '{}'))

    staging_dir = tempfile.mkdtemp()
    try:
        deployment_package_dir = os.path.join(staging_dir, 'deployment_package')
        os.mkdir(deployment_package_dir)
        requirements_txt = os.path.join(staging_dir, 'requirements.txt')
        code_py = os.path.join(deployment_package_dir, 'code.py')

        with open(requirements_txt, 'w') as ofp:
            ofp.write(registered_function.tags['requirements'])

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                requirements_txt,
                "--target",
                deployment_package_dir
            ],
            check=True,
        )
        if os.path.exists(code_py):
            raise ValueError('File already exists at path: {}'.format(code_py))

        with open(code_py, 'w') as ofp:
            ofp.write(registered_function.code)

        zipfilepath = os.path.join(staging_dir, 'function.zip')
        shutil.make_archive(os.path.splitext(zipfilepath)[0], 'zip', deployment_package_dir)
        with open(zipfilepath, 'rb') as ifp:
            deployment_package = ifp.read()

        lambda_client = boto3.client('lambda')
        handler_path = 'code.{}'.format(registered_function.tags['handler'])
        lambda_resource = lambda_client.create_function(
            FunctionName=args.name,
            Runtime=registered_function.tags['runtime'],
            Role=registered_function.tags['iam_role_arn'],
            Handler=handler_path,
            Code={'ZipFile': deployment_package},
            Environment={
                'Variables': environment_variables,
            },
            Description='Simiotics lambada deployment of: {}'.format(args.key),
            Timeout=int(registered_function.tags['timeout']),
            Tags={
                'Creator': 'simiotics',
            },
        )

        lambda_arn = lambda_resource['FunctionArn']

        registered_function.tags['lambda_arn'] = lambda_arn
        simiotics.register_function(
            key=registered_function.key,
            code=registered_function.code,
            tags=registered_function.tags,
            overwrite=True,
        )
        print(lambda_arn)
    finally:
        if not args.keep_staging_dir:
            shutil.rmtree(staging_dir)
        else:
            print(staging_dir, file=sys.stderr)

def down(args: argparse.Namespace) -> None:
    """
    Handler for `lambada down`, which takes down an AWS Lambda from a Simiotics function

    Args:
    args
        `argparse.Namespace` object containing parameters to the `down` command

    Returns: None, prints Simiotics Function Registry key
    """
    simiotics = client_from_env()
    registered_function = simiotics.get_registered_function(args.key)
    if registered_function.tags.get(LambadaManagerKey) != LambadaManager:
        raise ValueError('Simiotics function with key={} not managed by lambada'.format(args.key))

    try:
        lambda_arn = registered_function.tags.get('lambda_arn')
        if lambda_arn is not None:
            lambda_client = boto3.client('lambda')
            lambda_client.delete_function(FunctionName=lambda_arn)
            registered_function.tags.pop('lambda_arn')

        if args.teardown:
            iam_client = boto3.client('iam')
            role_name = registered_function.tags.get('iam_role_name')
            if role_name is not None:
                policy_name = registered_function.tags.get('iam_role_policy')
                if policy_name is not None:
                    iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
                    registered_function.tags.pop('iam_role_policy')

                iam_client.delete_role(RoleName=role_name)
                registered_function.tags.pop('iam_role_name')
                registered_function.tags.pop('iam_role_arn')
    finally:
        simiotics.register_function(
            key=registered_function.key,
            code=registered_function.code,
            tags=registered_function.tags,
            overwrite=True,
        )

    print(args.key)

def list_functions(args: argparse.Namespace) -> None:
    """
    Handler for `lambada list`, which lists all the functions in a Simiotics Function Registry which
    are managed by lambada. The function registry for which functions are listed is the one
    specified by the SIMIOTICS_FUNCTION_REGISTRY environment variable.

    Args:
    args
        `argparse.Namespace` object containing parameters to the `list` command

    Returns: None, prints lambada-managed functions in the Simiotics Function Registry line by line
    """
    simiotics = client_from_env()

    proceed = True
    current_offset = 0
    while proceed:
        registered_functions = simiotics.list_registered_functions(current_offset, args.num_items)
        for registered_function in registered_functions:
            if registered_function.tags.get(LambadaManagerKey) == LambadaManager:
                print(registered_function.key)

        if len(registered_functions) < args.num_items:
            proceed = False

        current_offset += len(registered_functions)
