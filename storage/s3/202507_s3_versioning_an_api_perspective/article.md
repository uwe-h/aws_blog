# S3 Versioning an API Perspective

To be decided:

![Illustration](./internal/Firefly_Create%20an%20Cool%203d%20Sketch%20for%20an%20AWS%20S3%20Versioning%20with%20an%20API-SDK%20Perspective.%20A%20S3%20B%20145567.jpg)

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

## TODO
* the thing with Delete Markers
* Copy Object Tests