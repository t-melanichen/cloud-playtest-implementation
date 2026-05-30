// <copyright file="TitleIngestionWorker.cs" company="Microsoft">
// Copyright (c) Microsoft. All rights reserved.
// Internal use only.
// </copyright>

namespace Microsoft.GameStreaming.Services.ContentCatalog.Ingestion.Worker.Core;

using Microsoft.Extensions.Options;
using Microsoft.GameStreaming.AllocationManagerService.Client;
using Microsoft.GameStreaming.AllocationManagerService.Contracts;
using Microsoft.GameStreaming.Partners;
using Microsoft.GameStreaming.Partners.Contracts;
using Microsoft.GameStreaming.Services.AllocationManagerService.Client;
using Microsoft.GameStreaming.Services.Common;
using Microsoft.GameStreaming.Services.Common.ArgumentValidation;
using Microsoft.GameStreaming.Services.Common.Content.Extensions;
using Microsoft.GameStreaming.Services.Common.Content.Ids;
using Microsoft.GameStreaming.Services.Common.Ids;
using Microsoft.GameStreaming.Services.Common.Providers;
using Microsoft.GameStreaming.Services.Common.Telemetry.Base.Metrics;
using Microsoft.GameStreaming.Services.ContentCatalog.Common.Contracts.Workflows;
using Microsoft.GameStreaming.Services.ContentCatalog.Common.Contracts.Workflows.Legacy;
using Microsoft.GameStreaming.Services.ContentCatalog.Ingestion.Core.Processors;
using Microsoft.GameStreaming.Services.ContentCatalog.Ingestion.Worker.Configuration;
using Microsoft.GameStreaming.Services.ContentCatalog.Ingestion.Worker.Telemetry;
using Microsoft.GameStreaming.Services.Mailer.Client;
using Microsoft.GameStreaming.Services.Mailer.Contracts;
using Microsoft.GameStreaming.Workflows.WorkerFramework;
using ITitleIngestionContext = Workflows.WorkerFramework.IJobContext<TitleIngestion.JobParameters, TitleIngestion.JobState>;

public class TitleIngestionWorker : AsyncWorker<TitleIngestion.JobParameters, TitleIngestion.JobState>
{
    private const float GB = 1_000_000_000;

    public const string ValidateParametersState = "ValidateParameters";
    public const string InitializeProductIngestionState = "InitializeProductIngestion";
    public const string PollProductIngestionState = "PollProductIngestion";
    public const string AddTitleToCollectionState = "AddTitleToCollection";
    public const string PollFirstInstallState = "PollFirstInstall";
    public const string NotifyInstallNotFoundState = "NotifyInstallNotFound";
    public const string SucceededState = "Succeeded";
    public const string FailedState = "Failed";

    private readonly IWorkflowProcessor workflowProcessor;
    private readonly TitleIngestionSettings settings;
    private readonly RetryPolicy productIngestionJobsPollingPolicy;
    private readonly IPartnerRegistryClient partnerRegistryClient;
    private readonly IMailerClient mailerClient;
    private readonly IServerAllocatorClient serverAllocatorClient;
    private readonly RetryPolicy allocatorInstallPollingPolicy;
    private readonly IEnvironmentProvider environmentProvider;

    private readonly ILogger logger;

    public TitleIngestionWorker(
        IWorkflowProcessor workflowProcessor,
        IOptions<TitleIngestionSettings> workerOptions,
        ILogger<TitleIngestionWorker> logger,
        IMetricEmitter metricEmitter,
        IPartnerRegistryClient partnerRegistryClient,
        IMailerClient mailerClient,
        IServerAllocatorClient serverAllocatorClient,
        IEnvironmentProvider environmentProvider,
        IAsyncOperator asyncOperator) : base(asyncOperator, workflowProcessor.WorkflowClient, logger, metricEmitter)
    {
        this.workflowProcessor = workflowProcessor;
        this.settings = workerOptions.Value;
        this.productIngestionJobsPollingPolicy = RetryPolicy.CreateConstantPolicy(this.settings.ChildJobPollingInterval);
        this.productIngestionJobsPollingPolicy.FailAfter = this.settings.ChildJobPollingTimeout;
        this.partnerRegistryClient = partnerRegistryClient;
        this.mailerClient = mailerClient;
        this.serverAllocatorClient = serverAllocatorClient;
        this.environmentProvider = environmentProvider;
        this.allocatorInstallPollingPolicy = RetryPolicy.CreateConstantPolicy(this.settings.AllocatorInstallPollingInterval);
        this.allocatorInstallPollingPolicy.FailAfter = this.settings.AllocatorInstallPollingTimeout;

        this.logger = logger;
    }

    public override string QueueName => TitleIngestion.QueueName;

