"""
Sample code showing how to PUT objects to Amazon S3 with Signature V4
authorization
"""
from ..auth.aws4_signer_base import AWS4SignerBase
from ..auth.aws4_signer_for_authorization_header import AWS4SignerForAuthorizationHeader
from ..util.binary_utils import to_hex
from ..util.http_utils import invoke_http_request

OBJECT_CONTENT = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc tortor metus, sagittis eget augue ut,\n"
    "feugiat vehicula risus. Integer tortor mauris, vehicula nec mollis et, consectetur eget tortor. In ut\n"
    "elit sagittis, ultrices est ut, iaculis turpis. In hac habitasse platea dictumst. Donec laoreet tellus\n"
    "at auctor tempus. Praesent nec diam sed urna sollicitudin vehicula eget id est. Vivamus sed laoreet\n"
    "lectus. Aliquam convallis condimentum risus, vitae porta justo venenatis vitae. Phasellus vitae nunc\n"
    "varius, volutpat quam nec, mollis urna. Donec tempus, nisi vitae gravida facilisis, sapien sem malesuada\n"
    "purus, id semper libero ipsum condimentum nulla. Suspendisse vel mi leo. Morbi pellentesque placerat congue.\n"
    "Nunc sollicitudin nunc diam, nec hendrerit dui commodo sed. Duis dapibus commodo elit, id commodo erat\n"
    "congue id. Aliquam erat volutpat.\n"
)

def put_s3_object(bucket_name, region_name, aws_access_key, aws_secret_key):
    """
    Uploads content to an Amazon S3 object in a single call using Signature V4 authorization.
    """
    print("************************************************")
    print("*        Executing sample 'PutS3Object'        *")
    print("************************************************")
    
    if region_name == "us-east-1":
        endpoint_url = f"https://s3.amazonaws.com/{bucket_name}/ExampleObject.txt"
    else:
        endpoint_url = f"https://s3-{region_name}.amazonaws.com/{bucket_name}/ExampleObject.txt"
    
    # Precompute hash of the body content
    content_hash = AWS4SignerBase.hash_string(OBJECT_CONTENT)
    content_hash_string = to_hex(content_hash)
    
    headers = {
        "x-amz-content-sha256": content_hash_string,
        "content-length": str(len(OBJECT_CONTENT)),
        "x-amz-storage-class": "REDUCED_REDUNDANCY"
    }
    
    signer = AWS4SignerForAuthorizationHeader(
        endpoint_url, "PUT", "s3", region_name
    )
    authorization = signer.compute_signature(
        headers,
        None,  # no query parameters
        content_hash_string,
        aws_access_key,
        aws_secret_key
    )
    
    # Express authorization for this as a header
    headers["Authorization"] = authorization
    
    # Make the call to Amazon S3
    response = invoke_http_request(endpoint_url, "PUT", headers, OBJECT_CONTENT)
    print("--------- Response content ---------")
    print(response)
    print("------------------------------------")