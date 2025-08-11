#!/usr/bin/env python3
"""
Main entry point for running AWS S3 Signature V4 samples
"""
import sys
from samples.get_s3_object_sample import get_s3_object
from samples.put_s3_object_sample import put_s3_object

def main():
    if len(sys.argv) != 5:
        print("Usage: python main.py <bucket_name> <region_name> <aws_access_key> <aws_secret_key>")
        sys.exit(1)
    
    bucket_name = sys.argv[1]
    region_name = sys.argv[2]
    aws_access_key = sys.argv[3]
    aws_secret_key = sys.argv[4]
    
    print("Running AWS S3 Signature V4 Python samples...")
    print()
    
    # Run GET sample
    try:
        get_s3_object(bucket_name, region_name, aws_access_key, aws_secret_key)
    except Exception as e:
        print(f"GET sample failed: {e}")
    
    print()
    
    # Run PUT sample
    try:
        put_s3_object(bucket_name, region_name, aws_access_key, aws_secret_key)
    except Exception as e:
        print(f"PUT sample failed: {e}")

if __name__ == "__main__":
    main()