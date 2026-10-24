# cloudfit-provider-aws

[![PyPI version](https://img.shields.io/pypi/v/cloudfit-provider-aws)](https://pypi.org/project/cloudfit-provider-aws/)
[![Tests](https://github.com/cloudfit-io/cloudfit-provider-aws/actions/workflows/ci.yml/badge.svg)](https://github.com/cloudfit-io/cloudfit-provider-aws/actions)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

**AWS EC2 provider plugin for [cloudfit-core](https://github.com/cloudfit-io/cloudfit-core).**

Reads AWS's public EC2 price list and normalizes every Linux instance type into `MachineType` objects that `cloudfit-core` understands, with on-demand and 1-year reserved prices, each family's `perf_factor`, and each GPU's model and memory. **No AWS account or credentials needed.**

---

## Installation

```bash
pip install cloudfit-provider-aws
```

Requires Python 3.10 or newer (CI tests 3.10 through 3.14) and `cloudfit-core>=0.9.1`. The only dependency is cloudfit-core: no AWS SDK.

---

## Quick start

```python
from cloudfit import WorkloadProfile, rank
from cloudfit_provider_aws import AWSProvider

candidates = AWSProvider().fetch_instances(region="us-east-1")

profile = WorkloadProfile(vcpu=32, ram_gb=128, archetype="cpu", optimize_for="balanced")
for result in rank(profile, candidates)[:5]:
    m = result.instance
    print(f"{m.id:<20} score={result.score:.3f}  ${m.price_hr:.4f}/hr  {result.reason}")
```

Output from a live run (2026-10-23):

```
m6i.8xlarge          score=1.000  $1.5360/hr  Led by performance fit.
m6id.8xlarge         score=0.999  $1.8984/hr  Led by performance fit.
m6in.8xlarge         score=0.999  $2.2277/hr  Led by performance fit.
m6idn.8xlarge        score=0.998  $2.5459/hr  Led by performance fit.
m7g.8xlarge          score=0.990  $1.3056/hr  Led by performance fit; m7g.8xlarge cores ~10% faster than baseline.
```

The same script is [`examples/recommend.py`](examples/recommend.py).

---

## Where the data comes from

AWS publishes each region's full EC2 offer as a [public price list](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-ppslong.html) file. Every row is one price term and also carries the instance's attributes, so one file gives both the catalog and its prices. The files are large (about 300 MB for us-east-1), so the provider streams them row by row; a region takes roughly 15 to 20 seconds and is cached on the provider instance. Fetch on a schedule, never on a request path.

Each `MachineType` carries:

| Field | Source |
|---|---|
| `vcpu`, `ram_gb` | vCPU and memory attributes |
| `price_hr` | on-demand Linux price, shared tenancy |
| `cud_1yr_price_hr` | 1-year standard No Upfront reserved price (cloudfit-core's 1-year commitment mode); unset when AWS offers none |
| `local_ssd_tb` | instance store SSDs (HDD and EBS-only count as 0) |
| `gpu_count`, `gpu_vram_gb`, `gpu_type` | GPU attributes; model and per-GPU memory from a per-family table (below) |
| `status` | `active`, or `deprecated` for previous-generation types |
| `perf_factor` | cloudfit-core's `AWS_PERF_FACTORS`, via `perf_factor_for` |

**GPUs.** The price list has no GPU model column, and its GPU memory column is the total across GPUs for some families and per GPU for others. So known families (p2 through p6-b200, g2 through g6e) take their model and per-GPU memory from a table: a p4d is 8 × A100 40 GB, not 8 GPUs with 320 GB each. A GPU family newer than the table keeps its GPU count, splits the column's memory across the GPUs, and has no model, so cloudfit-core scores it on memory fit instead of throughput.

**Previous generations** are `deprecated`, which lowers their availability score; AWS keeps them running, so none is ever `tombstoned`.

---

## Not included

| | Why |
|---|---|
| Spot prices | They vary by availability zone and by hour, and are not in the public price list. Planned for a later release. |
| Savings Plans, 3-year and partial or all upfront reservations | cloudfit-core has one 1-year commitment price per instance; 1-year No Upfront is the closest match. |
| Windows, RHEL, SUSE, and other paid operating systems | Linux only, like the GCP provider. |
| Inferentia, Trainium, Gaudi, FPGA, video transcode, and Mac instances | cloudfit does not model these accelerators (the price list reports some of them as GPUs). |
| Fractional-GPU instances (g6f, gr6f) | `MachineType` has a whole-number GPU count. |
| Local Zones, Wavelength, GovCloud | Not in `AWS_REGIONS`; pass a region code directly to try one. |

---

## Snapshots

[`examples/generate_snapshot.py`](examples/generate_snapshot.py) writes a JSON snapshot in the same format as cloudfit-provider-gcp's, for the five `SNAPSHOT_REGIONS` (us-east-1, us-east-2, us-west-2, eu-west-1, ap-southeast-1) by default. It takes about a minute and writes about 6,000 instance types; it fails without writing anything if any region comes back empty.

```bash
python examples/generate_snapshot.py --output aws_snapshot.json
```

Rows are sorted by region and instance type, so a refresh diff shows only real changes.

The [`refresh-snapshot`](.github/workflows/refresh-snapshot.yml) workflow rebuilds the snapshot bundled by cloudfit-api and cloudfit-ui every Monday at 07:00 UTC and opens a pull request in each, where CI runs on it. It needs no AWS credentials, only a `SNAPSHOT_TOKEN` secret that can open pull requests in those two repos (see the comments in the workflow file).

`fetch_instances_all_regions()` covers all 34 regions in `AWS_REGIONS` (about 30 downloads), or the list you pass.

---

## Repository structure

```
cloudfit-provider-aws/
├── README.md
├── CHANGELOG.md             # release notes; GitHub Releases are built from it
├── CITATION.cff
├── pyproject.toml
├── Makefile                 # version bump, tag, test, lint, build
├── LICENSE
├── .gitignore
├── .github/
│   ├── dependabot.yml       # monthly GitHub Actions updates
│   ├── ISSUE_TEMPLATE/      # AWS coverage requests and scope feedback
│   └── workflows/
│       ├── ci.yml           # lint, mypy --strict, tests; PyPI publish and release on tags
│       └── refresh-snapshot.yml   # weekly snapshot PRs to cloudfit-api and cloudfit-ui
│
├── cloudfit_provider_aws/
│   ├── __init__.py          # exports AWSProvider, parse_price_list, regions
│   ├── provider.py          # AWSProvider: implements the Provider base class
│   ├── pricelist.py         # streams and filters the public price list CSV
│   ├── normalizer.py        # price list attributes → MachineType, GPU table
│   ├── regions.py           # AWS_REGIONS and SNAPSHOT_REGIONS
│   └── py.typed             # ships type hints (PEP 561)
│
├── examples/
│   ├── recommend.py         # live fetch → rank
│   └── generate_snapshot.py # build a snapshot for the five snapshot regions
│
└── tests/
    ├── test_pricelist.py    # parsing and filtering, against recorded rows
    ├── test_normalizer.py   # field mapping, GPUs, storage, exclusions
    ├── test_provider.py     # caching, region failures, ranking with cloudfit-core
    └── fixtures/
        └── us-east-1-sample.csv   # recorded slice of the us-east-1 price list
```

---

## Related

- [`cloudfit-core`](https://github.com/cloudfit-io/cloudfit-core): scoring engine. The thing this provider plugs into.
- [`cloudfit-provider-gcp`](https://github.com/cloudfit-io/cloudfit-provider-gcp): the GCP equivalent.
- [`cloudfit-api`](https://github.com/cloudfit-io/cloudfit-api) and [`cloudfit-ui`](https://github.com/cloudfit-io/cloudfit-ui): serve this provider's AWS snapshot alongside the GCP one.

## License

Apache 2.0. See [LICENSE](LICENSE).
