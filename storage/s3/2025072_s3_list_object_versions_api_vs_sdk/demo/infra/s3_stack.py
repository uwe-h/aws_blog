from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
import aws_cdk as cdk

from constructs import Construct

class S3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bkt = s3.Bucket(self, "S3VersioningBucket",
                  versioned=True,
                  auto_delete_objects=True,
                  removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        cdk.CfnOutput(self, "S3BucketName", value=bkt.bucket_name, export_name="S3VersioningBucket12561")
