# Content Ingestion Service

The ingestion service provides API endpoints for three different areas of management:

<!--ts-->
* [Partner's Landing Storage](#partner-landing-storage-management)
* [Content Assets](#content-asset-management)  
* [Streaming Packages](#streaming-package-management)
<!--te-->

## Partner Landing Storage Management

For each partner we onboard to our platform, we will need to define a landing storage account resource where to store all of its content initially, as part of the ingestion process. Ideally this resource would be located as close to the partner's main upload site (if uploading from their network). 

The payload points to an Azure subscription and resource group containing a **single** storage account that will be used as the landing storage resource for the partner. All the partner's assets will be pushed initially to this storage account. 

### Onboard Partner's Landing Storage

[_Request_](src/Product/ContentIngestion.Contracts.External/WireLandingStorage.cs)

`POST [ingestionHost]/v1/storage`

    {
      "partnerId": "GusGames"
      "subscription": "A78EEA19-36E9-4882-A2B0-0B7A789EE7BF"
      "resourceGroup": "gusgamesctinrg"
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireLandingStorage.cs)

`201 Created`

    {
      "partnerId": "GusGames"
      "subscription": "A78EEA19-36E9-4882-A2B0-0B7A789EE7BF"
      "resourceGroup": "gusgamesctinrg"
    }



### Get Onboarded Storage Info for Partner

_Request_

`GET [ingestionHost]/v1/storage/{partnerId}`

[_Response_](src/Product/ContentIngestion.Contracts.External/WireLandingStorage.cs)

 `200 OK`

    {
      "partnerId": "GusGames"
      "subscription": "A78EEA19-36E9-4882-A2B0-0B7A789EE7BF"
      "resourceGroup": "gusgamesctinrg"
    }

## Content Asset Management

<!--ts-->
* [Terminology](#terminology)
* [Define New Asset](#define-new-content-asset)
* [Update Asset](#update-content-asset)
* [Get Asset By Id](#get-asset-by-id)
* [Get New Asset Version Upload Info](#get-new-asset-version-upload-info)
* [Define New Asset Version](#define-new-asset-version)
* [Update Asset Version](#update-asset-version)
* [Get Asset Version By Id](#get-asset-version)
* [Search for Asset](#search-for-asset)
* [List a Partner's Assets For Update](#list-partner's-assets)
<!--te-->

### Terminology

An asset represents a certain piece of content (be it game or DLC) and its lineage of versions. It captures all the information shared across all versions of this content. 

Each asset is tagged to a partner (`partnerId` field) and has a unique id in the context of that partner (`sourceId` field. For Xbox content, each asset maps to basically a XVC lineage, and its `sourceId` is identical to the XVC's `ContentID` from the M$ Catalog.

With each version of an asset (stored as a separate blob), the binary content changes but the `sourceId` (aka contentId for Xbox) stays the same. Each new version will require then a new content upload, will have a different
tag (`version` field) that is supposed to be the same as in the partner's catalog, and will have an availability 
window where that specific version of the content can be streamed in the platform (this also follows the partner's 
catalog availability).

### Define New Content Asset

[_Request_](src/Product/ContentIngestion.Contracts.External/WireAsset.cs)

`POST [ingestionHost]/v1/asset`

    {
        "partnerId": "GusGames",
        "sourceId": "<Content Id from M$>",
        "type": "<Game|DLC>",
        "platform": "MACHINE_PC",
        "name": "SomeGame", // [Optional]
        "description": "some description", // [Optional]
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireAsset.cs)

 `201 Created`

    {
        "id": <some guid>,
        "partnerId": "GusGames",
        "sourceId": "<Content Id from M$>",
        "type": "<Game|DLC>",
        "platform": "MACHINE_PC",
        "name": "SomeGame",
        "description": "some description",
    }

_Note_: All possible values for the target platform of an asset are defined in the [ContentPlatformType](src/Product/ContentIngestion.Contracts.External/ContentPlatformType.cs) enum.

### Update Content Asset

[_Request_](src/Product/ContentIngestion.Contracts.External/WireAsset.cs)

`PUT [ingestionHost]/v1/asset/{assetId}`

    {
        "type": "<Game|DLC>", // [Optional]
        "name": "SomeGame", // [Optional]
        "description": "some description", // [Optional]
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireAsset.cs)

`200 OK`

    {
        "id": <some guid>,
        "partnerId": "GusGames",
        "sourceId": "<Content Id from M$>",
        "type": "<Game|DLC>",
        "platform": "MACHINE_PC",
        "name": "SomeGame",
        "description": "some description",
    }

### Get Asset By Id

_Request_

`GET [ingestionHost]/v1/asset/{assetId}?includeVersions={true|false}`

[_Response_](src/Product/ContentIngestion.Contracts.External/WireAssetWithVersions.cs)

`200 OK`

    {
        "id": <guid>,
        "partnerId": "GusGames",
        "sourceId": "<Content Id from M$>",
        "type": "<Game|DLC>",
        "platform": "MACHINE_PC",
        "name": "SomeGame",
        "description": "some description",
        "versions": [  // only if includeVersions query param is set to true
            {
                "id": <guid>
                "version": "1.0"
                "from": "2018-11-10 00:00",
                "until": "2020:11-10 12:00"
                "blobName": "<blob name here>"
            }
            ...
        ]
    }

### Get New Asset Version Upload Info

When creating a new version of an asset, one would first have to call this API to get an URI where to upload the contents of that new asset version. The client is responsible to then upload the content of this new version to 
the provided URI.

The API will also allocate a unique id for this new version, that has to be 
sent back next when defining the specifics of the new asset version. 

_Request_

`GET [ingestionHost]/v1/asset/{assetId}/version/upload`

[_Response_](src/Product/ContentIngestion.Contracts.External/AssetVersionUploadInfo.cs)

`200 OK`

    {
        "allocatedVersionId": <guid>,
        "uploadUri": <blob sas URI>
    }


### Define New Asset Version

[_Request_](src/Product/ContentIngestion.Contracts.External/WireAssetVersion.cs)

`POST [ingestionHost]/v1/asset/{assetId}/version`

    {
       "id": <guid>, // This needs to the be id obtained from the previous call to get the version upload info
       "version": "1.2.3" // Partner provided version for this asset, same as in their system
       "from": <UTC datetime>
       "until": null // not expiring
       "mountBlob": "<unique blob name for this version>" // For Xbox, this is 'ContentId.PDUID' for a given XVD
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireAssetVersion.cs)

`201 Created`

    {
       "id": <guid>,
       "version": "1.2.3"
       "from": <UTC datetime>
       "until": "9999-12-31 23:59:59" // UTC Max
       "mountBlob": <ContentId.PDUID> // For Xbox
    }

### Update Asset Version

[_Request_](src/Product/ContentIngestion.Contracts.External/WireAssetVersion.cs)

`PUT [ingestionHost]/v1/asset/{assetId}/version/{assetVersionId}`

    {
       "from": <new start date>
       "until": <new expiration date>
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireAssetVersion.cs)

`200 OK`

    {
       "id": <guid>,
       "version": "1.2.3"
       "from": <updated from date>
       "until": <updated until date>
       "mountBlob": <ContentId.PDUID> // For Xbox
    }

### Get Asset Version

_Request_

`GET [ingestionHost]/v1/asset/{assetId}/version/{assetVersionId}`

[_Response_](src/Product/ContentIngestion.Contracts.External/WireAssetVersion.cs)

`200 OK`

    {
       "id": <guid>,
       "version": "1.2.3"
       "from": <updated from date>
       "until": <updated until date>
       "mountBlob": <ContentId.PDUID> // For Xbox
    }

### Search for Asset

_Request_

`GET [ingestionHost]/v1/asset/search?sourceId=<asset_source_id>&version=<specific_version>&includeAllVersions=true`

_Headers_ : 
* `x-ms-gs-partnerId`: GusGames

[_Response_](src/Product/ContentIngestion.Contracts.External/WireAssetWithVersions.cs)

`200 OK`

    {
        "id": <guid>,
        "partnerId": "GusGames",
        "sourceId": "<asset_source_id>",
        "type": "<Game|DLC>",
        "platform": "MACHINE_PC",
        "name": "SomeGame",
        "description": "some description",
        "versions": [
            {
                "id": <guid>
                "version": "1.0"
                "from": "2018-11-10 00:00",
                "until": "2020:11-10 12:00"
                "blobName": "<blob name here>"
            }
            ...
        ]
    }

If searching by `sourceId` alone, the API will return the info on the most recent version (highest `version` tag) that was defined for the asset. 

If searching for a specific version by using the additional `version` query parameter, then the API will return information about the asset and that specific version, if valid. 

If the `includeAllVersions` flag is set, the API will return info on all available versions of the asset. 

### List Partner's Assets

This API has temporary designation as it will be used by the current implementation of the update service to 
get the list of all non-expired versions of any asset ingested for a given partner, to be able to then check
for updates. Eventually, this implementation will move to a Push model from the XUS service, since otherwise 
it will not scale, and at that point the API might no longer be required.

One can request the assets for a specific [platform type](src/Product/ContentIngestion.Contracts.External/ContentPlatformType.cs).

_Request_

`GET [ingestionHost]/v1/asset/list?platform=<platform_type>`

_Headers_ : 
* `x-ms-gs-partnerId`: GusGames

[_Response_](src/Product/ContentIngestion.Contracts.External/AssetInfoForUpdate.cs)

`200 OK`

    {
        [
            {
                "id": <guid>,
                "sourceId": "<assetSourceId>", // ContentId for Xbox,
                "versionId": <guid>,
                "version": "1.2",
                "from": <UTC datetime>
                "until": <UTC datetime>
            },
            ...
        ]
    }

## Streaming Package Management

<!--ts-->
* [Terminology](#terminology)
* [Define New Streaming Package](#define-a-new-streaming-package)
* [Update Streaming Package](#update-a-streaming-package)
* [Get Package By Id](#get-package-by-id)
* [Define New Package Version](#define-new-package-version)
* [Update Package Version](#update-package-version)
* [Get Package Version By Id](#get-package-version-by-id)
* [Get Package Details for Session](#get-package-details-for-session)
* [Get Package Details for Replication](#get-package-details-for-replication)
* [Search for Package](#search-for-package)
* [List a Partner's Packages](#list-partner's-packages)
<!--te-->

### Terminology

Within our platform, users will request and play games in the form of streaming packages, which represent
a collection of assets that are meant to be offered together (e.g. base game + DLC packs), as well as additional metadata about the collection as a whole. 

Just like assets, streaming packages are tagged per partner and have their own unique id in the partner's namespace (`sourceId` property again). We expect that the client will come asking to play a game using this `sourceId` and the `partnerId`, and the platform will ensure that the right collection of assets are installed on the game server for streaming. 

The streaming packages are made up of a collection of assets (referenced by their globally unique id), but not a specific version of each of those assets. We will determine at runtime which exact version of 
each component asset is best to be mounted for streaming at that time. Also, streaming packages can be versioned whenever their composition changes (e.g. new DLC pack launches and is added to the package). Each version has its own availability time window and the platform will use that to determine which version of a streaming package should be served at a given time.

The packages are meant to be streamed from certain game server platforms (`targetPlatform` field) and contain platform specific properties that are useful for mounting the game on the server (`properties` field, treated as a property bag).

### Define a New Streaming Package

[_Request_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackage.cs)

`POST [ingestionHost]/v1/package`

    {
        "partnerId": "GusGames",
        "sourceId": "Halo",
        "name": "Halo - The Game",
        "description": "....",
        "properties": 
        {
            "titleId": 0x0D174C79
        },
        "platform": "MACHINE_XBOX_RETAIL"
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackage.cs)

`201 Created`

    {
        "id": <guid>
        "partnerId": "GusGames",
        "sourceId": "Halo",
        "name": "Halo - The Game",
        "description": "....",
        "properties": 
        {
            "titleId": 0x0D174C79
        },
        "platform": "MACHINE_XBOX_RETAIL"
    }

### Update a Streaming Package

[_Request_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackage.cs)

`PUT [ingestionHost]/v1/package/{packageId}`

    {        
        "name": "Halo - The Game - changed",
        "properties": 
        {
            "titleId": 0x0D174C79,
            "otherProp": "propValue"
        }
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackage.cs)

`200 OK`

    {
        "id": <guid>
        "partnerId": "GusGames",
        "sourceId": "Halo",
        "name": "Halo - The Game - changed",
        "description": "....",
        "properties": 
        {
            "titleId": 0x0D174C79,
            "otherProp": "propValue"
        },
        "platform": "MACHINE_XBOX_RETAIL"
    }

### Get Package By Id

_Request_

`GET [ingestionHost]/v1/package/{packageId}`

[_Response_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackage.cs)

`200 OK`

    {
        "id": <guid>
        "partnerId": "GusGames",
        "sourceId": "Halo",
        "name": "Halo - The Game - changed",
        "description": "....",
        "properties": 
        {
            "titleId": 0x0D174C79,
            "otherProp": "propValue"
        },
        "platform": "MACHINE_XBOX_RETAIL"
    }

### Define New Package Version

[_Request_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackageVersion.cs)

`POST [ingestionHost]/v1/package/{packageId}/version`

    {
        "version": "1.1",
        "from": <UTC datetime>
        "until": <UTC datetime> | null,
        "assets": [ <guid>, <guid> ]
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackageVersion.cs)

`201 Created`

    {
        "id": <guid>,
        "version": "1.1",
        "from": <UTC datetime>
        "until": <UTC datetime>,
        "assets": [ <guid>, <guid> ]
    }

### Update Package Version

[_Request_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackageVersion.cs)

`POST [ingestionHost]/v1/package/{packageId}/version/{packageVersionId}`

    {
        "from": <changed UTC datetime>
    }

[_Response_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackageVersion.cs)

`200 OK`

    {
        "id": <guid>,
        "version": "1.1",
        "from": <changed UTC datetime>
        "until": <UTC datetime>,
        "assets": [ <guid>, <guid> ]
    }

### Get Package Version by Id

_Request_

`GET [ingestionHost]/v1/package/{packageId}/version/{packageVersionId}`

[_Response_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackageVersion.cs)

`200 OK`

    {
        "id": <guid>,
        "version": "1.1",
        "from": <UTC datetime>
        "until": <UTC datetime>,
        "assets": [ <guid>, <guid> ]
    }

### Get Package Details for Session

_Request_

`GET [ingestionHost]/v1/package/session?sourceId=<package_source_id>&version=<specific_version>`

_Headers_ : 
* `x-ms-gs-partnerId`: GusGames

[_Response_](src/Product/ContentIngestion.Contracts.External/StreamingPackageInfoForSession.cs)

`200 OK`

    {
        "id": <guid>, // Id of the streaming package version to be used for session
        "partnerId": "GusGames",
        "sourceId": "Halo",
        "version": "1.0",
        "platform": "MACHINE_XBOX_RETAIL",
        "properties": 
        {
            "titleId": 0x0D174C79
        },
        "assets":
        [
            {
                "id": <guid>, // The id of the specific asset version available now
                "sourceId": "...", // The parent asset's source id (aka ContentId for Xbox)
                "blobName": "..."
            },
            ...
        ]
    }

### Get Package Details for Replication

_Request_

`GET [ingestionHost]/v1/package/replication?sourceId=<package_source_id>&version=<specific_version>`

_Headers_ : 
* `x-ms-gs-partnerId`: GusGames

[_Response_](src/Product/ContentIngestion.Contracts.External/StreamingPackageInfoForReplication.cs)

`200 OK`

    {
        "id": <guid>, // Id of the streaming package version to be used for session
        "partnerId": "GusGames",
        "assets":
        [
            {
                "id": <guid>, // The id of the specific asset version available now
                "sourceId": "...", // The parent asset's source id (aka ContentId for Xbox)
                "blobName": "...",
                "version": "1.0",
                "uri": <uri> // The URI from where to replicate the asset's content
            },
            ...
        ]
    }

### Search for Package

_Request_

`GET [ingestionHost]/v1/package/search?sourceId=<package_source_id>&version=<specific_version>&includeAllVersions=true`

_Headers_ : 
* `x-ms-gs-partnerId`: GusGames

[_Response_](src/Product/ContentIngestion.Contracts.External/StreamingPackageInfoForSearch.cs)

`200 OK`

    {
        "id": <guid>
        "partnerId": "GusGames",
        "sourceId": "Halo",
        "name": "Halo - The Game",
        "description": "....",
        "properties": 
        {
            "titleId": 0x0D174C79
        },
        "platform": "MACHINE_XBOX_RETAIL",
        "versions":
        [
            {
                "id": <guid>,
                "version": "1.0",
                "from": <UTC datetime>,
                "until": <UTC datetime>,
                "assets": [ <guid>, <guid> ]
            },
            {
              ....
            }
        ]
    }


### List Partner's Packages

_Request_

`GET [ingestionHost]/v1/package/list`

_Headers_ : 
* `x-ms-gs-partnerId`: GusGames

[_Response_](src/Product/ContentIngestion.Contracts.External/WireStreamingPackage.cs)


`200 OK`

    [
        {
            "id": <guid>
            "partnerId": "GusGames",
            "sourceId": "Halo",
            "name": "Halo - The Game - changed",
            "description": "....",
            "properties": 
            {
                "titleId": 0x0D174C79,
                "otherProp": "propValue"
            },
            "platform": "MACHINE_XBOX_RETAIL"
        },
        {
            ....
        }
    ]