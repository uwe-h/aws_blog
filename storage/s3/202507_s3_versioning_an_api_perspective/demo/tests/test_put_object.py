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
def cleanup_put_object_prefix(s3_client, bucket_name):
    paginator = s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name, Prefix='put_object/'):
        for obj in page.get('Versions', []):
            s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'], VersionId=obj['VersionId'])
        for marker in page.get('DeleteMarkers', []):
            s3_client.delete_object(Bucket=bucket_name, Key=marker['Key'], VersionId=marker['VersionId'])


def test_put_object_version_agnostic(s3_client, bucket_name):
    key = "put_object/agnostic"
    res = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"v1")
    assert "VersionId" in res
    hres = s3_client.head_object(Bucket=bucket_name, Key=key)
    assert res["VersionId"] == hres["VersionId"]
    res2 = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"v2")
    assert res["VersionId"] != res2["VersionId"] # // We have overwritten version of res1
    gres = s3_client.get_object(Bucket=bucket_name, Key=key)
    assert gres["Body"].read() == b"v2" # // We have overwritten version of res1
    gresv1 = s3_client.get_object(Bucket=bucket_name, Key=key, VersionId=res["VersionId"])
    assert gresv1["Body"].read() == b"v1" # // We have overwritten version of res1

def test_put_object_version_specific(s3_client, bucket_name):
    key = "put_object/specific"
    res1 = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"v1")
    res2 = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"v2")
    # TODO Not possible check object locks in detail res2 = s3_client.put_object(Bucket=bucket_name, Key=key, Body=b"v2", VersionId=res1["VersionId"])

    assert res1["VersionId"] != res2["VersionId"]
    gres = s3_client.get_object(Bucket=bucket_name, Key=key, VersionId=res1["VersionId"])
    assert gres["Body"].read() == b"v1" # // We have overwritten version of res1
