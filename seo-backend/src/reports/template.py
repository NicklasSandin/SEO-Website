"""Deterministic template report: fixed rules applied to the analysis data. No AI involved."""
from __future__ import annotations

from typing import Any

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _count(n: int, noun: str) -> str:
    return f"{n} {noun}{'' if n == 1 else 's'}"


def _fmt_int(value: int | None) -> str:
    return f"{value:,}" if value is not None else "n/a"


def _kw_line(row: dict[str, Any], depth: int) -> str:
    if row["rank"] is None:
        position = f"not found in the first {depth} results"
    else:
        position = f"position {row['rank']}"
        if row.get("previous_rank") is not None:
            position += f" (previous check: {row['previous_rank']})"
    extras = []
    if row.get("search_volume") is not None:
        extras.append(f"about {_fmt_int(row['search_volume'])} searches per month")
    if row.get("difficulty") is not None:
        extras.append(f"keyword difficulty {row['difficulty']} of 100")
    suffix = "; " + "; ".join(extras) if extras else ""
    return f"- {row['keyword']}: {position}{suffix}"


def _names(rows: list[dict[str, Any]]) -> str:
    return ", ".join(f"'{r['keyword']}'" for r in rows)


def build_template_sections(analysis: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    keywords = analysis["keywords"]
    depth = analysis["serp_depth"]
    domain = analysis["target_domain"]
    audit = analysis["technical_audit"]
    competitors = analysis["competitors"]

    top3 = [k for k in keywords if k["rank"] is not None and k["rank"] <= 3]
    top10 = [k for k in keywords if k["rank"] is not None and k["rank"] <= 10]
    near = [k for k in keywords if k["rank"] is not None and 3 < k["rank"] <= 10]
    beyond = [k for k in keywords if k["rank"] is not None and k["rank"] > 10]
    missing = [k for k in keywords if k["rank"] is None]
    compared = [k for k in keywords if k["rank"] is not None and k.get("previous_rank") is not None]

    # ---- executive summary
    paragraphs = []
    if analysis["is_sample"]:
        paragraphs.append(
            "SAMPLE DATA: every number in this report is an invented fixture value. "
            "Nothing here describes the real search results of any website."
        )
    paragraphs.append(
        f"Tracked keywords: {len(keywords)}. For {domain}: {len(top10)} in the top 10 Google results "
        f"({len(top3)} of them in the top 3), {len(beyond)} between position 11 and {depth}, and "
        f"{len(missing)} not found in the first {depth} results."
    )
    if compared:
        up = sum(1 for k in compared if k["rank"] < k["previous_rank"])
        down = sum(1 for k in compared if k["rank"] > k["previous_rank"])
        paragraphs.append(
            f"Compared with the previous check of the same kind: moved up {up}, moved down {down}, "
            f"unchanged {len(compared) - up - down}. A single comparison between two checks is not a trend."
        )
    if audit.get("available"):
        issues = audit["issues"]
        crit = sum(1 for i in issues if i["severity"] == "critical")
        warn = sum(1 for i in issues if i["severity"] == "warning")
        paragraphs.append(
            f"The technical check of {audit['url']} flagged {_count(crit, 'critical issue')} and {_count(warn, 'warning')}. "
            "It covers that one page, not the whole site."
        )
    else:
        paragraphs.append("The technical check could not be run, so this report has no technical findings.")
    executive_summary = "\n\n".join(paragraphs)

    # ---- ranking analysis
    lines = [_kw_line(row, depth) for row in keywords]
    groups = []
    if top3:
        groups.append(f"In the top 3: {_names(top3)}.")
    if near:
        groups.append(f"On page one but below the top 3: {_names(near)}.")
    if beyond:
        groups.append(f"Between position 11 and {depth}: {_names(beyond)}.")
    if missing:
        groups.append(f"Not found in the first {depth} results: {_names(missing)}.")
    ranking_analysis = "\n".join(lines + [""] + groups) if groups else "\n".join(lines)

    # ---- competitors
    if competitors:
        parts = ["Domains other than yours that appear most often in the top 10 for your keywords:"]
        for i, c in enumerate(competitors[:5], 1):
            parts.append(
                f"{i}. {c['domain']}: in the top 10 for {c['keywords_count']} of {len(keywords)} keywords, "
                f"average position {c['average_rank']}, best position {c['best_rank']}."
            )
        parts.append(
            "This only shows who ranks, not why. Look at the competing pages yourself before drawing conclusions."
        )
        competitor_analysis = "\n".join(parts)
    else:
        competitor_analysis = "No other domains were found in the top 10 results for the tracked keywords."

    # ---- content suggestions
    gaps = sorted(
        beyond + missing,
        key=lambda k: (k["search_volume"] is None, -(k["search_volume"] or 0), k["keyword"]),
    )
    content = []
    for row in gaps[:5]:
        where = f"is not found in the first {depth} results" if row["rank"] is None else f"ranks at position {row['rank']}"
        content.append(
            {
                "title": f"Create or improve a page that answers '{row['keyword']}'",
                "keyword": row["keyword"],
                "type": "Page or article",
                "description": (
                    f"{domain} {where} for this keyword. Check whether a page on your site answers this search "
                    "directly; if not, consider one. Compare it with the pages that currently rank."
                ),
            }
        )
    if not content:
        content.append(
            {
                "title": "Review the pages that already rank on page one",
                "keyword": keywords[0]["keyword"] if keywords else "",
                "type": "Existing pages",
                "description": "All tracked keywords were found in the top 10. Check that titles, descriptions and content on those pages are current.",
            }
        )

    # ---- technical recommendations
    technical: list[str] = []
    if audit.get("available"):
        ordered = sorted(audit["issues"], key=lambda i: (SEVERITY_ORDER.get(i["severity"], 3), i["id"]))
        technical = [f"{i['title']} ({i['severity']}): {i['detail']}" for i in ordered[:10]]
        if not technical:
            technical = [
                "The technical check flagged no issues on the checked page. That does not mean the rest of the site is free of issues."
            ]
    else:
        technical = ["The technical check could not be run. Run the analysis again before planning technical work."]

    # ---- action plan
    plan: list[dict[str, str]] = [
        {
            "task": "Have a person review this report and the data behind it before acting on it",
            "priority": "High",
            "rationale": "The report is generated automatically and may be wrong or miss context about the business.",
        }
    ]
    crit_issues = [i for i in audit.get("issues", []) if i["severity"] == "critical"]
    if crit_issues:
        plan.append(
            {
                "task": f"Look into the critical technical findings for {audit['url']}",
                "priority": "High",
                "rationale": "Flagged as critical: " + ", ".join(i["title"] for i in crit_issues) + ".",
            }
        )
    if near:
        plan.append(
            {
                "task": f"Review the pages for keywords just below the top 3: {_names(near)}",
                "priority": "Medium",
                "rationale": "These are already on page one, so improving the page may be cheaper than starting something new.",
            }
        )
    if beyond or missing:
        plan.append(
            {
                "task": f"Check whether you have a suitable page for: {_names(beyond + missing)}",
                "priority": "Medium",
                "rationale": f"These keywords were not in the top 10 (position 11 to {depth}, or not found).",
            }
        )
    warn_issues = [i for i in audit.get("issues", []) if i["severity"] == "warning"]
    if warn_issues:
        plan.append(
            {
                "task": "Work through the technical warnings",
                "priority": "Low",
                "rationale": f"{_count(len(warn_issues), 'warning')} flagged; decide which are worth the effort for this site.",
            }
        )

    return {
        "executive_summary": executive_summary,
        "ranking_analysis": ranking_analysis,
        "competitor_analysis": competitor_analysis,
        "content_suggestions": content,
        "technical_recommendations": technical,
        "action_plan": plan,
    }