    public override string JobType => TitleIngestion.JobType;

    public override TimeSpan LockDuration => this.settings.LockDuration;

    [AsyncWorkflowState(ValidateParametersState, isInitialState: true)]
    public async Task<AsyncExecutionResult> ValidateParametersAsync(ITitleIngestionContext context)
    {
        context.State ??= new TitleIngestion.JobState();

        // Temporary: Delay for 10 seconds to reduce likelihood of breaking due to DB consistency issues
        await Task.Delay(TimeSpan.FromSeconds(10));

        bool executionLockAcquired = await this.workflowProcessor.TryAcquireJobExecutionLockAsync(context.Id, context.Parameters);

        if (!executionLockAcquired)
        {
            this.logger.LogTitleIngestionEvent(LogLevel.Error, context, "Job is terminating because it was unable to acquire its execution lock.");
            context.State.StatusDetails = "Could not grab execution lock";
            return AsyncExecutionResult.TransitionTo(FailedState);
        }
        
        try
        {
            context.Parameters.Validate();
        }
        catch (ArgumentException ex)
        {
            this.logger.LogWorkflowValidationError(context.Id, context.Partition, this.JobType, ex);
            context.State.StatusDetails = $"Failed validation for {ex.ParamName} - {ex.Message}";
            return AsyncExecutionResult.TransitionTo(FailedState);
        }

        return AsyncExecutionResult.TransitionTo(InitializeProductIngestionState);
    }

    [AsyncWorkflowState(InitializeProductIngestionState)]
    public async Task<AsyncExecutionResult> InitializeProductIngestionAsync(ITitleIngestionContext context)
    {
        WorkflowSubmissionTicket jobTicket = await this.workflowProcessor.TriggerProductIngestionJobAsync(context.Parameters.ProductIngestionJobParameters, createdBy: $"TitleIngestionJob: {context.Id}");

        context.State.ChildProductIngestionJob = new ChildJobState
        {
            JobId = jobTicket.WorkflowId,
            PartitionKey = jobTicket.WorkflowPartitionKey,
            Status = JobStatus.Running
        };
        
        return AsyncExecutionResult.TransitionTo(PollProductIngestionState, this.settings.ChildJobPollingInterval);
    }

    [AsyncWorkflowState(PollProductIngestionState)]
    public async Task<AsyncExecutionResult> PollProductIngestionAsync(ITitleIngestionContext context)
    {
        Validate.IsNotNull(context.State.ChildProductIngestionJob, nameof(context.State.ChildProductIngestionJob));
        
        await this.workflowProcessor.UpdateChildJobStatusesAsync<ProductIngestion.JobParameters, ProductIngestion.JobState>(
            new[] { context.State.ChildProductIngestionJob }, 
            onSuccess: childState =>
            {
                context.State.EstimatedInstallSizeInBytes = childState.EstimatedInstallSizeInBytes;
                context.State.StreamingPackageIds = childState.StreamingPackageIds;
                context.State.XboxTitleId = childState.StoreGameAssets.FirstOrDefault()?.XboxTitleId;
            });

        if (context.State.ChildProductIngestionJob.Status == JobStatus.Running)
        {
            return AsyncExecutionResult.RetryWith(this.productIngestionJobsPollingPolicy);
        }

        // All child jobs completed (successfully or not)
        // If any child jobs fail, mark this job as failed, even though some of the child 
        // jobs may have succeeded, as not all available versions have been ingested. 
        // The operation as a whole can be retried
        if (context.State.ChildProductIngestionJob.Status != JobStatus.Succeeded)
        {
            context.State.StatusDetails = $"Child ingestion job did not succeed. Status: {context.State.ChildProductIngestionJob.Status}. " +
                                          $"Id: {context.State.ChildProductIngestionJob.JobId}. Partition: {context.State.ChildProductIngestionJob.PartitionKey}";
            return AsyncExecutionResult.TransitionTo(FailedState);
        }

        return AsyncExecutionResult.TransitionTo(string.IsNullOrWhiteSpace(context.Parameters.TitleCollection) ? SucceededState : AddTitleToCollectionState);
    }

