import pytest
import boto3


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
def cleanup_list_versions_prefix(s3_client, bucket_name):
    yield  # Run test first
    # Cleanup after test
    paginator = s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name, Prefix='list_versions/'):
        for obj in page.get('Versions', []):
            s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'], VersionId=obj['VersionId'])
        for marker in page.get('DeleteMarkers', []):
            s3_client.delete_object(Bucket=bucket_name, Key=marker['Key'], VersionId=marker['VersionId'])


def test_list_object_versions_prefix(s3_client, bucket_name):
    # Create objects with different prefixes
    s3_client.put_object(Bucket=bucket_name, Key="list_versions/file1.txt", Body=b"content1")
    s3_client.put_object(Bucket=bucket_name, Key="list_versions/file2.txt", Body=b"content2")
    s3_client.put_object(Bucket=bucket_name, Key="other_prefix/file3.txt", Body=b"content3")

    # Prefix filters results
    response = s3_client.list_object_versions(Bucket=bucket_name, Prefix="list_versions/")
    assert len(response["Versions"]) == 2

    # No prefix returns all objects
    response = s3_client.list_object_versions(Bucket=bucket_name)
    assert len(response["Versions"]) >= 3

def test_list_object_versions_max_keys(s3_client, bucket_name):
    # Create multiple versions
    for i in range(5):
        s3_client.put_object(Bucket=bucket_name, Key=f"list_versions/file{i}.txt", Body=f"content{i}".encode())

    # MaxKeys limits results
    response = s3_client.list_object_versions(Bucket=bucket_name, Prefix="list_versions/", MaxKeys=3)
    assert len(response["Versions"]) == 3
    assert response["IsTruncated"] == True
    assert "NextKeyMarker" in response

def test_list_object_versions_key_version_markers(s3_client, bucket_name):
    # Create multiple objects and versions
    s3_client.put_object(Bucket=bucket_name, Key="list_versions/a.txt", Body=b"v1")
    s3_client.put_object(Bucket=bucket_name, Key="list_versions/a.txt", Body=b"v2")
    s3_client.put_object(Bucket=bucket_name, Key="list_versions/b.txt", Body=b"v1")
    s3_client.delete_object(Bucket=bucket_name, Key="list_versions/b.txt")

    # Get first page with MaxKeys=2
    response = s3_client.list_object_versions(Bucket=bucket_name, Prefix="list_versions/", MaxKeys=2)
    assert len(response["Versions"]) + len(response.get("DeleteMarkers", [])) == 2

    # Use markers for pagination
    next_response = s3_client.list_object_versions(
        Bucket=bucket_name,
        Prefix="list_versions/",
        KeyMarker=response["NextKeyMarker"],
        VersionIdMarker=response.get("NextVersionIdMarker", "")
    )
    assert len(next_response["Versions"]) + len(next_response.get("DeleteMarkers", [])) >= 1

def test_list_object_versions_combined_parameters(s3_client, bucket_name):
    # Create test data
    s3_client.put_object(Bucket=bucket_name, Key="list_versions/test1.txt", Body=b"content")
    s3_client.put_object(Bucket=bucket_name, Key="list_versions/test2.txt", Body=b"content")
    s3_client.delete_object(Bucket=bucket_name, Key="list_versions/test1.txt")

    # Combine prefix, MaxKeys, and markers
    response = s3_client.list_object_versions(
        Bucket=bucket_name,
        Prefix="list_versions/",
        MaxKeys=1
    )

    assert len(response.get("Versions", [])) + len(response.get("DeleteMarkers", [])) == 1
    assert response["IsTruncated"] == True

def test_list_object_versions_version_id_marker_pagination(s3_client, bucket_name):
    """Test that VersionIdMarker returns the first version after the specified version ID marker"""
    key = "list_versions/version_marker_test.txt"
    
    # Create multiple versions of the same object
    version_ids = []
    for i in range(4):
        res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=f"content{i}".encode())
        version_ids.append(res["VersionId"])
    
    # Get all versions first to understand the order (newest first)
    all_versions = s3_client.list_object_versions(Bucket=bucket_name, Prefix="list_versions/version_marker_test.txt")
    all_version_ids = [v["VersionId"] for v in all_versions["Versions"]]
    
    # Use the second version ID as marker (should return versions after it)
    marker_version_id = all_version_ids[1]  # Second newest version
    
    # List versions starting after the marker
    response = s3_client.list_object_versions(
        Bucket=bucket_name,
        Prefix="list_versions/version_marker_test.txt",
        KeyMarker=key,
        VersionIdMarker=marker_version_id
    )
    
    # Should return versions that come after the marker in the listing order
    returned_version_ids = [v["VersionId"] for v in response.get("Versions", [])]
    
    # The marker version should not be included in results
    assert marker_version_id not in returned_version_ids
    
    # Should return the versions that come after the marker in chronological order
    expected_versions_after_marker = all_version_ids[2:]  # Versions after the marker
    assert len(returned_version_ids) == len(expected_versions_after_marker)
    
    # Verify the returned versions are the ones that come after the marker
    for returned_id in returned_version_ids:
        assert returned_id in expected_versions_after_marker