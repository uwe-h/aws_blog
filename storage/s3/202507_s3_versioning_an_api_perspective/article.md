# S3 Versioning an API Perspective

![Illustration](./illustration.jpg)

Many times I fall into the same pitfalls related to S3 Versioning: Every time I want to simplify code through refactoring, I encounter the same understanding gaps that seem to be understood only temporarily.

Therefore, I want to describe S3 Versioning from an API perspective in a form that allows me to understand and memorize it. I hope this way of describing it helps you to memorize it better as well. 


S3 Versioning is a way of having immutable changes in you bucket. Therefore, S3 creates with each upload a different version in a version stack for each S3 Key. Deletes becomes immutable by adding delete marker on the top of the version stack. In other words, a delete marker is a tombstone.

This article focus more on the SDK/API Part of S3 Versioning and therefore I classify the S3 services into three categories:

<table style="border-collapse: collapse">
<tr style="border: none">
<td style="border: none"> <img src="Sa3VersionAgnosticIcons.png"> </td><td style="border: none"> <span style="font-weight: 700">Versioning Agnostic</span><br> The behavior of AWS services that transparently handle versioning as if it didn't exist. In other words the services behaves in this mode like a non-versioned bucket. </td></tr> 
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

A delete marker is not an object and has no meta data. Accordingly, it is not allowed (405/Method Not Allowed) to use GetObject or HeadObject on a delete marker in the version specific mode. In the version agnostic mode it returns 404 respectivly "no such key" depending on the service.

## Version Aware: List Object Versions

The ListObjectVersions service allows to return the versions of a subset of keys or all keys. You might use the prefix to limit the responses on that prefix that could even be one key itself.

The main purpose of key marker and version id marker is to iterate through a big set of keys and versions. So you can use the next marker of the previous call to iterate further. However, you can use it also for your own purpose and here might be a big pitfall which you can step into: the version id marker does not return the version id provided with the marker it provides the first after it.

A quick workaround to add a head object call for the version you want to start with, except that head returns "Method Not Allowed" for delete markers.

Another, pitfall that I step into is the seperation of object versions and delete markers in the response for the [SDK (e.g., boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_object_versions.html). The [API](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectVersions.html) seems not to have this separation (Currently an assumption only). This fact an the time resolution of last modified leads to the fact, that I cannot determine the correct order in fast creation of object versions and delete marker.

I overcome this pitfall by using an well-established and proven technique of log-based systems: log-chaining. Therefore, you have a previous pointer to the previous version or delete marker. In concurrent setups the difficulties lies to determine the correct previous version.

## Further Analysis Required

* Object Lock: According to the [documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html), it prevents "Deletion and Overwriting of Object Versions". PutObject does not allow overwriting versions, and CopyObject doesn't either. However, Delete can physically delete objects, which can be prevented.

* The List Object Versions and the order criteria of delete markers and object versions with direct usage of the API.

## Proof of Article

I provided some [unit tests]() to demonstrate the behavior of S3 according versioning. These test runs regulary to guarantee continuity of these statements. Please check the [github action](https://github.com/uwe-h/aws_blog/actions) to make it sure.

## TODO Add Unit Test Link