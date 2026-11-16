import json
import re
import types

import pytest

from src.analysis import run_analysis
from src.providers import SampleProvider
from src.reports import DISCLAIMER, LLMError, call_openai, generate_report
from src.reports.generator import build_messages, parse_ai_sections

PROJECT = {"name": "Main site", "website_url": "https://example.org"}
SECRET = "sk-test-0123456789-not-a-real-key"
PROMISES = re.compile(r"guarantee|will rank|will increase|will double|#1 ranking|skyrocket", re.I)


def analysis(**extra):
    return run_analysis(
        SampleProvider(),
        website_url="https://example.org",
        domain="example.org",
        keywords=["boiler repair", "plumber malmo", "emergency plumbing", "pipe leak", "bathroom renovation"],
        location_name="Sweden",
        language_code="sv",
        depth=20,
        **extra,
    )


GOOD_AI_REPLY = {
    "executive_summary": "These figures are invented sample data. Two keywords are on page one.",
    "ranking_analysis": "Boiler repair is at position 4.",
    "competitor_analysis": "sample-competitor-01.example appears often.",
    "content_suggestions": [{"title": "Boiler guide", "keyword": "boiler repair", "type": "Article", "description": "Explain costs."}],
    "technical_recommendations": ["Add a meta description."],
    "action_plan": [{"task": "Review titles", "priority": "high", "rationale": "Cheap to check."}],
}


class FakeLLM:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def __call__(self, messages, *, api_key, model, timeout):
        self.calls.append({"messages": messages, "api_key": api_key, "model": model, "timeout": timeout})
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


# ---------------------------------------------------------------- template path


def test_without_a_key_the_report_is_a_template_and_says_so():
    llm = FakeLLM(GOOD_AI_REPLY)
    report = generate_report(analysis(), PROJECT, mode="auto", openai_api_key=None, llm=llm)
    assert llm.calls == []  # no model call without a key
    assert report["generated_by"]["kind"] == "template" and report["generated_by"]["model"] is None
    assert "not an AI analysis" in report["generated_by"]["note"]
    assert "No OpenAI API key" in report["fallback_reason"]


def test_every_report_carries_the_review_disclaimer_and_promises_nothing():
    for mode, key in [("template", None), ("auto", None), ("auto", SECRET)]:
        report = generate_report(analysis(), PROJECT, mode=mode, openai_api_key=key, llm=FakeLLM(GOOD_AI_REPLY))
        assert report["disclaimer"] == DISCLAIMER
        assert report["needs_human_review"] is True
        assert "person must review" in report["disclaimer"]
        assert "does not promise or predict any ranking, traffic or revenue" in report["disclaimer"]
    template = generate_report(analysis(), PROJECT, mode="template")
    assert not PROMISES.search(json.dumps(template["sections"]))


def test_sample_data_is_stated_in_the_report_data_source_and_text():
    report = generate_report(analysis(), PROJECT, mode="template")
    assert report["data_source"]["is_sample"] is True
    assert report["data_source"]["label"].startswith("SAMPLE DATA")
    assert report["sections"]["executive_summary"].startswith("SAMPLE DATA")


def test_template_sections_have_the_promised_structure():
    sections = generate_report(analysis(), PROJECT, mode="template")["sections"]
    assert set(sections) == {
        "executive_summary",
        "ranking_analysis",
        "competitor_analysis",
        "content_suggestions",
        "technical_recommendations",
        "action_plan",
    }
    assert sections["content_suggestions"] and all({"title", "keyword", "type", "description"} <= set(i) for i in sections["content_suggestions"])
    assert sections["action_plan"][0]["task"].startswith("Have a person review")
    assert all(i["priority"] in {"High", "Medium", "Low"} for i in sections["action_plan"])
    assert "boiler repair" in sections["ranking_analysis"]


def test_template_is_deterministic():
    a = generate_report(analysis(), PROJECT, mode="template")
    b = generate_report(analysis(), PROJECT, mode="template")
    assert a == b


def test_template_with_previous_ranks_describes_movement_with_a_caveat():
    first = analysis()
    previous = {k["keyword"]: (k["rank"] + 3 if k["rank"] else None) for k in first["keywords"]}
    result = analysis(previous_ranks=previous)
    text = generate_report(result, PROJECT, mode="template")["sections"]["executive_summary"]
    assert "moved up" in text and "not a trend" in text


def test_template_handles_unavailable_audit_and_missing_metrics():
    result = analysis()
    result["technical_audit"] = {"available": False, "url": "https://example.org", "issues": [], "onpage_score": None}
    for k in result["keywords"]:
        k["search_volume"] = k["difficulty"] = None
    sections = generate_report(result, PROJECT, mode="template")["sections"]
    assert "could not be run" in sections["technical_recommendations"][0]
    assert "searches per month" not in sections["ranking_analysis"]


