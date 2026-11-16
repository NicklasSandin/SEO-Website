from __future__ import annotations

from typing import Mapping

from .base import RankProvider
from .dataforseo import DataForSEOClient
from .sample import SampleProvider


def provider_mode(config: Mapping) -> str:
    """'dataforseo' or 'sample', resolved from RANK_PROVIDER and the presence of credentials."""
    choice = config["RANK_PROVIDER"]
    if choice == "auto":
        return "dataforseo" if config.get("DATAFORSEO_LOGIN") and config.get("DATAFORSEO_PASSWORD") else "sample"
    return choice


def build_provider(config: Mapping) -> RankProvider:
    if provider_mode(config) == "sample":
        return SampleProvider()
    return DataForSEOClient(
        config["DATAFORSEO_LOGIN"],
        config["DATAFORSEO_PASSWORD"],
        base_url=config["DATAFORSEO_BASE_URL"],
        timeout=config["DATAFORSEO_TIMEOUT_SECONDS"],
        max_retries=config["DATAFORSEO_MAX_RETRIES"],
    )
