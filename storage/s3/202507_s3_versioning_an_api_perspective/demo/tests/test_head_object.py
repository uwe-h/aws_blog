import pytest
import boto3
from botocore.exceptions import ClientError


@pytest.fixture
def bucket_name():
    # Retrieve CloudFormation Output with export name 'S3VersioningBucket12567'
    cf_client = boto3.client("cloudformation")
    response = cf_client.list_exports()
    for export in response["Exports"]:
        print(f"export name {export['Name']}")
        if export["Name"] == "S3VersioningBucket12567":
            return export["Value"]

    raise ValueError("export with name S3VersioningBucket12567 not found")

@pytest.fixture
def s3_client():
    client = boto3.client("s3")
    yield client

@pytest.fixture(autouse=True)
def cleanup_head_object_prefix(s3_client, bucket_name):
    yield  # Run test first
    # Cleanup after test
    paginator = s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name, Prefix='head_object/'):
        for obj in page.get('Versions', []):
            s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'], VersionId=obj['VersionId'])
        for marker in page.get('DeleteMarkers', []):
            s3_client.delete_object(Bucket=bucket_name, Key=marker['Key'], VersionId=marker['VersionId'])


def test_head_object_version_agnostic(s3_client, bucket_name):
    key = "head_object/agnostic"
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        assert False, "Expected an error, but none was raised"  # Fail the test if no error is raised
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            # The object does not exist, so we can proceed with the test
            pass
        else:
            assert False, f"Unexpected error: {e}"  # Fail the test if it's not a 404 error
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    s3_client.head_object(Bucket=bucket_name, Key=key)
    s3_client.delete_object(Bucket=bucket_name, Key=key)
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        assert False, "Expected an error, but none was raised"  # Fail the test if no error is raised
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            # The object does not exist, so we can proceed with the test
            pass
        else:
            assert False, f"Unexpected error: {e}"  # Fail the test if it's not a 404 error    

def test_head_object_version_specific(s3_client, bucket_name):
    key = "head_object/specific"
    res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    s3_client.head_object(Bucket=bucket_name, Key=key, VersionId=res["VersionId"])
    del_res = s3_client.delete_object(Bucket=bucket_name, Key=key)
    
    # head_object without version ID on deleted object returns 404
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        assert False, "Expected 404 error"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "404"

    # head_object with delete marker version ID raises MethodNotAllowed, because delete marker can have no meta data
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key, VersionId=del_res["VersionId"])
        assert False, "Expected MethodNotAllowed error"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "405"
