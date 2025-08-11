"""
Samples showing how to GET an object from Amazon S3 using Signature V4
authorization.
"""
from ..auth.aws4_signer_base import AWS4SignerBase
from ..auth.aws4_signer_for_authorization_header import AWS4SignerForAuthorizationHeader
from ..util.http_utils import invoke_http_request

def get_s3_object(bucket_name, region_name, aws_access_key, aws_secret_key):
    """
    Request the content of the object '/ExampleObject.txt' from the given
    bucket in the given region using virtual hosted-style object addressing.
    """
    print("*******************************************************")
    print("*  Executing sample 'GetObjectUsingHostedAddressing'  *")
    print("*******************************************************")
    
    # The region-specific endpoint to the target object expressed in path style
    endpoint_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/ExampleObject.txt"
    
    # For a simple GET, we have no body so supply the precomputed 'empty' hash
    headers = {
        "x-amz-content-sha256": AWS4SignerBase.EMPTY_BODY_SHA256
    }
    
    signer = AWS4SignerForAuthorizationHeader(
        endpoint_url, "GET", "s3", region_name
    )
    authorization = signer.compute_signature(
        headers, 
        None,  # no query parameters
        AWS4SignerBase.EMPTY_BODY_SHA256,
        aws_access_key,
        aws_secret_key
    )
    
    # Place the computed signature into a formatted 'Authorization' header
    # and call S3
    headers["Authorization"] = authorization
    response = invoke_http_request(endpoint_url, "GET", headers, None)
    print("--------- Response content ---------")
    print(response)
    print("------------------------------------")