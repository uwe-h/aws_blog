# S3 Versioning an API Perspective

To be decided:

![Illustration](./illustration.jpg)

Many times I fall for the same pitfalls in relation to S3 Versioning: All the times I want to simplify the code through refactoring I fell for the same understanding gaps that seems for a short time to be understood. 

Therefore, I want to describe S3 Versioning in relation to an API Perspecitive in a form that allows me to be understand and memorize it. Therefore I classify the s3 services in three categories:

* *Versioning Agnostic*  
is the behavior of AWS Services that transparently handles versioning if it would not exists.
* *Versioning Specific*  
is to exactly do something with one version such as getting an specific object version.
* *Versioning Aware*
is a service that returns a set of versions.



| S3 Service/Operation | Classification | Behavior Description |
|---------------------|----------------|---------------------|
| **GetObject** | Versioning Agnostic/Versioning Specific | Always returns latest version unless versionId specified. With Version Id it returns the exact Version. |
| **HeadObject** | Versioning Agnostic/Version Specific | Returns metadata of latest version unless versionId specified. With Version Id it returns the meta data of the exact version. |
| **ListObjects/ListObjectsV2** | Versioning Agnostic | Only shows latest versions, ignores version history. Object with latest version a delete marker will not be returned. |
| **ListObjectVersions** | Versioning Aware | Returns all versions and delete markers for objects in bucket |
| **PutObject** | Versioning Agnostic | Creates new version automatically when versioning enabled, overwrites when disabled |
| **DeleteObject** | Versioning Agnostic/Version Specific | Creates delete marker when versioning enabled, permanent delete when Version Id is specified |
| **CopyObject** | Versioning Agnostic (Target|Source) Version Specific (Source)  | Copies latest version by default, creates new version in destination. In case in the source a specific version is specified it copies the exact version. |
| **PutObjectTagging (with versionId)** | Versioning Specific | Tags specific object version |
| **GetObjectTagging (with versionId)** | Versioning Specific | Gets tags for specific object version |


## Detailed Behavior

The get object service returns the object in case the key exists, otherwise returns NoSuchKey Error. In case the version does not exists it returns NoSuchVersion. Even if the response marker has an DeleteMarker Flag it returns MethodNotAllowed as error code in case we have an delete marker, because a delete marker is not an object accordingly get object is not allowed.

The head object behaves similar except that NoSuchKey becomes 404, and MethodNotAllowed 405. A delete marker has no meta data, accordingly the head request is also not allowed.

The list object versions service behaves with the usage of version id marker so that it returns the next version as delete marker or object version depending on the type of the next version. The SDK uses two separate list for delete markers and object versions that leads in my testing to ordering problems. It seems that the API do not have the problems, because it is one list. I want to find out soon!

In case you need the list object version to return the first version as well, you can use the head object to retrieve its meta data and then continue with list object versions. For the ordering problem you could use version changing. Be carefully, version changing needs in currency situation locking, so you have a correct chain. In this case, it might be better to evaluate accessing the API directly.

## Open Question

* Object Locks According Documentation prevents "Deletion and Overwriting of Object Versions". Put Object does not allow to overwrite versions and copy object as well not. Yes, Delete can physically delete object that can be prevent.

## TODO
* the thing with Delete Markers
* Copy Object Tests