"""
Simple lambda which registers data against a Simiotics Data Registry
"""

import os
from typing import Dict, Tuple
import uuid

from simiotics.client import client_from_env, Simiotics
from simiotics.registry import data_pb2

class InvalidEnvironment(Exception):
    """
    Raised if function environment is not valid
    """

class InvalidSource(Exception):
    """
    Raised if source does not match assumptions of the registration function
    """

class RegistrationError(IOError):
    """
    Raised if datum registration failed
    """

def register_object(bucket: str, key: str, tags: Dict[str, str]) -> Tuple[str, str]:
    """
    Registers an object stored to S3 against a Simiotics Data Registry provided:
    1. The SIMIOTICS_DATA_REGISTRY environment variable is set
    2. The SIMIOTICS_DATA_SOURCE environment variable is set
    3. The SIMIOTICS_DATA_SOURCE has been registered as a source under the SIMIOTICS_DATA_REGISTRY
       as an S3 data source
    4. The source's data_access_spec is a prefix of the string `s3://{bucket}/{key}`

    The suffix of `data_access_spec` required to form `s3://{bucket}/{key}` is used as the datum ID

    Args:
    bucket
        Name of bucket containing the object that the caller wishes to register against Simiotics
        Data Registry
    key
        Key (relative to bucket root) under which object is registered on S3
    tags
        Dictionary mapping string keys to string values that represents metadata tags to be
        associated with the object being registered

    Returns: Ordered pair of the form (data source ID, datum ID) to identify the data registered in
    the Simiotics Data Registry
    """
    source_id = os.environ.get('SIMIOTICS_DATA_SOURCE')
    if source_id is None:
        raise InvalidEnvironment('SIMIOTICS_DATA_SOURCE environment variable has not been set')

    if os.environ.get('SIMIOTICS_DATA_REGISTRY') is None:
        raise InvalidEnvironment('SIMIOTICS_DATA_REGISTRY environment variable has not been set')

    simiotics_client = client_from_env()

    datum_id = str(uuid.uuid4())
    object_path = f's3://{bucket}/{key}'

    source = simiotics_client.get_data_source(source_id)
    if source.data_access_spec != object_path[:len(source.data_access_spec)]:
        raise InvalidSource(
            (
                f'Source data access specification ({source.data_access_spec}) does not match '
                f'object path ({object_path})'
            )
        )
    if source.source_type != data_pb2.Source.SOURCE_S3:
        raise InvalidSource(
            f'Source {source_id} has type {source.source_type} not {data_pb2.Source.SOURCE_S3}'
        )

    responses = list(simiotics_client.register_data([(source_id, datum_id, object_path, tags)]))
    if len(responses) != 1:
        raise RegistrationError(f'Expected single response; got {responses}')

    response = responses[0]
    if response.error:
        raise RegistrationError(response.error_message)

    return (source_id, response.datum.id)

def manual_trigger(event: Dict, context: Dict) -> Tuple[str, str]:
    """
    Manually triggered AWS Lambda handler

    Simply unpacks its event object as keyword arguments to register_object
    """
    return register_object(**event)

def s3_trigger(event: Dict, context: Dict) -> Tuple[str, str]:
    """
    Trigger for when S3 object gets created - this allows auto-registration of new S3 objects
    against a Simiotics Data Registry.

    The assumption is that the event argument is structured as per:
    https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html

    """
    records = event.get('Records', [])
    arguments = [
        (
            record.get('s3', {}).get('bucket', {}).get('name'),
            record.get('s3', {}).get('object', {}).get('key'),
            {
                'creator': 'lambada',
            },
        )
        for record in records
    ]
    responses = [
        register_object(bucket, key, tags) for bucket, key, tags in arguments
        if bucket is not None and key is not None
    ]
    return responses

if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description='Register datum against a source in a Simiotics Data Registry'
    )
    parser.add_argument(
        '-b',
        '--bucket',
        type=str,
        required=True,
        help='Name of S3 bucket containing the datum'
    )
    parser.add_argument(
        '-k',
        '--key',
        type=str,
        required=True,
        help='Datum key within the S3 bucket'
    )
    parser.add_argument(
        '-t',
        '--tags',
        type=json.loads,
        default={},
        help='JSON string representing tags (mapping string keys to string values)'
    )

    args = parser.parse_args()

    source_id, datum_id = register_object(args.bucket, args.key, args.tags)
    print(f'Registered {datum_id} under {source_id}')
