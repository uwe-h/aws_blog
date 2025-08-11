"""
Utilities for encoding and decoding binary data to and from different forms.
"""

def to_hex(data):
    """
    Converts byte data to a Hex-encoded string.
    
    Args:
        data: bytes data to hex encode
        
    Returns:
        hex-encoded string
    """
    return data.hex().lower()

def from_hex(hex_data):
    """
    Converts a Hex-encoded data string to the original byte data.
    
    Args:
        hex_data: hex-encoded data to decode
        
    Returns:
        decoded data from the hex string
    """
    return bytes.fromhex(hex_data)