    [AsyncWorkflowState(AddTitleToCollectionState)]
    public async Task<AsyncExecutionResult> AddTitleToCollectionAsync(ITitleIngestionContext context)
    {
        Validate.IsNotNull(context.Parameters.TitleCollection, nameof(context.Parameters.TitleCollection));

        CollectionTitle collectionTitle = new()
        {
            Id = context.Parameters.ProductIngestionJobParameters.TitleId,
            PartnerId = context.Parameters.ProductIngestionJobParameters.PartnerId,
            Platform = context.Parameters.ProductIngestionJobParameters.Platform,
            ProductId = context.Parameters.ProductIngestionJobParameters.ProductId,
            AvailableTime = DateTime.Now,
            ExpirationTime = context.Parameters.Expiry,
            FriendlyName = context.Parameters.ProductIngestionJobParameters.PackageNameOverride ?? context.Parameters.ProductIngestionJobParameters.TitleId,
            TitleCollectionId = context.Parameters.TitleCollection,
            XboxTitleId = context.State.XboxTitleId
        };
        
        try
        {
            await this.partnerRegistryClient.AddCollectionTitleAsync(collectionTitle);
        } 
        catch (Exception ex)
        {
            context.State.StatusDetails = $"Could not add title {context.Parameters.ProductIngestionJobParameters.TitleId} to collection {context.Parameters.TitleCollection}. {ex.Message}";
            return AsyncExecutionResult.TransitionTo(FailedState);
        }

        await this.SendMailerStatusNotificationAsync(context, true);
        return AsyncExecutionResult.TransitionTo(PollFirstInstallState);
    }

    [AsyncWorkflowState(PollFirstInstallState)]
    public async Task<AsyncExecutionResult> PollFirstInstallAsync(ITitleIngestionContext context)
    {
        if (context.State.StreamingPackageIds.IsNullOrEmpty())
        {
            context.State.StatusDetails = "Child product ingestion job did not return any install IDs. Cannot notify on install.";
            return AsyncExecutionResult.TransitionTo(FailedState);
        }

        // Renew the lock since this can take a while.
        await this.workflowProcessor.TryAcquireJobExecutionLockAsync(context.Id, context.Parameters);

        Id targetInstallId = ContentInstallId.Generate(context.State.StreamingPackageIds.First());
        ServerFilter serverFilter = new()
        {
            // TODO: This should eventually be replaced with an env-specific config instead of using the environment provider
            Region = this.environmentProvider.IsProd() ? GsRegionName.WestUs2 : GsRegionName.WestEurope,
            PoolId = context.Parameters.ProductIngestionJobParameters.Audiences.Any(a => a.SandboxId == XusAudience.CertSandboxId) ? "XBOX_CERT" : "XBOX_MAIN",
            SystemUpdateGroup = SystemUpdateGroup.GA,
            ServerType = ServerType.XboxV3SeriesS,
            LocalPackageId = targetInstallId
        };
        
        IReadOnlyCollection<Server> servers = await this.serverAllocatorClient.QueryServersAsync(serverFilter);
        if (servers.IsEmpty())
        {
            context.State.StatusDetails = "Install not found. Retrying.";
            return AsyncExecutionResult.RetryWith(this.allocatorInstallPollingPolicy, nextStateOnFail: NotifyInstallNotFoundState);
        }

        context.State.StatusDetails = string.Empty;
        this.logger.LogTitleIngestionEvent(LogLevel.Information, context, "Install successful");
        if (this.settings.NotifyOnInstall)
        {
            this.logger.LogTitleIngestionEvent(LogLevel.Information, context, "Sending install notification");
            await this.SendInstallNotificationAsync(context);
        }
        
        return AsyncExecutionResult.TransitionTo(SucceededState);
    }

    [AsyncWorkflowState(NotifyInstallNotFoundState)]
    public async Task<AsyncExecutionResult> NotifyInstallNotFoundAsync(ITitleIngestionContext context)
    {
        await this.SendInstallNotFoundNotificationAsync(context);
        return AsyncExecutionResult.TransitionTo(SucceededState);
    }

    [AsyncWorkflowState(SucceededState)]
    public Task<AsyncExecutionResult> CompletedAsync(ITitleIngestionContext context)
    {
        return Task.FromResult(AsyncExecutionResult.Success);
    }

    [AsyncWorkflowState(FailedState)]
    public async Task<AsyncExecutionResult> HandleJobFailureAsync(ITitleIngestionContext context)
    {
        await this.SendMailerStatusNotificationAsync(context, false);
        return AsyncExecutionResult.Fail;
    }

    public override async Task BeforeCompletingAsync(IReadOnlyJobContext<TitleIngestion.JobParameters, TitleIngestion.JobState> context, bool jobSucceeded)
    {
        await this.workflowProcessor.ReleaseJobLockAsync(context.Id, context.Parameters);
    }

