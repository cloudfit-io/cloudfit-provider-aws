"""cloudfit-provider-aws: AWS EC2 provider for cloudfit-core."""

from .pricelist import parse_price_list
from .provider import AWSProvider
from .regions import AWS_REGIONS, SNAPSHOT_REGIONS

__version__ = "0.1.1"
__author__  = "Chaitanya Krishna Kasaraneni"
__license__ = "Apache-2.0"

__all__ = ["AWSProvider", "parse_price_list", "AWS_REGIONS", "SNAPSHOT_REGIONS"]
