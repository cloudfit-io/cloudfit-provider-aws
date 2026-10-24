# Changelog

All notable changes to `cloudfit-provider-aws` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No unreleased changes._

## [0.1.0] - 2026-10-23

First release.

### Added
- `AWSProvider` implementing cloudfit-core's `Provider` interface: `fetch_instances(region)`, `fetch_instances_all_regions(regions=None)`, and `get_pricing(instance_id, region)`. A fetched region is cached on the provider.
- Catalog and prices from AWS's public EC2 price list, streamed row by row: no AWS account, credentials, or SDK needed. Every Linux instance type on shared tenancy, with the on-demand price and the 1-year standard No Upfront reserved price as `cud_1yr_price_hr`.
- `perf_factor` from cloudfit-core's `AWS_PERF_FACTORS`; GPU model and per-GPU memory from a per-family table, since the price list has no model column and reports memory inconsistently; local instance-store SSD capacity; previous-generation types marked `deprecated`.
- `parse_price_list` for parsing a price list file you already have, `AWS_REGIONS` (34 commercial regions), and `SNAPSHOT_REGIONS` (five).
- `examples/recommend.py` (live fetch and rank) and `examples/generate_snapshot.py` (writes a snapshot in cloudfit-provider-gcp's format and fails without writing if any region is empty).

### Notes
- Not included: spot prices (they vary by zone and hour and are not in the public price list), Savings Plans and other reservation terms, non-Linux operating systems, non-GPU accelerators (Inferentia, Trainium, Gaudi, FPGA), Mac, and fractional-GPU instances.
- The planning-phase scope listed EC2 `DescribeInstanceTypes` and the AWS Pricing API, which both need credentials. The public price list carries the same attributes and prices without them, so this release uses it instead.
