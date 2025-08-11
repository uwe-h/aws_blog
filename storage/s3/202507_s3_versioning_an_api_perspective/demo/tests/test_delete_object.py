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
def cleanup_delete_object_prefix(s3_client, bucket_name):
    paginator = s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name, Prefix='delete_object/'):
        for obj in page.get('Versions', []):
            s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'], VersionId=obj['VersionId'])
        for marker in page.get('DeleteMarkers', []):
            s3_client.delete_object(Bucket=bucket_name, Key=marker['Key'], VersionId=marker['VersionId'])


def test_delete_object_version_agnostic(s3_client, bucket_name):
    key = "delete_object/agnostic"
    put_res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    del_res = s3_client.delete_object(Bucket=bucket_name, Key=key)

    assert "VersionId" in del_res
    assert "DeleteMarker" in del_res

    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        assert False, "Expected 404 error"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "404"


def test_delete_object_version_specific(s3_client, bucket_name):
    key = "delete_object/specific"
    put_res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")
    del_res = s3_client.delete_object(Bucket=bucket_name, Key=key, VersionId=put_res["VersionId"])

    assert del_res["VersionId"] == put_res["VersionId"]
    assert "DeleteMarker" not in del_res

    try:
        s3_client.head_object(Bucket=bucket_name, Key=key, VersionId=put_res["VersionId"])
        # Physically gone
        assert False, "Expected 404 error"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "404"

def test_delete_object_consecutive_delete_markers(s3_client, bucket_name):
    """Test that deleting an object twice creates two consecutive delete markers"""
    key = "delete_object/consecutive_markers"

    # Create object
    put_res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"content")

    # First delete - creates first delete marker
    del_res1 = s3_client.delete_object(Bucket=bucket_name, Key=key)
    assert "DeleteMarker" in del_res1

    # Second delete - creates second delete marker
    del_res2 = s3_client.delete_object(Bucket=bucket_name, Key=key)
    assert "DeleteMarker" in del_res2
    assert del_res1["VersionId"] != del_res2["VersionId"]  # Different version IDs

    # Verify we have two delete markers and one object version
    response = s3_client.list_object_versions(Bucket=bucket_name, Prefix="delete_object/consecutive_markers")
    delete_markers = response.get("DeleteMarkers", [])
    versions = response.get("Versions", [])

    assert len(delete_markers) == 2, f"Expected 2 delete markers, got {len(delete_markers)}"
    assert len(versions) == 1, f"Expected 1 object version, got {len(versions)}"

    # Verify the version IDs match
    marker_version_ids = {marker["VersionId"] for marker in delete_markers}
    assert del_res1["VersionId"] in marker_version_ids
    assert del_res2["VersionId"] in marker_version_ids
    assert versions[0]["VersionId"] == put_res["VersionId"]

