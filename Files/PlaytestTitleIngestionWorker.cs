// <copyright file="PlaytestTitleIngestionWorker.cs" company="Microsoft">
// Copyright (c) Microsoft. All rights reserved.
// Internal use only.
// </copyright>

// DRAFT SKELETON (XC3). A trimmed-down copy of ProductIngestionWorker.
// Playtest is always ONE StoreAsset -> ONE streaming package -> ONE 1.0 version.
// Copy the real ProductIngestionWorker into services.contentingestion, then strip the
// items called out below (see also Documentation/PlaytestIngestionWorkflowDevSpec.docx §8).

namespace Microsoft.GameStreaming.Services.ContentCatalog.Ingestion.Worker.Core;

using Microsoft.GameStreaming.Partners;
using Microsoft.GameStreaming.Partners.Contracts;
using Microsoft.GameStreaming.Services.Common.Content.Ids;
using Microsoft.GameStreaming.Services.Common.Ids;
using Microsoft.GameStreaming.Workflows.WorkerFramework;
using IPlaytestTitleIngestionContext =
    Workflows.WorkerFramework.IJobContext<PlaytestTitleIngestion.JobParameters, PlaytestTitleIngestion.JobState>;

public class PlaytestTitleIngestionWorker
    : AsyncWorker<PlaytestTitleIngestion.JobParameters, PlaytestTitleIngestion.JobState>
{
    // STRIP vs ProductIngestionWorker — states that do NOT exist here:
    //   GetStoreAssetState        -> StoreAsset is supplied on JobParameters.
    //   IngestDwobsState          -> no DWOBs for playtest.
    //   PollFilterAssetsState     -> single asset, nothing to filter.
    //   DeleteOrphanedEntitiesState -> nothing to reconcile.
    public const string ValidateParametersState = "ValidateParameters";
    public const string TriggerAssetsIngestionState = "TriggerAssetsIngestion";
    public const string PollAssetsIngestionState = "PollAssetsIngestion";
    public const string CreatePackageState = "CreatePackage";
    public const string ConfigureOfferingState = "ConfigureOffering";
    public const string SucceededState = "Succeeded";
    public const string FailedState = "Failed";

    private readonly IWorkflowProcessor workflowProcessor;
    private readonly IPackagesProcessor packagesProcessor;
    private readonly IPartnerRegistryClient partnerRegistryClient;

    public PlaytestTitleIngestionWorker(
        IWorkflowProcessor workflowProcessor,
        IPackagesProcessor packagesProcessor,
        IPartnerRegistryClient partnerRegistryClient)
    {
        this.workflowProcessor = workflowProcessor;
        this.packagesProcessor = packagesProcessor;
        this.partnerRegistryClient = partnerRegistryClient;
    }

    [AsyncWorkflowState(ValidateParametersState, isInitialState: true)]
    public Task<AsyncExecutionResult> ValidateParametersAsync(IPlaytestTitleIngestionContext context)
    {
        context.State ??= new PlaytestTitleIngestion.JobState();
        context.Parameters.Validate();
        return Task.FromResult(AsyncExecutionResult.TransitionTo(TriggerAssetsIngestionState));
    }

    // ONE asset, ONE job. Each DNA group becomes a distinct XusAudience.
    // STRIP: the foreach over StoreGameAssets.Union(StoreDlcAssets) — playtest has no DLC.
    [AsyncWorkflowState(TriggerAssetsIngestionState)]
    public async Task<AsyncExecutionResult> TriggerAssetsIngestionAsync(IPlaytestTitleIngestionContext context)
    {
        StoreAsset storeAsset = context.Parameters.StoreAsset;

        var parameters = new AssetIngestion.JobParameters(context.Parameters.PartnerId, storeAsset.ContentId)
        {
            StoreAsset = storeAsset,
            Audiences = context.Parameters.Audiences, // one XusAudience per DNA group
        };

        WorkflowSubmissionTicket ticket = await this.workflowProcessor.TriggerAssetIngestionJobAsync(
            parameters, createdBy: $"PlaytestTitleIngestionJob: {context.Id}");

        context.State.PendingAssetJob = new ChildJobState
        {
            JobId = ticket.WorkflowId,
            PartitionKey = ticket.WorkflowPartitionKey,
            Status = JobStatus.Running,
        };

        return AsyncExecutionResult.TransitionTo(PollAssetsIngestionState, this.settings.ChildJobPollingInterval);
    }

    // Unchanged poll loop from ProductIngestionWorker, reduced to a single child job.
    [AsyncWorkflowState(PollAssetsIngestionState)]
    public async Task<AsyncExecutionResult> PollAssetsIngestionAsync(IPlaytestTitleIngestionContext context)
    {
        await this.workflowProcessor.UpdateChildJobStatusesAsync<AssetIngestion.JobParameters, AssetIngestion.JobState>(
            new[] { context.State.PendingAssetJob });

        if (context.State.PendingAssetJob.Status == JobStatus.Running)
        {
            return AsyncExecutionResult.RetryWith(this.assetIngestionJobsPollingPolicy);
        }

        if (context.State.PendingAssetJob.Status != JobStatus.Succeeded)
        {
            context.State.StatusDetails = $"Asset ingestion did not succeed. Status: {context.State.PendingAssetJob.Status}.";
            return AsyncExecutionResult.TransitionTo(FailedState);
        }

        return AsyncExecutionResult.TransitionTo(CreatePackageState);
    }

    // ONE package, ONE version (1.0), tied to a neutral title id.
    // STRIP vs ProductIngestionWorker package hydration:
    //   - the assetsBySourceId dictionary + "Not all assets are ingested" multi-asset check,
    //   - the existingPackages lookup + else-if "update name/description" (market-mix) branch,
    //   - StoreDlcAssets / dlc Markets.Intersect join,
    //   - latest-version retire (AvailableUntil = utcNow) reconciliation,
    //   - the ContentIdsFilter branch.
    [AsyncWorkflowState(CreatePackageState)]
    public async Task<AsyncExecutionResult> CreatePackageAsync(IPlaytestTitleIngestionContext context)
    {
        StoreAsset storeAsset = context.Parameters.StoreAsset;
        WireAsset gameAsset = await this.GetIngestedAssetAsync(storeAsset.ContentId); // single lookup

        WireStreamingPackage package = await this.packagesProcessor.CreatePackageAsync(new WireStreamingPackage
        {
            PartnerId = context.Parameters.PartnerId,
            TitleId = ContentEntityIdentifiers.QualifyNeutralTitleId(
                ContentEntityIdentifiers.GenerateNeutralTitleId(storeAsset.StoreEntry.Name)),
            Name = ResolvePackageName(context, storeAsset),
            Description = ResolvePackageDescription(context, storeAsset, null),
            Platform = context.Parameters.Platform,
            Properties = new PackageProperties(),
            MainGameAssetId = gameAsset.Id,
        });

        context.State.StreamingPackageId = package.Id;
        context.State.TitleId = package.TitleId;

        // Single 1.0 version — no DLC bundle, no market mix, no prior version to retire.
        await this.packagesProcessor.CreatePackageVersionAsync(package.Id, new WireStreamingPackageVersion
        {
            // TODO: confirm the minimal 1.0 version shape (no DLC asset ids, single market).
            MainGameAssetId = gameAsset.Id,
        });

        return AsyncExecutionResult.TransitionTo(ConfigureOfferingState);
    }

    // Partner Registry: create the offering AND attach the title in ONE PR, wait for the PR
    // to merge, then link. Replaces ProductIngestion's separate offering-write + AddCollectionTitle.
    [AsyncWorkflowState(ConfigureOfferingState)]
    public async Task<AsyncExecutionResult> ConfigureOfferingAsync(IPlaytestTitleIngestionContext context)
    {
        // TODO: build OfferingV2 (AllowedDnaGroups + AllowedSandboxId + ExpirationTime) and CollectionTitle,
        //       then call the new combined Partner Registry method (offering create + title add, one PR).
        // await this.partnerRegistryClient.ConfigureAsync(offering, title, user);
        // Poll until the PR merges, then link the package/title to the offering.
        await Task.Yield();
        return AsyncExecutionResult.TransitionTo(SucceededState);
    }

    [AsyncWorkflowState(SucceededState)]
    public Task<AsyncExecutionResult> CompletedAsync(IPlaytestTitleIngestionContext context)
        => Task.FromResult(AsyncExecutionResult.Success);

    [AsyncWorkflowState(FailedState)]
    public Task<AsyncExecutionResult> HandleJobFailureAsync(IPlaytestTitleIngestionContext context)
        => Task.FromResult(AsyncExecutionResult.Fail);
}
