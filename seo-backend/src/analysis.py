"""Turns provider calls into one normalised analysis payload.

The payload is what gets stored on `AnalysisRun.result` and what the report generator reads.
Ranks are positions among Google's organic results; `None` means "not found within the first
`serp_depth` results", which is not the same as "not ranking at all".
"""
from __future__ import annotations

from typing import Any

from .domains import domain_matches
from .providers import (
    SAMPLE_LABEL,
    ProviderAuthError,
    ProviderError,
    ProviderPaymentError,
    ProviderRateLimitError,
    RankProvider,
)

TOP_RESULTS_KEPT = 10
COMPETITOR_WINDOW = 10  # a domain is a competitor on a keyword if it is in this many top results
MAX_COMPETITORS = 10


def data_label(is_sample: bool, provider: str) -> str:
    if is_sample:
        return SAMPLE_LABEL
    return f"Data from {provider}"


def run_analysis(
    provider: RankProvider,
    *,
    website_url: str,
    domain: str,
    keywords: list[str],
    location_name: str,
    language_code: str,
    depth: int,
    previous_ranks: dict[str, int | None] | None = None,
) -> dict[str, Any]:
    previous_ranks = previous_ranks or {}
    warnings: list[str] = []
    keyword_rows: list[dict[str, Any]] = []

    for keyword in keywords:
        serp = provider.get_serp(
            keyword,
            location_name=location_name,
            language_code=language_code,
            depth=depth,
            target_domain=domain,
        )
        own = next((item for item in serp.items if domain_matches(item.domain, domain)), None)
        keyword_rows.append(
            {
                "keyword": keyword,
                "rank": own.rank if own else None,
                "ranking_url": own.url if own else None,
                "previous_rank": previous_ranks.get(keyword),
                "search_volume": None,
                "difficulty": None,
                "top_results": [
                    {"rank": item.rank, "domain": item.domain, "url": item.url, "title": item.title}
                    for item in serp.items[:TOP_RESULTS_KEPT]
                ],
                "_window": [(item.rank, item.domain) for item in serp.items if item.rank <= COMPETITOR_WINDOW],
            }
        )

    try:
        metrics = provider.get_keyword_metrics(keywords, location_name=location_name, language_code=language_code)
        warnings.extend(metrics.warnings)
        for row in keyword_rows:
            found = metrics.metrics.get(row["keyword"].lower())
            if found:
                row["search_volume"] = found.search_volume
                row["difficulty"] = found.difficulty
    except (ProviderAuthError, ProviderPaymentError, ProviderRateLimitError):
        raise
    except ProviderError as exc:
        warnings.append(f"Search volume and difficulty are unavailable: {exc}")

    competitors = _competitors(keyword_rows, domain)
    for row in keyword_rows:
        del row["_window"]

    try:
        audit = provider.audit_page(website_url)
        technical_audit: dict[str, Any] = {
            "available": True,
            "url": audit.url,
            "onpage_score": audit.onpage_score,
            "issues": [
                {"id": i.id, "severity": i.severity, "title": i.title, "detail": i.detail} for i in audit.issues
            ],
        }
    except (ProviderAuthError, ProviderPaymentError, ProviderRateLimitError):
        raise
    except ProviderError as exc:
        technical_audit = {"available": False, "url": website_url, "onpage_score": None, "issues": [], "reason": str(exc)}
        warnings.append(f"Technical audit is unavailable: {exc}")

    return {
        "target_domain": domain,
        "serp_depth": depth,
        "location_name": location_name,
        "language_code": language_code,
        "provider": provider.name,
        "is_sample": provider.is_sample,
        "data_label": data_label(provider.is_sample, provider.name),
        "keywords": keyword_rows,
        "competitors": competitors,
        "technical_audit": technical_audit,
        "warnings": warnings,
    }


def _competitors(keyword_rows: list[dict[str, Any]], own_domain: str) -> list[dict[str, Any]]:
    """Domains other than the site's own that appear in the top results of its keywords.

    Ordered by how many of the keywords the domain appears for, then by average position over
    those keywords (lower is better).
    """
    seen: dict[str, list[tuple[str, int]]] = {}
    for row in keyword_rows:
        counted: set[str] = set()  # one appearance per keyword, at the domain's best position
        for rank, domain in sorted(row["_window"]):
            if domain_matches(domain, own_domain) or domain in counted:
                continue
            counted.add(domain)
            seen.setdefault(domain, []).append((row["keyword"], rank))
    competitors = []
    for domain, appearances in seen.items():
        ranks = [rank for _, rank in appearances]
        competitors.append(
            {
                "domain": domain,
                "keywords_count": len(appearances),
                "average_rank": round(sum(ranks) / len(ranks), 1),
                "best_rank": min(ranks),
                "keywords": [{"keyword": kw, "rank": rank} for kw, rank in appearances],
            }
        )
    competitors.sort(key=lambda c: (-c["keywords_count"], c["average_rank"], c["domain"]))
    return competitors[:MAX_COMPETITORS]
