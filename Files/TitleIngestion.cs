// <copyright file="TitleIngestion.cs" company="Microsoft">
// Copyright (c) Microsoft. All rights reserved.
// Internal use only.
// </copyright>

namespace Microsoft.GameStreaming.Services.ContentCatalog.Common.Contracts.Workflows;

using Microsoft.GameStreaming.Services.ContentCatalog.Common.Contracts.Workflows.Abstractions;
using Microsoft.GameStreaming.Services.ContentCatalog.Common.Contracts.Workflows.Legacy;

/// <summary>
/// Contains the job parameters, state, and constants for the title ingestion workflow.
/// </summary>
public static class TitleIngestion
{
    /// <summary>
    /// The job type identifier for title ingestion workflows.
    /// </summary>
    public const string JobType = "TitleIngestion";

    /// <summary>
    /// The queue name used for title ingestion workflow messages.
    /// </summary>
    public static readonly string QueueName = JobType.ToLowerInvariant();

    /// <summary>
    /// Represents the parameters required to start a title ingestion job.
    /// </summary>
    /// <param name="ProductIngestionJobParameters">The nested product ingestion parameters for this title.</param>
    /// <param name="TitleCollection">The optional title collection identifier.</param>
    /// <param name="Expiry">The optional expiry date for the title collection.</param>
    public record JobParameters(ProductIngestion.JobParameters ProductIngestionJobParameters, Id? TitleCollection, DateTime? Expiry) : IIngestionParameters
    {
        /// <inheritdoc/>
        /// <remarks>
        /// Adding a prefix to the lock string is necessary or else the lockManager in the JobLockProcessor and TitleJobLockProcessor will still collide
        /// </remarks>
        public Id GetLockId() => $"{JobType}_{this.ProductIngestionJobParameters.PartnerId}_{this.ProductIngestionJobParameters.TitleId}";

        /// <inheritdoc/>
        public string GetPartitionKey() => this.ProductIngestionJobParameters.GetPartitionKey();

        /// <inheritdoc/>
        public string GetJobType() => JobType;

        /// <inheritdoc/>
        public string GetQueueName() => QueueName;

        /// <inheritdoc/>
        public void Validate()
        {
            this.ProductIngestionJobParameters.Validate();
            if (!string.IsNullOrWhiteSpace(this.TitleCollection))
            {
                if (this.Expiry.HasValue && this.Expiry.Value < DateTime.Now)
                {
                    throw new ArgumentException($"The expiry date {this.Expiry.Value} is in the past.", nameof(this.Expiry));
                }
                
                CommonValidate.IsNotEmptyOrWhitespace(this.ProductIngestionJobParameters.PackageNameOverride, nameof(this.ProductIngestionJobParameters.PackageNameOverride));
            }
        }
    }

    /// <summary>
    /// Represents the persisted state of a title ingestion job.
    /// </summary>
    public class JobState
    {
        /// <summary>
        /// Gets or sets the child product ingestion job state.
        /// </summary>
        public ChildJobState? ChildProductIngestionJob { get; set; }

        /// <summary>
        /// Gets or sets the list of streaming package identifiers produced by the ingestion.
        /// </summary>
        public IList<Guid>? StreamingPackageIds { get; set; }

        /// <summary>
        /// Gets or sets the Xbox title identifier.
        /// </summary>
        public uint? XboxTitleId { get; set; }

        /// <summary>
        /// Gets or sets a human-readable status message describing the job outcome.
        /// </summary>
        public string StatusDetails { get; set; } = string.Empty;

        /// <summary>
        /// Gets or sets the estimated install size of the title in bytes.
        /// </summary>
        public long EstimatedInstallSizeInBytes { get; set; }
    }
}
