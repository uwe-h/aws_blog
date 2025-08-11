# AWS S3 Signature V4 Python Implementation

This is a Python translation of the Java AWS S3 Signature V4 samples. The code demonstrates how to sign requests to Amazon S3 using AWS Signature Version 4.

## Disclaimer 

This is Q Developer Translation [AWS Given Exampl Java Implementation](https://docs.aws.amazon.com/AmazonS3/latest/API/samples/AWSS3SigV4JavaSamples.zip). This translation was simple created for demonstration purposes.

## Structure

```
aws_s3_sigv4_python/
├── auth/
│   ├── aws4_signer_base.py              # Base signer functionality
│   └── aws4_signer_for_authorization_header.py  # Authorization header signer
├── util/
│   ├── binary_utils.py                  # Hex encoding/decoding utilities
│   └── http_utils.py                    # HTTP request utilities
├── samples/
│   ├── get_s3_object_sample.py          # GET object sample
│   └── put_s3_object_sample.py          # PUT object sample
└── main.py                              # Main entry point
```

## Usage

Run the samples with:

```bash
cd aws_s3_sigv4_python
python main.py <bucket_name> <region_name> <aws_access_key> <aws_secret_key>
```

## Key Differences from Java

- Uses Python's `hashlib` and `hmac` modules instead of Java's crypto classes
- Uses `urllib` for HTTP requests instead of `HttpURLConnection`
- Uses Python's `datetime` instead of Java's `SimpleDateFormat`
- Follows Python naming conventions (snake_case instead of camelCase)
- Uses Python's built-in string methods for text processing

## Dependencies

This implementation uses only Python standard library modules - no external dependencies required.