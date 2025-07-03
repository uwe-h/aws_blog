import pytest
import boto3
from botocore.exceptions import ClientError


@pytest.fixture
def bucket_name():
    # Retrieve CloudFormation Output with export name 'S3VersioningBucket12567'
    cf_client = boto3.client("cloudformation")
    response = cf_client.list_exports()
    for export in response["Exports"]:
        if export["Name"] == "S3VersioningBucket12567":
            return export["Value"]

    raise ValueError("export with name S3VersioningBucket12567 not found")

@pytest.fixture
def s3_client():
    client = boto3.client("s3")
    yield client

@pytest.fixture(autouse=True)
def cleanup_get_object_prefix(s3_client, bucket_name):
    yield  # Run test first
    # Cleanup after test
    paginator = s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name, Prefix='get_object/'):
        for obj in page.get('Versions', []):
            s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'], VersionId=obj['VersionId'])
        for marker in page.get('DeleteMarkers', []):
            s3_client.delete_object(Bucket=bucket_name, Key=marker['Key'], VersionId=marker['VersionId'])


def test_get_object_version_agnostic(s3_client, bucket_name):
    key = "get_object/agnostic"
    try:
        s3_client.get_object(Bucket=bucket_name, Key=key)
        assert False, "Expected 404 error"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "NoSuchKey"
    
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert response["Body"].read() == b"content"
    
    s3_client.delete_object(Bucket=bucket_name, Key=key)
    try:
        s3_client.get_object(Bucket=bucket_name, Key=key)
        assert False, "Expected NoSuchKey error"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "NoSuchKey"

def test_get_object_version_specific(s3_client, bucket_name):
    key = "get_object/specific"
    res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    response = s3_client.get_object(Bucket=bucket_name, Key=key, VersionId=res["VersionId"])
    assert response["Body"].read() == b"content"
    
    del_res = s3_client.delete_object(Bucket=bucket_name, Key=key)
    
    # get_object without version ID on deleted object returns NoSuchKey
    try:
        s3_client.get_object(Bucket=bucket_name, Key=key)
        assert False, "Expected NoSuchKey error"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "NoSuchKey"
    
    # get_object with delete marker version ID raises MethodNotAllowed because delete marker is no object
    try:
        s3_client.get_object(Bucket=bucket_name, Key=key, VersionId=del_res["VersionId"])
        assert False, "Expected MethodNotAllowed error"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "MethodNotAllowed"