"""
Sample AWS4 signer demonstrating how to sign requests to Amazon S3 using an
'Authorization' header.
"""
from datetime import datetime
from urllib.parse import urlparse
from .aws4_signer_base import AWS4SignerBase
from ..util.binary_utils import to_hex

class AWS4SignerForAuthorizationHeader(AWS4SignerBase):
    
    def __init__(self, endpoint_url, http_method, service_name, region_name):
        super().__init__(endpoint_url, http_method, service_name, region_name)
    
    def compute_signature(self, headers, query_parameters, body_hash, 
                         aws_access_key, aws_secret_key):
        """
        Computes an AWS4 signature for a request, ready for inclusion as an
        'Authorization' header.
        
        Args:
            headers: The request headers; 'Host' and 'X-Amz-Date' will be added
            query_parameters: Any query parameters in canonical format
            body_hash: Precomputed SHA256 hash of the request body content
            aws_access_key: The user's AWS Access Key
            aws_secret_key: The user's AWS Secret Key
            
        Returns:
            The computed authorization string for the request
        """
        # Get the date and time for the subsequent request
        now = datetime.utcnow()
        date_time_stamp = now.strftime(self.ISO8601_BASIC_FORMAT)
        
        # Update the headers with required 'x-amz-date' and 'host' values
        headers["x-amz-date"] = date_time_stamp
        
        parsed_url = urlparse(self.endpoint_url)
        host_header = parsed_url.hostname
        if parsed_url.port and parsed_url.port not in (80, 443):
            host_header = f"{host_header}:{parsed_url.port}"
        headers["Host"] = host_header
        
        # Canonicalize the headers
        canonicalized_header_names = self.get_canonicalized_header_names(headers)
        canonicalized_headers = self.get_canonicalized_header_string(headers)
        
        # Canonicalize query string parameters if any
        canonicalized_query_parameters = self.get_canonicalized_query_string(query_parameters or {})
        
        # Canonicalize the various components of the request
        canonical_request = self.get_canonical_request(
            self.endpoint_url, self.http_method,
            canonicalized_query_parameters, canonicalized_header_names,
            canonicalized_headers, body_hash
        )
        print("--------- Canonical request --------")
        print(canonical_request)
        print("------------------------------------")
        
        # Construct the string to be signed
        date_stamp = now.strftime(self.DATE_STRING_FORMAT)
        scope = f"{date_stamp}/{self.region_name}/{self.service_name}/{self.TERMINATOR}"
        string_to_sign = self.get_string_to_sign(
            self.SCHEME, self.ALGORITHM, date_time_stamp, scope, canonical_request
        )
        print("--------- String to sign -----------")
        print(string_to_sign)
        print("------------------------------------")
        
        # Compute the signing key
        k_secret = (self.SCHEME + aws_secret_key).encode('utf-8')
        k_date = self.sign(date_stamp, k_secret, "HmacSHA256")
        k_region = self.sign(self.region_name, k_date, "HmacSHA256")
        k_service = self.sign(self.service_name, k_region, "HmacSHA256")
        k_signing = self.sign(self.TERMINATOR, k_service, "HmacSHA256")
        signature = self.sign(string_to_sign, k_signing, "HmacSHA256")
        
        # Build the authorization header
        credentials_authorization_header = f"Credential={aws_access_key}/{scope}"
        signed_headers_authorization_header = f"SignedHeaders={canonicalized_header_names}"
        signature_authorization_header = f"Signature={to_hex(signature)}"
        
        authorization_header = (
            f"{self.SCHEME}-{self.ALGORITHM} "
            f"{credentials_authorization_header}, "
            f"{signed_headers_authorization_header}, "
            f"{signature_authorization_header}"
        )
        
        return authorization_header