import pytest
import boto3
import logging
import time
import uuid
from direct_api_client import S3DirectAPIClient


@pytest.fixture
def bucket_name():
    # Retrieve CloudFormation Output with export name 'S3VersioningBucket12567'
    cf_client = boto3.client("cloudformation")
    response = cf_client.list_exports()
    for export in response["Exports"]:
        if export["Name"] == "S3VersioningBucket12561":
            return export["Value"]

    raise ValueError("export with name S3VersioningBucket12561 not found")


@pytest.fixture
def s3_client():
    client = boto3.client("s3")
    yield client


@pytest.fixture
def direct_client():
    import os
    client = S3DirectAPIClient(
        access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region=os.environ.get('AWS_REGION', 'eu-central-1')
    )
    yield client
    


@pytest.fixture
def test_key():
    return f"test-ordering/{uuid.uuid4()}"


#@pytest.fixture(autouse=True)
def cleanup_test_objects(s3_client, bucket_name, test_key):
    yield  # Run test first
    
    # Clean up all versions
    versions_paginator = s3_client.get_paginator('list_object_versions')
    for page in versions_paginator.paginate(Bucket=bucket_name, Prefix=test_key):
        delete_objects = []
        
        if 'Versions' in page:
            for version in page['Versions']:
                delete_objects.append({
                    'Key': version['Key'],
                    'VersionId': version['VersionId']
                })
        
        if 'DeleteMarkers' in page:
            for marker in page['DeleteMarkers']:
                delete_objects.append({
                    'Key': marker['Key'],
                    'VersionId': marker['VersionId']
                })
        
        if delete_objects:
            s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': delete_objects}
            )


def create_alternating_versions(s3_client, bucket_name, test_key, count=5):
    """Create alternating versions and delete markers"""
    expected_order = []

    for i in range(count):
        # Create object version
        content = f"content-{i}".encode()
        put_response = s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=content
        )
        version_id = put_response['VersionId']
        expected_order.append({
            'type': 'Version',
            'VersionId': version_id
        })

        # Small delay to ensure different timestamps
        time.sleep(0.1)

        # Create delete marker
        delete_response = s3_client.delete_object(
            Bucket=bucket_name,
            Key=test_key
        )
        delete_marker_id = delete_response['VersionId']
        expected_order.append({
            'type': 'DeleteMarker',
            'VersionId': delete_marker_id
        })

        # Small delay to ensure different timestamps
        time.sleep(0.1)

    return expected_order

#@pytest.mark.skip(reason="Not implemented yet")
def test_api_preserves_version_order(s3_client, direct_client, bucket_name, test_key):
    """Test that direct API client preserves the correct version order"""
    # Create alternating versions and delete markers
    expected_order = create_alternating_versions(s3_client, bucket_name, test_key)

    # Get versions using direct API client
    api_response = direct_client.list_object_versions(
        bucket=bucket_name,
        prefix=test_key
    )

    # Extract API versions
    api_versions = []
    for item in api_response['VersionStack']:
        api_versions.append({
            'type': 'DeleteMarker' if item['IsDeleteMarker'] else 'Version',
            'VersionId': item['VersionId']
        })

    # Verify API order matches expected order (newest first)
    api_version_ids = [item['VersionId'] for item in api_versions]
    expected_version_ids = [item['VersionId'] for item in reversed(expected_order)]

    assert api_version_ids == expected_version_ids, "Direct API client does not preserve correct version order"


def test_sdk_vs_api_ordering(s3_client, bucket_name, test_key):
    """Test to compare SDK and API ordering"""
    # Create alternating versions and delete markers
    expected_order = create_alternating_versions(s3_client, bucket_name, test_key)
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)
    # Get versions using SDK
    sdk_response = s3_client.list_object_versions(
        Bucket=bucket_name,
        Prefix=test_key
    )

    # Get versions using direct API client
   # api_response = direct_client.list_object_versions(
    #    bucket=bucket_name,
     #   prefix=test_key
    #)

    # Extract SDK versions and delete markers
    sdk_versions = []
    for version in sdk_response.get('Versions', []):
        sdk_versions.append({
            'type': 'Version',
            'VersionId': version['VersionId'],
            'LastModified': version['LastModified'].isoformat()
        })

    for marker in sdk_response.get('DeleteMarkers', []):
        sdk_versions.append({
            'type': 'DeleteMarker',
            'VersionId': marker['VersionId'],
            'LastModified': marker['LastModified'].isoformat()
        })

    # Create LastModified occurrence dictionary
    last_modified_counts = {}
    for version in sdk_versions:
        timestamp = version['LastModified']
        last_modified_counts[timestamp] = last_modified_counts.get(timestamp, 0) + 1
    
    # Check for duplicate timestamps
    duplicates = {ts: count for ts, count in last_modified_counts.items() if count > 1}
    
    print(f"\nDEBUG: LastModified timestamp analysis:")
    print(f"Total versions: {len(sdk_versions)}")
    print(f"Unique timestamps: {len(last_modified_counts)}")
    print(f"Duplicate timestamps: {len(duplicates)}")
    
    if duplicates:
        print(f"Timestamps with duplicates:")
        for ts, count in duplicates.items():
            print(f"  {ts}: {count} occurrences")
            # Show which versions have this timestamp
            versions_with_ts = [v for v in sdk_versions if v['LastModified'] == ts]
            for v in versions_with_ts:
                print(f"    - {v['type']}: {v['VersionId']}")
    
    # Sort SDK versions by LastModified (newest first)
    sdk_versions.sort(key=lambda x: x['LastModified'], reverse=True)
    
    # Verify ordering
    sdk_version_ids = [item['VersionId'] for item in sdk_versions]
    expected_version_ids = [item['VersionId'] for item in reversed(expected_order)]
    
    # Validate that we have at least one duplicate timestamp (proving the ordering issue)
    assert len(duplicates) > 0, "Expected duplicate LastModified timestamps to demonstrate ordering issues"
    
    # Check if SDK sorting fails due to duplicate timestamps
    assert sdk_version_ids != expected_version_ids, "SDK sorting should fail due to duplicate timestamps"
    assert False