    private async Task SendMailerStatusNotificationAsync(ITitleIngestionContext context, bool jobSucceeded)
    {
        if (this.settings.MailerNotificationsEnabled)
        {
            // StatusDetails being populated determines whether the job succeeded or failed
            if (jobSucceeded)
            {
                // Send success report as a DM to the user who triggered the job
                // For DMs, we should double check CreatedBy is a valid alias
                if (context.CreatedBy.EndsWith("@microsoft.com", StringComparison.CurrentCultureIgnoreCase))
                {
                    PersonalMessage message = PersonalMessage.BeginCreate()
                        .WithTitle($"Title Ingestion Job for {context.Parameters.ProductIngestionJobParameters.TitleId} completed successfully")
                        .WithSubtitle($"Title Collection: {context.Parameters.TitleCollection} | Expiry: {(context.Parameters.Expiry.HasValue ? context.Parameters.Expiry : "Empty")}")
                        .WithBody($"Report generated at {DateTimeOffset.UtcNow} UTC \n " +
                                  $"TitleId: {context.Parameters.ProductIngestionJobParameters.TitleId} \n " +
                                  $"PartnerId: {context.Parameters.ProductIngestionJobParameters.PartnerId} \n " +
                                  $"Platform: {context.Parameters.ProductIngestionJobParameters.Platform} \n " +
                                  $"ProductId: {context.Parameters.ProductIngestionJobParameters.ProductId} \n " +
                                  $"PackageNameOverride: {context.Parameters.ProductIngestionJobParameters.PackageNameOverride} \n " +
                                  $"TitleCollection: {context.Parameters.TitleCollection} \n " +
                                  $"Expiry: {(context.Parameters.Expiry.HasValue ? context.Parameters.Expiry : "Empty")}" +
                                  $"Estimated Install Size: {context.State.EstimatedInstallSizeInBytes / GB:.000GB}")
                        .Build();
                    try
                    {
                        await this.mailerClient.SendMessageToIndividualAsync(context.CreatedBy, XCloudTeams.XCloudCentralFte, message);
                    }
                    catch (Exception ex)
                    {
                        this.logger.LogTitleIngestionEvent(LogLevel.Error, context, $"Error sending success mailer notification to {context.CreatedBy}", ex);
                    }
                }
            }
            else
            {
                // Send failure report to channel
                ChannelMessage mailerMessage = ChannelMessage.BeginCreate()
                    .WithTitle($"Title Ingestion Job Failed")
                    .WithSubtitle($"TitleID: {context.Parameters.ProductIngestionJobParameters.TitleId}")
                    .WithBody(builder =>
                    {
                        builder.AddParagraph($"Report generated at {DateTimeOffset.UtcNow} UTC");
                        builder.AddParagraph($"Job status: {context.State.StatusDetails}");
                        builder.AddParagraph($"Job ID: {context.Id} | Partition: {context.Partition}");
                    })
                    .WithMentions(context.CreatedBy)
                    .Build();
                try
                {
                    await this.mailerClient.SendMessageToChannelAsync(XCloudTeamsChannels.ServicesDev_ContentNotifications, mailerMessage);
                }
                catch (Exception ex)
                {
                    this.logger.LogTitleIngestionEvent(LogLevel.Error, context, "Error sending failure report via mailer", ex);
                }
            }
        }
    }

    private async Task SendInstallNotificationAsync(ITitleIngestionContext context)
    {
        PersonalMessage message = PersonalMessage.BeginCreate()
            .WithTitle($"Install completed for {context.Parameters.ProductIngestionJobParameters.TitleId}!")
            .WithSubtitle($"Estimated Install Size: {context.State.EstimatedInstallSizeInBytes / GB:.000GB}")
            .WithBody($"Copies of {context.Parameters.ProductIngestionJobParameters.TitleId} have been found. It is now ready to be played.")
            .Build();

        try
        {
            await this.mailerClient.SendMessageToIndividualAsync(this.environmentProvider.IsProd() ? this.settings.InstallNotificationAlias : context.CreatedBy,  XCloudTeams.XCloudCentralFte, message);
        }
        catch (Exception ex)
        {
            this.logger.LogTitleIngestionEvent(LogLevel.Error, context, "Error sending install report via mailer", ex);
        }
    }

    private async Task SendInstallNotFoundNotificationAsync(ITitleIngestionContext context)
    {
        ChannelMessage message = ChannelMessage.BeginCreate()
            .WithTitle($"Title Install not found for {context.Parameters.ProductIngestionJobParameters.TitleId}!")
            .WithBody(builder =>
            {
                builder.AddParagraph($"Report generated at {DateTimeOffset.UtcNow} UTC");
                builder.AddParagraph($"Job status: {context.State.StatusDetails}");
                builder.AddParagraph($"Job ID: {context.Id} | Partition: {context.Partition}");
            })
            .WithMentions(context.CreatedBy)
            .Build();

        try
        {
            await this.mailerClient.SendMessageToChannelAsync(XCloudTeamsChannels.ServicesDev_ContentNotifications, message);
        }
        catch (Exception ex)
        {
            this.logger.LogTitleIngestionEvent(LogLevel.Error, context, "Error sending install not found report via mailer", ex);
        }
    }
}
