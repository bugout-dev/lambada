"""
Simple lambda which registers data against a Simiotics Data Registry
"""

from io import BytesIO
import tempfile
from typing import Dict

import boto3
from PIL import ExifTags, Image

def exif_tags(bucket: str, image_key: str) -> Dict[str, str]:
    """
    Returns the EXIF tags associated with an image on S3
    """
    # Read file directly from S3 get_object bytes stream as per the StackOverflow answer here:
    # https://stackoverflow.com/a/55732616
    s3_client = boto3.client('s3')
    s3_response = s3_client.get_object(Bucket=bucket, Key=image_key)
    image_body = s3_response.get('Body')
    if image_body is None:
        raise ValueError('S3 GetObject response had no Body')
    image_bytes = image_body.read()

    try:
        image = Image.open(BytesIO(image_bytes))
    except IOError as open_error:
        raise IOError(
            'Worker could not load image at path - s3://{}/{}. Error: {}'.format(
                bucket,
                image_key,
                open_error,
            )
        )

    # EXIF tag extraction is adapted from this StackOverflow answer:
    # https://stackoverflow.com/a/56571871
    exif_tags = image.getexif()
    exif_dict = {}
    if exif_tags is not None:
        raw_exif_dict = dict(exif_tags)
        for key, value in raw_exif_dict.items():
            if key in ExifTags.TAGS:
                exif_dict[ExifTags.TAGS[key]] = repr(value)

    return exif_dict

def manual_trigger(event, context):
    """
    Assumes that the event object has exactly two keys: 'bucket' and 'image_key'. These are unpacked
    using `**` into the exif_targets function directly.
    """
    return exif_tags(**event)

def s3_trigger(event, context):
    """
    Triggers the EXIF Tagger with an S3 event. The assumption is that the event argument is
    structured as per:
    https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html
    """
    records = event.get('Records', [])
    arguments = [
        (
            record.get('s3', {}).get('bucket', {}).get('name'),
            record.get('s3', {}).get('object', {}).get('key'),
        )
        for record in records
    ]
    tags = [
        exif_tags(bucket, image_key) for bucket, image_key in arguments
        if bucket is not None and image_key is not None
    ]
    return tags

if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Display EXIF data for image on S3')
    parser.add_argument(
        '-b',
        '--bucket',
        type=str,
        required=True,
        help='Name of S3 bucket containing the image'
    )
    parser.add_argument(
        '-k',
        '--key',
        type=str,
        required=True,
        help='Image key within the S3 bucket'
    )

    args = parser.parse_args()

    exif_info = exif_tags(args.bucket, args.key)
    print(json.dumps(exif_info))
