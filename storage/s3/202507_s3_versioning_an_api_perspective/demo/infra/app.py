#!/usr/bin/env python3
import aws_cdk as cdk
from s3_stack import S3Stack

app = cdk.App()
S3Stack(app, "S3VersioningApiPerspectiveStack")
app.synth()