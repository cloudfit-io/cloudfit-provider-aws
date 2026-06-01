# cloudfit-provider-aws

[![Status: Planned](https://img.shields.io/badge/status-planned-orange)](https://github.com/cloudfit-io/cloudfit-provider-aws)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

**AWS EC2 provider for [cloudfit-core](https://github.com/cloudfit-io/cloudfit-core).**

> **Status: not built yet.** This repository is a public tracker for the AWS provider work. Watch / star to get notified when v0.1.0 ships.

---

## What this will be

A `cloudfit.providers.base.Provider` implementation that fetches the AWS EC2 catalog and on-demand pricing and normalizes them into the cloudfit `MachineType` schema, so cloudfit-core can score AWS instances the same way it scores GCP.

When complete, the typical usage will look like:

```python
from cloudfit_provider_aws import AWSProvider
from cloudfit import rank, WorkloadProfile

provider = AWSProvider(region="us-east-1")
candidates = provider.fetch_instances()

profile = WorkloadProfile(vcpu=32, ram_gb=128, optimize_for="balanced")
ranked = rank(profile, candidates)
```

Same shape as [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp), which already exists. The contract is documented in [cloudfit-core's CONTRIBUTING.md](https://github.com/cloudfit-io/cloudfit-core/blob/main/CONTRIBUTING.md).

---

## Scope for v0.1.0

| Feature | In v0.1.0? |
|---|---|
| EC2 `DescribeInstanceTypes` catalog ingestion | yes |
| AWS Pricing API integration (on-demand) | yes |
| Multi-region fetch (`fetch_instances_all_regions`) | yes |
| Normalizer into cloudfit `MachineType` schema | yes |
| Status / deprecation handling | yes |
| Spot pricing | no, deferred to v0.2 |
| Reserved Instances / Savings Plans modeling | no, separate roadmap item in cloudfit-core |
| GPU type discrimination beyond VRAM | no, depends on cloudfit-core v0.3 work |

---

## Why "planned" not "in progress"

`cloudfit-core` and `cloudfit-provider-gcp` shipped first because GCP was the home turf. Validating the scoring engine and the provider plugin contract on a single cloud lets us avoid rebuilding the abstraction once we add AWS.

AWS Pricing API is verbose enough to warrant focused work (roughly 4 to 6 weeks part-time), so this provider is the next discrete milestone after the launch of cloudfit-core v0.2 and cloudfit-api v0.2.

If you'd find it useful before then, please file an issue or comment on the meta-issue once it's open: that signal directly affects the priority.

---

## How to follow progress

- **Watch this repository** for the first commit
- **Star [cloudfit-io](https://github.com/cloudfit-io)** to follow the broader org
- **Subscribe to the meta-issue** (once filed) for milestone updates
- **Read the project landing page** at [cloudfit-io.github.io](https://cloudfit-io.github.io) for the current state of the ecosystem

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

## Related

- [`cloudfit-core`](https://github.com/cloudfit-io/cloudfit-core): Scoring engine. The thing this provider plugs into.
- [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp): GCP equivalent. Use it as the reference implementation.
- [`cloudfit-api`](https://github.com/cloudfit-io/cloudfit-api): REST API service. Will pick up AWS instances automatically once this provider ships and a snapshot is generated.
- [`cloudfit-ui`](https://github.com/cloudfit-io/cloudfit-ui): Gradio demo UI. Same story: AWS instances appear once the provider ships.
