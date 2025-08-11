import pytest
import boto3
from botocore.exceptions import ClientError


@pytest.fixture
def bucket_name():
    # Retrieve CloudFormation Output with export name 'S3VersioningBucket12560'
    cf_client = boto3.client("cloudformation")
    response = cf_client.list_exports()
    for export in response["Exports"]:
        if export["Name"] == "S3VersioningBucket12560":
            return export["Value"]

    raise ValueError("export with name S3VersioningBucket12560 not found")

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
            s3_client.delete_object(
                Bucket=bucket_name,
                Key=marker['Key'],
                VersionId=marker['VersionId'])


def test_get_object_version_agnostic_success(s3_client, bucket_name):
    """Test successful get_object without version ID"""
    key = "get_object/agnostic_success"
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert response["Body"].read() == b"content"
    assert "VersionId" in response

def test_get_object_version_agnostic_not_found(s3_client, bucket_name):
    """Test get_object returns NoSuchKey when object doesn't exist"""
    key = "get_object/nonexistent"
    with pytest.raises(ClientError) as exc_info:
        s3_client.get_object(Bucket=bucket_name, Key=key)
    assert exc_info.value.response["Error"]["Code"] == "NoSuchKey"

def test_get_object_version_agnostic_after_delete(s3_client, bucket_name):
    """Test get_object returns NoSuchKey after object is deleted (delete marker created)"""
    key = "get_object/deleted"
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    s3_client.delete_object(Bucket=bucket_name, Key=key)
    with pytest.raises(ClientError) as exc_info:
        s3_client.get_object(Bucket=bucket_name, Key=key)
    assert exc_info.value.response["Error"]["Code"] == "NoSuchKey"

def test_get_object_version_specific_success(s3_client, bucket_name):
    """Test successful get_object with specific version ID"""
    key = "get_object/specific_success"
    res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    response = s3_client.get_object(Bucket=bucket_name, Key=key, VersionId=res["VersionId"])
    assert response["Body"].read() == b"content"
    assert response["VersionId"] == res["VersionId"]

def test_get_object_version_specific_delete_marker_is_not_an_object(s3_client, bucket_name):
    """
        Test get_object with delete marker version ID returns MethodNotAllowed,
        because a delete marker is not an object.
    """
    key = "get_object/delete_marker"
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    del_res = s3_client.delete_object(Bucket=bucket_name, Key=key)

    with pytest.raises(ClientError) as exc_info:
        s3_client.get_object(Bucket=bucket_name, Key=key, VersionId=del_res["VersionId"])
    assert exc_info.value.response["Error"]["Code"] == "MethodNotAllowed"

def test_get_object_version_specific_wrong_key_error(s3_client, bucket_name):
    """
        Test get_object with a valid version ID that does not exists for that object
    """
    key1 = "get_object/key1"
    key2 = "get_object/key2"
    res1 = s3_client.put_object(Bucket=bucket_name, Key=key1, Body=b"content")

    with pytest.raises(ClientError) as exc_info:
        s3_client.get_object(Bucket=bucket_name, Key=key2, VersionId=res1["VersionId"])
    assert exc_info.value.response["Error"]["Code"] == "NoSuchVersion"
