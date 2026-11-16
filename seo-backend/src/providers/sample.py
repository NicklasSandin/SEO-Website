"""Fixture provider used when no DataForSEO credentials are configured.

EVERYTHING this module returns is invented. It exists so the product can be run, clicked through
and tested without credentials or network access. The values are derived from a hash of the
inputs so they are stable between runs; they say nothing about any real website. The API and the
UI mark every result that comes from here as SAMPLE DATA, and the competitor domains use the
reserved ``.example`` top-level name (RFC 2606) so they can never be real sites.
"""
from __future__ import annotations

import hashlib

from ..domains import normalize_host
from .base import AuditIssue, KeywordMetrics, MetricsResult, OrganicResult, PageAudit, RankProvider, SerpResult

SAMPLE_LABEL = "SAMPLE DATA - invented fixture values, not real search results"

_POOL_SIZE = 100  # the SERP depth limit; every position can get a distinct fixture domain

_SAMPLE_ISSUES = [
    ("no_description", "warning", "Sample finding: missing meta description", "Sample data. This is not a real finding."),
    ("no_h1_tag", "warning", "Sample finding: no H1 heading", "Sample data. This is not a real finding."),
    ("no_image_alt", "warning", "Sample finding: images without alt text", "Sample data. This is not a real finding."),
    ("high_loading_time", "warning", "Sample finding: slow loading time", "Sample data. This is not a real finding."),
    ("title_too_long", "warning", "Sample finding: long title tag", "Sample data. This is not a real finding."),
    ("no_favicon", "info", "Sample finding: no favicon", "Sample data. This is not a real finding."),
    ("is_http", "critical", "Sample finding: served over HTTP", "Sample data. This is not a real finding."),
]


def _hash(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


class SampleProvider(RankProvider):
    name = "sample"
    is_sample = True

    def get_serp(
        self,
        keyword: str,
        *,
        location_name: str,
        language_code: str,
        depth: int,
        target_domain: str | None = None,
    ) -> SerpResult:
        base = _hash("serp", keyword.lower(), location_name, language_code)
        # Fixture competitors: low numbers tend to rank higher, so a few of them recur across keywords.
        order = sorted(range(_POOL_SIZE), key=lambda i: i * 4 + _hash("order", keyword.lower(), str(i)) % 60)
        target = normalize_host(target_domain)
        # The target site lands at a stable position; about a third of the time it is outside the depth.
        target_rank = 1 + base % (depth + depth // 2) if target else None
        if target_rank is not None and target_rank > depth:
            target_rank = None

        items: list[OrganicResult] = []
        pool = iter(order)
        for rank in range(1, depth + 1):
            domain = target if target_rank == rank else f"sample-competitor-{next(pool) + 1:02d}.example"
            items.append(
                OrganicResult(
                    rank=rank,
                    rank_absolute=rank,
                    domain=domain,
                    url=f"https://{domain}/sample-page",
                    title=f"Sample result {rank} for '{keyword}' (sample data)",
                )
            )
        return SerpResult(keyword=keyword, items=items)

    def get_keyword_metrics(
        self, keywords: list[str], *, location_name: str, language_code: str
    ) -> MetricsResult:
        metrics = {}
        for kw in keywords:
            h = _hash("metrics", kw.lower(), location_name)
            metrics[kw.lower()] = KeywordMetrics(search_volume=(50 + h % 500) * 10, difficulty=10 + (h >> 16) % 81)
        return MetricsResult(metrics=metrics, warnings=[])

    def audit_page(self, url: str) -> PageAudit:
        h = _hash("audit", url)
        count = 2 + h % 3
        start = (h >> 8) % len(_SAMPLE_ISSUES)
        picked = [_SAMPLE_ISSUES[(start + i) % len(_SAMPLE_ISSUES)] for i in range(count)]
        order = {"critical": 0, "warning": 1, "info": 2}
        issues = sorted((AuditIssue(*item) for item in picked), key=lambda i: (order[i.severity], i.id))
        return PageAudit(url=url, onpage_score=float(50 + (h >> 20) % 41), issues=issues)
