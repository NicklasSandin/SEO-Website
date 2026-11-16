from src.providers import SAMPLE_LABEL, SampleProvider

KW = dict(location_name="Sweden", language_code="sv")


def test_sample_provider_is_flagged_as_sample():
    provider = SampleProvider()
    assert provider.is_sample is True
    assert provider.name == "sample"
    assert "SAMPLE" in SAMPLE_LABEL


def test_serp_is_deterministic_and_has_depth_results():
    provider = SampleProvider()
    a = provider.get_serp("boiler repair", depth=20, target_domain="example.org", **KW)
    b = provider.get_serp("boiler repair", depth=20, target_domain="example.org", **KW)
    assert a == b
    assert [item.rank for item in a.items] == list(range(1, 21))
    assert len({item.domain for item in a.items}) == 20


def test_competitors_use_the_reserved_example_tld_so_they_cannot_be_real_sites():
    serp = SampleProvider().get_serp("boiler repair", depth=20, target_domain="example.org", **KW)
    others = [item for item in serp.items if item.domain != "example.org"]
    assert others and all(item.domain.endswith(".example") for item in others)
    assert all("sample" in item.title.lower() for item in others)


def test_target_domain_is_placed_at_most_once_and_sometimes_missing():
    provider = SampleProvider()
    placed, missing = 0, 0
    for i in range(60):
        serp = provider.get_serp(f"keyword {i}", depth=20, target_domain="example.org", **KW)
        count = sum(1 for item in serp.items if item.domain == "example.org")
        assert count <= 1
        placed += count
        missing += 1 - count
    assert placed > 0 and missing > 0


def test_no_target_domain_means_no_own_result():
    serp = SampleProvider().get_serp("boiler repair", depth=10, **KW)
    assert all(item.domain.endswith(".example") for item in serp.items)


def test_metrics_cover_every_keyword_case_insensitively():
    result = SampleProvider().get_keyword_metrics(["Boiler Repair", "plumber"], **KW)
    assert set(result.metrics) == {"boiler repair", "plumber"}
    for metrics in result.metrics.values():
        assert metrics.search_volume and metrics.search_volume >= 500
        assert 10 <= metrics.difficulty <= 90
    assert result.warnings == []


def test_audit_findings_are_marked_as_samples():
    audit = SampleProvider().audit_page("https://example.org")
    assert audit.issues
    assert all(issue.title.startswith("Sample finding") for issue in audit.issues)
    assert all("not a real finding" in issue.detail for issue in audit.issues)
