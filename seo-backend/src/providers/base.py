"""The rank-data provider interface.

Two implementations exist: `DataForSEOClient` (real data, needs credentials) and
`SampleProvider` (fixed fixture data, always labelled as sample). Everything above this layer
(analysis, reports, API, UI) only sees the dataclasses below and the `is_sample` flag.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ProviderError(Exception):
    """A rank-data provider call failed. The message is safe to show to a user."""

    def __init__(self, message: str, *, code: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class ProviderAuthError(ProviderError):
    """The provider rejected the configured credentials."""


class ProviderPaymentError(ProviderError):
    """The provider account has no balance, or a cost limit was hit."""


class ProviderRateLimitError(ProviderError):
    """The provider's rate or concurrency limit was hit, even after retries."""

    def __init__(self, message: str, *, code: int | None = None, retry_after: float | None = None):
        super().__init__(message, code=code, retryable=True)
        self.retry_after = retry_after


@dataclass(frozen=True)
class OrganicResult:
    rank: int  # position among organic results (DataForSEO `rank_group`)
    rank_absolute: int | None
    domain: str
    url: str
    title: str


@dataclass(frozen=True)
class SerpResult:
    keyword: str
    items: list[OrganicResult] = field(default_factory=list)


@dataclass(frozen=True)
class KeywordMetrics:
    search_volume: int | None = None
    difficulty: int | None = None


@dataclass(frozen=True)
class MetricsResult:
    metrics: dict[str, KeywordMetrics] = field(default_factory=dict)  # keyed by lower-case keyword
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditIssue:
    id: str
    severity: str  # critical | warning | info
    title: str
    detail: str


@dataclass(frozen=True)
class PageAudit:
    url: str
    onpage_score: float | None
    issues: list[AuditIssue] = field(default_factory=list)


class RankProvider(ABC):
    name: str = "provider"
    is_sample: bool = False

    @abstractmethod
    def get_serp(
        self,
        keyword: str,
        *,
        location_name: str,
        language_code: str,
        depth: int,
        target_domain: str | None = None,
    ) -> SerpResult:
        """Organic Google results for one keyword.

        `target_domain` is a hint that only the sample provider uses (to place the site in its
        fixture results). Real providers ignore it and return whatever Google shows.
        """

    @abstractmethod
    def get_keyword_metrics(
        self, keywords: list[str], *, location_name: str, language_code: str
    ) -> MetricsResult:
        """Monthly search volume and keyword difficulty. Partial failures become `warnings`."""

    @abstractmethod
    def audit_page(self, url: str) -> PageAudit:
        """On-page technical checks for one URL."""
