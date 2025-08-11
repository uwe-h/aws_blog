import urllib.parse
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
import hashlib
from aws_s3_sigv4_python.auth.aws4_signer_for_authorization_header import AWS4SignerForAuthorizationHeader
from aws_s3_sigv4_python.auth.aws4_signer_base import AWS4SignerBase


class S3DirectAPIClient:
    """Direct S3 API client for ListObjectVersions without SDK dependencies"""
    
    def __init__(self, access_key_id, secret_access_key, region='us-east-1'):
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        self.service = 's3'
    


    
    def list_object_versions(self, bucket, prefix=None, key_marker=None, version_id_marker=None, max_keys=None):
        """Direct API call to ListObjectVersions"""
        
        # Build query parameters in AWS expected order
        query_parts = []
        if prefix:
            query_parts.append(f'prefix={urllib.parse.quote(prefix, safe="")}')
        if key_marker:
            query_parts.append(f'key-marker={urllib.parse.quote(key_marker, safe="")}')
        if version_id_marker:
            query_parts.append(f'version-id-marker={urllib.parse.quote(version_id_marker, safe="")}')
        if max_keys:
            query_parts.append(f'max-keys={max_keys}')
        query_parts.append('encoding-type=url')
        query_parts.append('versions')  # versions parameter goes last
        
        query_string = '&'.join(query_parts)
        url = f"https://{bucket}.s3.{self.region}.amazonaws.com/?{query_string}"
        
        # Create signer and sign request
        signer = AWS4SignerForAuthorizationHeader(
            url, 'GET', 's3', self.region
        )
        
        # Build query parameters dict for signer
        query_params = {}
        if prefix:
            query_params['prefix'] = prefix
        if key_marker:
            query_params['key-marker'] = key_marker
        if version_id_marker:
            query_params['version-id-marker'] = version_id_marker
        if max_keys:
            query_params['max-keys'] = str(max_keys)
        query_params['encoding-type'] = 'url'
        query_params['versions'] = ''
        
        headers = {
            'x-amz-content-sha256': AWS4SignerBase.EMPTY_BODY_SHA256
        }
        
        authorization = signer.compute_signature(
            headers,
            query_params,
            AWS4SignerBase.EMPTY_BODY_SHA256,
            self.access_key_id,
            self.secret_access_key
        )
        
        headers['Authorization'] = authorization
        
        # Make request
        print(f"DEBUG: Making request to: {url}")
        print(f"DEBUG: Host: {bucket}.s3.{self.region}.amazonaws.com")
        print(f"DEBUG: Region: {self.region}")
        print(f"DEBUG: Access Key: {self.access_key_id[:8]}...")
        
        response = requests.get(url, headers=headers)
        
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"DEBUG: Response body: {response.text}")
            print(f"DEBUG: Request headers: {dict(response.request.headers)}")
        
        response.raise_for_status()
        
        # Parse XML response
        return self._parse_list_versions_response(response.text)
    
    def _parse_list_versions_response(self, xml_content):
        """Parse ListObjectVersions XML response with unified VersionStack preserving original order"""
        root = ET.fromstring(xml_content)
        ns = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}
        
        result = {
            'IsTruncated': root.find('s3:IsTruncated', ns).text == 'true',
            'VersionStack': []
        }
        
        # Process all children in original order
        for child in root:
            tag = child.tag.split('}')[-1]  # Remove namespace prefix
            
            if tag == 'Version':
                result['VersionStack'].append({
                    'Key': child.find('s3:Key', ns).text,
                    'VersionId': child.find('s3:VersionId', ns).text,
                    'IsDeleteMarker': False,
                    'LastModified': child.find('s3:LastModified', ns).text,
                    'IsLatest': child.find('s3:IsLatest', ns).text == 'true'
                })
            elif tag == 'DeleteMarker':
                result['VersionStack'].append({
                    'Key': child.find('s3:Key', ns).text,
                    'VersionId': child.find('s3:VersionId', ns).text,
                    'IsDeleteMarker': True,
                    'LastModified': child.find('s3:LastModified', ns).text,
                    'IsLatest': child.find('s3:IsLatest', ns).text == 'true'
                })
        
        # Add pagination markers if truncated
        if result['IsTruncated']:
            next_key = root.find('s3:NextKeyMarker', ns)
            next_version = root.find('s3:NextVersionIdMarker', ns)
            if next_key is not None:
                result['NextKeyMarker'] = next_key.text
            if next_version is not None:
                result['NextVersionIdMarker'] = next_version.text
        
        return result


# Example usage
if __name__ == "__main__":
    import os
    
    client = S3DirectAPIClient(
        access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region='us-east-1'
    )
    
    # List versions for a specific prefix
    response = client.list_object_versions(
        bucket='your-bucket-name',
        prefix='test/',
        max_keys=10
    )
    
    print(f"Truncated: {response['IsTruncated']}")
    print(f"Total versions: {len(response['VersionStack'])}")
    
    # Count delete markers and regular versions
    delete_markers = sum(1 for v in response['VersionStack'] if v['IsDeleteMarker'])
    regular_versions = len(response['VersionStack']) - delete_markers
    print(f"Regular versions: {regular_versions}")
    print(f"Delete markers: {delete_markers}")
    
    # Print version stack in order
    for i, version in enumerate(response['VersionStack']):
        marker_type = "DeleteMarker" if version['IsDeleteMarker'] else "Version"
        print(f"{i+1}. {marker_type}: {version['VersionId']} - {version['LastModified']}")
    