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


def test_head_object_version_agnostic_success(s3_client, bucket_name):
    """Test successful head_object without version ID"""
    key = "head_object/agnostic_success"
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    response = s3_client.head_object(Bucket=bucket_name, Key=key)
    assert "ContentLength" in response
    assert "LastModified" in response

def test_head_object_version_agnostic_not_found(s3_client, bucket_name):
    """Test head_object returns 404 when object doesn't exist"""
    key = "head_object/nonexistent"
    with pytest.raises(ClientError) as exc_info:
        s3_client.head_object(Bucket=bucket_name, Key=key)
    assert exc_info.value.response["Error"]["Code"] == "404"

def test_head_object_version_agnostic_after_delete(s3_client, bucket_name):
    """Test head_object returns 404 after object is deleted (delete marker created)"""
    key = "head_object/deleted"
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    s3_client.delete_object(Bucket=bucket_name, Key=key)
    with pytest.raises(ClientError) as exc_info:
        s3_client.head_object(Bucket=bucket_name, Key=key)
    assert exc_info.value.response["Error"]["Code"] == "404"

def test_head_object_version_specific_success(s3_client, bucket_name):
    """Test successful head_object with specific version ID"""
    key = "head_object/specific_success"
    res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    response = s3_client.head_object(Bucket=bucket_name, Key=key, VersionId=res["VersionId"])
    assert "ContentLength" in response
    assert "VersionId" in response

def test_head_object_version_specific_delete_marker_has_no_metadata(s3_client, bucket_name):
    """Test head_object with delete marker version ID returns 405 MethodNotAllowed"""
    key = "head_object/delete_marker"
    s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    del_res = s3_client.delete_object(Bucket=bucket_name, Key=key)

    with pytest.raises(ClientError) as exc_info:
        s3_client.head_object(Bucket=bucket_name, Key=key, VersionId=del_res["VersionId"])
    assert exc_info.value.response["Error"]["Code"] == "405"

def test_head_object_version_specific_wrong_no_such_key(s3_client, bucket_name):
    """Test head_object with version ID from not existing key returns 404"""
    key1 = "head_object/key1"
    key2 = "head_object/key2"
    res1 = s3_client.put_object(Bucket=bucket_name, Key=key1, Body=b"content")

    with pytest.raises(ClientError) as exc_info:
        s3_client.head_object(Bucket=bucket_name, Key=key2, VersionId=res1["VersionId"])
    assert exc_info.value.response["Error"]["Code"] == "404"
