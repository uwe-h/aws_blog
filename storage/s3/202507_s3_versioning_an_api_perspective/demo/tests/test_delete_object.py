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

    # we delete version marker again
    s3_client.delete_object(Bucket=bucket_name, Key=key, VersionId=del_res["VersionId"])
    hres = s3_client.head_object(Bucket=bucket_name, Key=key)
    assert hres["VersionId"] == put_res["VersionId"]

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

