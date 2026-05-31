# Changelog

All notable changes to `cloudfit-provider-aws` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Planning phase

No code yet. See [README](README.md) for the planned v0.1.0 scope and how to influence it.

### Planned for v0.1.0
- `AWSProvider` implementing the cloudfit `Provider` interface from `cloudfit-core`.
- EC2 `DescribeInstanceTypes` catalog ingestion.
- AWS Pricing API integration for on-demand pricing.
- Multi-region fetch (`fetch_instances_all_regions`).
- Normalizer into the cloudfit `MachineType` schema.
- Instance status / deprecation handling.

### Deferred
- Spot pricing (v0.2).
- Reserved Instances / Savings Plans modeling (separate roadmap item in cloudfit-core).
- GPU type discrimination beyond VRAM (depends on cloudfit-core v0.3).
