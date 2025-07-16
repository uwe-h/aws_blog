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
def cleanup_list_objects_prefix(s3_client, bucket_name):
    yield  # Run test first
    # Cleanup after test
    paginator = s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name, Prefix='list_objects/'):
        for obj in page.get('Versions', []):
            s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'], VersionId=obj['VersionId'])
        for marker in page.get('DeleteMarkers', []):
            s3_client.delete_object(Bucket=bucket_name, Key=marker['Key'], VersionId=marker['VersionId'])


def test_list_objects_version_agnostic(s3_client, bucket_name):
    prefix = "list_objects/"
    key = "list_objects/agnostic"

    # Empty prefix returns no objects
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    assert response.get("Contents", []) == []

    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    assert len(response["Contents"]) == 1
    assert response["Contents"][0]["Key"] == key

    s3_client.delete_object(Bucket=bucket_name, Key=key)
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    assert response.get("Contents", []) == []

def test_list_objects_hides_deleted_objects(s3_client, bucket_name):
    """Test that list_objects_v2 hides objects whose latest version is a delete marker"""
    prefix = "list_objects/"
    key = "list_objects/deleted"

    # Create object
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    assert len(response["Contents"]) == 1
    assert response["Contents"][0]["Key"] == key

    # Delete object (creates delete marker)
    s3_client.delete_object(Bucket=bucket_name, Key=key)
    
    # list_objects_v2 doesn't show objects with delete markers as latest version
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    assert response.get("Contents", []) == []