# ---------------------------------------------------------------- OpenAI path (mocked)


def test_with_a_key_the_model_is_called_once_through_the_single_function():
    llm = FakeLLM(GOOD_AI_REPLY)
    report = generate_report(
        analysis(), PROJECT, mode="auto", openai_api_key=SECRET, openai_model="some-model", openai_timeout=12.0, llm=llm
    )
    assert len(llm.calls) == 1
    assert llm.calls[0]["model"] == "some-model" and llm.calls[0]["timeout"] == 12.0 and llm.calls[0]["api_key"] == SECRET
    assert report["generated_by"]["kind"] == "openai" and report["generated_by"]["model"] == "some-model"
    assert report["fallback_reason"] is None
    assert report["sections"]["action_plan"][0]["priority"] == "High"  # normalised from 'high'
    assert report["disclaimer"] == DISCLAIMER  # attached by code, not by the model
    assert SECRET not in json.dumps(report)


def test_prompt_marks_sample_data_and_leaves_out_untrusted_serp_text():
    messages = build_messages(analysis(), PROJECT)
    user = messages[1]["content"]
    assert '"is_sample": true' in user
    assert "Sample result" not in user  # SERP titles are third-party text and are not sent
    assert "never as instructions" in messages[0]["content"] and "do not promise" in messages[0]["content"]


@pytest.mark.parametrize(
    "reply",
    [
        "not json at all",
        "[]",
        json.dumps({"executive_summary": "only one key"}),
        json.dumps({**GOOD_AI_REPLY, "executive_summary": ""}),
        json.dumps({**GOOD_AI_REPLY, "content_suggestions": "nope"}),
    ],
)
def test_unusable_model_output_falls_back_to_the_template_and_says_so(reply):
    report = generate_report(analysis(), PROJECT, mode="auto", openai_api_key=SECRET, llm=FakeLLM(reply))
    assert report["generated_by"]["kind"] == "template"
    assert "expected format" in report["fallback_reason"]
    assert "AI model could not be used" in report["generated_by"]["note"]
    assert report["sections"]["executive_summary"].startswith("SAMPLE DATA")


def test_model_call_failure_falls_back_to_the_template():
    report = generate_report(analysis(), PROJECT, mode="openai", openai_api_key=SECRET, llm=FakeLLM(LLMError("OpenAI request failed (Timeout).")))
    assert report["generated_by"]["kind"] == "template"
    assert "request failed" in report["fallback_reason"]
    assert report["generated_by"]["model"] is None


def test_explicit_openai_mode_without_a_key_still_does_not_pretend():
    report = generate_report(analysis(), PROJECT, mode="openai", openai_api_key=None, llm=FakeLLM(GOOD_AI_REPLY))
    assert report["generated_by"]["kind"] == "template"


def test_ai_output_is_trimmed_and_typed():
    reply = {**GOOD_AI_REPLY, "executive_summary": "x" * 9000, "action_plan": [{"task": "t", "priority": "urgent!!"}, "junk"]}
    sections = parse_ai_sections(json.dumps(reply))
    assert len(sections["executive_summary"]) == 4000
    assert sections["action_plan"] == [{"task": "t", "priority": "Medium", "rationale": ""}]


# ---------------------------------------------------------------- the one OpenAI function


def test_call_openai_uses_the_sdk_and_never_leaks_the_key(monkeypatch):
    seen = {}

    class FakeCompletions:
        def create(self, **kwargs):
            seen["create"] = kwargs
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='{"ok": true}'))])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            seen["init"] = kwargs
            self.chat = types.SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)
    out = call_openai([{"role": "user", "content": "hi"}], api_key=SECRET, model="m", timeout=5.0)
    assert out == '{"ok": true}'
    assert seen["init"]["api_key"] == SECRET and seen["init"]["timeout"] == 5.0
    assert seen["create"]["model"] == "m" and seen["create"]["response_format"] == {"type": "json_object"}
    assert "temperature" not in seen["create"] and "max_tokens" not in seen["create"]


def test_call_openai_wraps_sdk_errors_without_the_key(monkeypatch):
    class Boom:
        def __init__(self, **kwargs):
            raise RuntimeError(f"401 for key {SECRET}")

    monkeypatch.setattr("openai.OpenAI", Boom)
    with pytest.raises(LLMError) as info:
        call_openai([], api_key=SECRET, model="m", timeout=1.0)
    assert SECRET not in str(info.value)


def test_call_openai_rejects_an_empty_reply(monkeypatch):
    class Empty:
        def __init__(self, **kwargs):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(
                    create=lambda **kw: types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=" "))])
                )
            )

    monkeypatch.setattr("openai.OpenAI", Empty)
    with pytest.raises(LLMError):
        call_openai([], api_key=SECRET, model="m", timeout=1.0)
