// <copyright file="ProductIngestionWorkflow.cs" company="Microsoft">
// Copyright (c) Microsoft. All rights reserved.
// Internal use only.
// </copyright>

namespace Microsoft.GameStreaming.Services.ContentCatalog.Ingestion.Core.Workflows;

using Microsoft.GameStreaming.Services.Common;
using Microsoft.GameStreaming.Services.Common.Content.Ids;
using Microsoft.GameStreaming.Services.Common.Ids;
using Microsoft.GameStreaming.Services.ContentCatalog.Common.Contracts.Workflows.Abstractions;

public static class ProductIngestionWorkflow
{
    public record JobParameters(Id PartnerId, Id ProductId, Id Platform) : IIngestionParameters
    {
        public IReadOnlyCollection<XusAudience> Audiences { get; init; } = Array.Empty<XusAudience>();

        public string? PackageNameOverride { get; init; }

        public string? PackageDescriptionOverride { get; init; }

        public Id GetLockId() => $"{this.ProductId}";

        public string GetJobType() => throw new NotImplementedException();

        public string GetPartitionKey() => throw new NotImplementedException();

        public string GetQueueName() => throw new NotImplementedException();

        public void Validate()
        {
            CommonValidate.IsNotEmptyOrWhitespace(this.PartnerId, nameof(this.PartnerId));
            CommonValidate.IsNotEmptyOrWhitespace(this.ProductId, nameof(this.ProductId));
            CommonValidate.IsNotEmptyOrWhitespace(this.Platform, nameof(this.Platform));

            if (this.Platform != ServerPlatform.PC && this.Platform != ServerPlatform.Xbox)
            {
                throw new ArgumentException($"Unsupported platform {this.Platform}", nameof(this.Platform));
            }
        }
    }
}
