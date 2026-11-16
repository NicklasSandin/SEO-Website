import pytest

from src.analysis import run_analysis
from src.providers import (
    AuditIssue,
    KeywordMetrics,
    MetricsResult,
    OrganicResult,
    PageAudit,
    ProviderAuthError,
    ProviderError,
    RankProvider,
    SampleProvider,
    SerpResult,
)

KW = dict(location_name="Sweden", language_code="sv", depth=20)


class StubProvider(RankProvider):
    name = "stub"
    is_sample = False

    def __init__(self, serps, metrics=None, audit=None):
        self.serps, self._metrics, self._audit = serps, metrics, audit

    def get_serp(self, keyword, *, location_name, language_code, depth, target_domain=None):
        return SerpResult(keyword, [OrganicResult(rank, rank, domain, f"https://{domain}/", "") for rank, domain in self.serps[keyword]])

    def get_keyword_metrics(self, keywords, *, location_name, language_code):
        if isinstance(self._metrics, Exception):
            raise self._metrics
        return self._metrics or MetricsResult()

    def audit_page(self, url):
        if isinstance(self._audit, Exception):
            raise self._audit
        return self._audit or PageAudit(url, 90.0, [])


def analyze(provider, keywords, **extra):
    return run_analysis(provider, website_url="https://example.org", domain="example.org", keywords=keywords, **{**KW, **extra})


def test_rank_is_found_for_the_domain_and_its_subdomains_but_not_lookalikes():
    provider = StubProvider(
        {
            "a": [(1, "rival.se"), (2, "blog.example.org"), (3, "example.org")],
            "b": [(1, "notexample.org"), (2, "example.org.evil.se")],
        }
    )
    result = analyze(provider, ["a", "b"])
    by_kw = {k["keyword"]: k for k in result["keywords"]}
    assert by_kw["a"]["rank"] == 2 and by_kw["a"]["ranking_url"] == "https://blog.example.org/"
    assert by_kw["b"]["rank"] is None  # lookalike domains must not count as the site


def test_competitors_exclude_own_domain_count_once_per_keyword_and_sort():
    provider = StubProvider(
        {
            "a": [(1, "big.se"), (2, "big.se"), (3, "example.org"), (4, "small.se")],
            "b": [(1, "small.se"), (2, "big.se")],
            "c": [(1, "other.se")],
        }
    )
    result = analyze(provider, ["a", "b", "c"])
    competitors = {c["domain"]: c for c in result["competitors"]}
    assert "example.org" not in competitors
    assert competitors["big.se"]["keywords_count"] == 2  # two results on one keyword still count once
    assert competitors["big.se"]["average_rank"] == 1.5 and competitors["big.se"]["best_rank"] == 1
    assert competitors["small.se"]["average_rank"] == 2.5
    assert [c["domain"] for c in result["competitors"]][:2] == ["big.se", "small.se"]


def test_results_beyond_the_top_ten_are_not_competitors():
    provider = StubProvider({"a": [(i, f"site{i}.se") for i in range(1, 16)]})
    result = analyze(provider, ["a"])
    assert {c["domain"] for c in result["competitors"]} == {f"site{i}.se" for i in range(1, 11)}


def test_metrics_and_previous_ranks_are_attached():
    provider = StubProvider(
        {"a": [(4, "example.org")]},
        metrics=MetricsResult({"a": KeywordMetrics(search_volume=500, difficulty=33)}, warnings=["partial"]),
    )
    result = analyze(provider, ["a"], previous_ranks={"a": 9})
    row = result["keywords"][0]
    assert (row["rank"], row["previous_rank"], row["search_volume"], row["difficulty"]) == (4, 9, 500, 33)
    assert result["warnings"] == ["partial"]


def test_metrics_failure_and_audit_failure_are_warnings_not_errors():
    provider = StubProvider({"a": [(1, "example.org")]}, metrics=ProviderError("boom"), audit=ProviderError("nope"))
    result = analyze(provider, ["a"])
    assert result["keywords"][0]["rank"] == 1
    assert result["technical_audit"]["available"] is False
    assert len(result["warnings"]) == 2


def test_auth_errors_abort_the_whole_run():
    provider = StubProvider({"a": [(1, "example.org")]}, metrics=ProviderAuthError("rejected"))
    with pytest.raises(ProviderAuthError):
        analyze(provider, ["a"])


def test_payload_is_labelled_with_the_provider_and_sample_flag():
    real = analyze(StubProvider({"a": []}), ["a"])
    assert real["is_sample"] is False and real["provider"] == "stub" and "SAMPLE" not in real["data_label"]
    sample = analyze(SampleProvider(), ["boiler repair", "plumber"])
    assert sample["is_sample"] is True and sample["provider"] == "sample"
    assert sample["data_label"].startswith("SAMPLE DATA")
    assert sample["technical_audit"]["available"] is True
    assert all(k["search_volume"] for k in sample["keywords"])


def test_audit_issues_are_copied_into_the_payload():
    audit = PageAudit("https://example.org", 70.0, [AuditIssue("no_h1_tag", "warning", "No H1 heading", "d")])
    result = analyze(StubProvider({"a": []}, audit=audit), ["a"])
    assert result["technical_audit"]["issues"] == [{"id": "no_h1_tag", "severity": "warning", "title": "No H1 heading", "detail": "d"}]
    assert result["technical_audit"]["onpage_score"] == 70.0
