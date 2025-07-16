# S3 Versioning an API Perspective

![Illustration](./illustration.jpg)

I repeatedly encounter the same pitfalls with S3 Versioning: Every time I refactor code to simplify it, I run into understanding gaps that seem to be grasped only temporarily.

Therefore, I want to describe S3 Versioning from an API perspective in a way that helps me understand and memorize it. I hope this approach will help you memorize it better as well.

S3 Versioning provides immutable changes in your bucket. S3 creates a different version in a version stack for each S3 key with every upload. Deletes become immutable by adding a delete marker on top of the version stack. In other words, a delete marker is a tombstone.

This article focuses on the SDK/API aspects of S3 Versioning. I classify S3 services into three categories:

<table style="border-collapse: collapse">
<tr style="border: none">
<td style="border: none"> <img src="Sa3VersionAgnosticIcons.png"> </td><td style="border: none"> <span style="font-weight: 700">Versioning Agnostic</span><br> AWS services that transparently handle versioning as if it didn't exist. In other words, these services behave like a non-versioned bucket. </td></tr> 
<tr style="border: none; background: #ffffff"><td style="border: none"> <img src="Sa3VersionSpecificIcons.png"> </td><td style="border: none"> <span style="font-weight: 700">Versioning Specific</span><br> Operations that work with exactly one version, such as getting a specific object version. </td></tr>
<tr style="border: none" ><td style="border: none"> <img src="Sa3VersionAwareIcons.png"> </td><td style="border: none"> <span style="font-weight: 700">Versioning Aware</span><br> Services that return a set of versions. </td></tr>
</table>

<br><br>

| S3 Service/Operation | Classification | Behavior Description |
|---------------------|----------------|---------------------|
| **GetObject** | Versioning Agnostic/Versioning Specific | Always returns the latest version unless versionId is specified. With versionId, it returns the provided version. |
| **HeadObject** | Versioning Agnostic/Versioning Specific | Returns metadata of the latest version unless versionId is specified. With versionId, it returns the metadata of the provided version. |
| **ListObjects/ListObjectsV2** | Versioning Agnostic | Only shows latest versions, ignores version history. Objects whose latest version is a delete marker will not be returned. |
| **ListObjectVersions** | Versioning Aware | Returns all versions and delete markers for objects in the bucket |
| **PutObject** | Versioning Agnostic | Creates a new version automatically when versioning is enabled, overwrites when disabled |
| **DeleteObject** | Versioning Agnostic/Versioning Specific | Creates a delete marker when versioning is enabled, performs permanent delete when versionId is specified |
| **CopyObject** | Versioning Agnostic (Source and Target)/Versioning Specific (Source) | Copies the latest version by default, creates a new version in the destination. When a specific version is specified in the source, it copies that provided version. |
| **PutObjectTagging (with versionId)** | Versioning Specific | Tags specific object version |
| **GetObjectTagging (with versionId)** | Versioning Specific | Gets tags for specific object version |

## Delete Markers

A delete marker is not an object and has no metadata. Therefore, using GetObject or HeadObject on a delete marker in version-specific mode is not allowed (405/Method Not Allowed). In version-agnostic mode, it returns 404 or "no such key" depending on the service.

## Version Aware: List Object Versions

The ListObjectVersions service returns versions of a subset of keys or all keys. You can use the prefix parameter to limit responses to that prefix, which could even be a single key.

The main purpose of key marker and version ID marker is to iterate through large sets of keys and versions. You can use the next marker from the previous call to continue iteration. However, there's a significant pitfall here: the version ID marker does not return the version ID provided with the marker—it returns the first version after it.

A quick workaround is to add a HeadObject call for the version you want to start with, except that HeadObject returns "Method Not Allowed" for delete markers.

Another pitfall I encounter is the separation of object versions and delete markers in the response for SDKs like [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_object_versions.html). The [API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectVersions.html) doesn't seem to have this separation (currently an assumption only). This separation, combined with the time resolution of LastModified, makes it impossible to determine the correct order when rapidly creating object versions and delete markers.

I overcome this pitfall using a well-established technique from log-based systems: log-chaining. This involves maintaining a pointer to the previous version or delete marker. In concurrent setups, the difficulty lies in determining the correct previous version.

## Further Analysis Required

* Object Lock: According to the [documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html), it prevents "Deletion and Overwriting of Object Versions". PutObject does not allow overwriting versions, and CopyObject doesn't either. However, Delete can physically delete objects, which can be prevented.

* The List Object Versions and the order criteria of delete markers and object versions with direct usage of the API.

## Proof of Article

I have provided [unit tests](https://github.com/uwe-h/aws_blog/tree/master/storage/s3/202507_s3_versioning_an_api_perspective/demo) to demonstrate S3 versioning behavior. These tests run regularly to ensure the continuity of these statements. Please check the [GitHub Actions](https://github.com/uwe-h/aws_blog/actions) to verify this.

