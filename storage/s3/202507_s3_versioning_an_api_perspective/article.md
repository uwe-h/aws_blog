# S3 Versioning an API Perspective

To be decided:

![Illustration](./illustration.jpg)

Many times I fall into the same pitfalls related to S3 Versioning: Every time I want to simplify code through refactoring, I encounter the same understanding gaps that seem to be understood only temporarily.

Therefore, I want to describe S3 Versioning from an API perspective in a form that allows me to understand and memorize it. I classify the S3 services into three categories:

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


## Detailed Behavior

The GetObject service returns the object if the key exists, otherwise it returns a NoSuchKey error. If the version doesn't exist, it returns NoSuchVersion. Even if the response has a DeleteMarker flag, it returns MethodNotAllowed as the error code when encountering a delete marker, because a delete marker is not an object and therefore GetObject is not allowed.

HeadObject behaves similarly, except that NoSuchKey becomes a 404 error, and MethodNotAllowed becomes a 405 error. A delete marker has no metadata, so the head request is also not allowed.

The ListObjectVersions service uses a version ID marker to return the next version as either a delete marker or object version, depending on the type of the next version. The SDK uses two separate lists for delete markers and object versions, which leads to ordering problems in my testing. It seems the API doesn't have these problems because it uses a single list. I want to investigate this further!

If you need ListObjectVersions to return the first version as well, you can use HeadObject to retrieve its metadata and then continue with ListObjectVersions. For the ordering problem, you could use version chaining. Be careful—version chaining requires locking in concurrent situations to maintain a correct chain. In this case, it might be better to evaluate accessing the API directly.

## Open Question

* Object Lock: According to the documentation, it prevents "Deletion and Overwriting of Object Versions". PutObject does not allow overwriting versions, and CopyObject doesn't either. However, Delete can physically delete objects, which can be prevented.

## TODO
* the thing with Delete Markers
* Copy Object Tests