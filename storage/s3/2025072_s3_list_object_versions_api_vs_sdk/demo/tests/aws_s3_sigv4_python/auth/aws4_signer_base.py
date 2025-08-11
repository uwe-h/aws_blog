"""
Common methods and properties for all AWS4 signer variants
"""
import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlparse
from ..util.http_utils import url_encode
from ..util.binary_utils import to_hex

class AWS4SignerBase:
    # SHA256 hash of an empty request body
    EMPTY_BODY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    UNSIGNED_PAYLOAD = "UNSIGNED-PAYLOAD"
    
    SCHEME = "AWS4"
    ALGORITHM = "HMAC-SHA256"
    TERMINATOR = "aws4_request"
    
    # Format strings for the date/time and date stamps required during signing
    ISO8601_BASIC_FORMAT = "%Y%m%dT%H%M%SZ"
    DATE_STRING_FORMAT = "%Y%m%d"
    
    def __init__(self, endpoint_url, http_method, service_name, region_name):
        """
        Create a new AWS V4 signer.
        
        Args:
            endpoint_url: The service endpoint URL
            http_method: The HTTP verb for the request, e.g. GET
            service_name: The signing name of the service, e.g. 's3'
            region_name: The system name of the AWS region, e.g. us-east-1
        """
        self.endpoint_url = endpoint_url
        self.http_method = http_method
        self.service_name = service_name
        self.region_name = region_name
    
    @staticmethod
    def get_canonicalized_header_names(headers):
        """
        Returns the canonical collection of header names that will be included in
        the signature. For AWS4, all header names must be included in the process
        in sorted canonicalized order.
        """
        sorted_headers = sorted(headers.keys(), key=str.lower)
        return ';'.join(header.lower() for header in sorted_headers)
    
    @staticmethod
    def get_canonicalized_header_string(headers):
        """
        Computes the canonical headers with values for the request. For AWS4, all
        headers must be included in the signing process.
        """
        if not headers:
            return ""
        
        # Sort headers by case-insensitive order
        sorted_headers = sorted(headers.keys(), key=str.lower)
        
        # Form the canonical header:value entries in sorted order
        # Multiple white spaces in the values should be compressed to a single space
        canonical_headers = []
        for key in sorted_headers:
            canonical_key = key.lower().strip()
            canonical_value = ' '.join(headers[key].split())
            canonical_headers.append(f"{canonical_key}:{canonical_value}")
        
        return '\n'.join(canonical_headers) + '\n'
    
    @staticmethod
    def get_canonical_request(endpoint, http_method, query_parameters, 
                            canonicalized_header_names, canonicalized_headers, body_hash):
        """
        Returns the canonical request string to go into the signer process
        """
        canonical_request = (
            f"{http_method}\n"
            f"{AWS4SignerBase.get_canonicalized_resource_path(endpoint)}\n"
            f"{query_parameters}\n"
            f"{canonicalized_headers}\n"
            f"{canonicalized_header_names}\n"
            f"{body_hash}"
        )
        return canonical_request
    
    @staticmethod
    def get_canonicalized_resource_path(endpoint):
        """
        Returns the canonicalized resource path for the service endpoint.
        """
        parsed = urlparse(endpoint)
        path = parsed.path
        
        if not path:
            return "/"
        
        encoded_path = url_encode(path, keep_path_slash=True)
        return encoded_path if encoded_path.startswith("/") else "/" + encoded_path
    
    @staticmethod
    def get_canonicalized_query_string(parameters):
        """
        Examines the specified query string parameters and returns a
        canonicalized form.
        """
        if not parameters:
            return ""
        
        # Sort parameters and URL encode both keys and values
        sorted_params = []
        for key, value in parameters.items():
            encoded_key = url_encode(key, keep_path_slash=False)
            encoded_value = url_encode(value, keep_path_slash=False)
            sorted_params.append((encoded_key, encoded_value))
        
        sorted_params.sort()
        
        # Join with & separator
        return '&'.join(f"{key}={value}" for key, value in sorted_params)
    
    @staticmethod
    def get_string_to_sign(scheme, algorithm, date_time, scope, canonical_request):
        """
        Constructs the string to sign for AWS Signature Version 4
        """
        string_to_sign = (
            f"{scheme}-{algorithm}\n"
            f"{date_time}\n"
            f"{scope}\n"
            f"{to_hex(AWS4SignerBase.hash_string(canonical_request))}"
        )
        return string_to_sign
    
    @staticmethod
    def hash_string(text):
        """
        Hashes the string contents (assumed to be UTF-8) using the SHA-256 algorithm.
        """
        return hashlib.sha256(text.encode('utf-8')).digest()
    
    @staticmethod
    def hash_bytes(data):
        """
        Hashes the byte array using the SHA-256 algorithm.
        """
        return hashlib.sha256(data).digest()
    
    @staticmethod
    def sign(string_data, key, algorithm):
        """
        Signs the given string with the given key using the specified algorithm
        """
        return hmac.new(key, string_data.encode('utf-8'), hashlib.sha256).digest()