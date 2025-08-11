"""
Various HTTP helper routines
"""
import urllib.request
import urllib.parse
from urllib.error import HTTPError

def invoke_http_request(endpoint_url, http_method, headers, request_body=None):
    """
    Makes an HTTP request to the specified endpoint
    """
    connection = create_http_connection(endpoint_url, http_method, headers)
    
    try:
        if request_body:
            request_body = request_body.encode('utf-8')
        
        response = urllib.request.urlopen(connection, data=request_body)
        return response.read().decode('utf-8')
    except HTTPError as e:
        return e.read().decode('utf-8')

def create_http_connection(endpoint_url, http_method, headers):
    """
    Creates an HTTP connection with the specified parameters
    """
    request = urllib.request.Request(endpoint_url, method=http_method)
    
    if headers:
        print("--------- Request headers ---------")
        for header_key, header_value in headers.items():
            print(f"{header_key}: {header_value}")
            request.add_header(header_key, header_value)
    
    return request

def url_encode(url, keep_path_slash=False):
    """
    URL encodes the given string
    """
    encoded = urllib.parse.quote(url, safe='')
    if keep_path_slash:
        encoded = encoded.replace('%2F', '/')
    return encoded