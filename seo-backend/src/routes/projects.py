from __future__ import annotations

from datetime import timedelta

from flask import Blueprint, current_app, jsonify
from sqlalchemy import func

from ..analysis import data_label, run_analysis
from ..extensions import db
from ..models import AnalysisRun, Keyword, Project, Report, utcnow
from ..providers import (
    ProviderAuthError,
    ProviderError,
    ProviderPaymentError,
    ProviderRateLimitError,
)
from ..reports import generate_report
from ..security import current_user, login_required, plan_keyword_limit
from ..validation import (
    ValidationError,
    validate_keywords,
    validate_language,
    validate_location,
    validate_name,
    validate_website_url,
)
from .common import error, json_body, not_found, owned_project

bp = Blueprint("projects", __name__)


def _last_analyzed(project_ids: list[int]) -> dict[int, object]:
    if not project_ids:
        return {}
    rows = (
        db.session.query(AnalysisRun.project_id, func.max(AnalysisRun.created_at))
        .filter(AnalysisRun.project_id.in_(project_ids))
        .group_by(AnalysisRun.project_id)
        .all()
    )
    return dict(rows)


def _latest_analysis(project_id: int) -> AnalysisRun | None:
    return AnalysisRun.query.filter_by(project_id=project_id).order_by(AnalysisRun.id.desc()).first()


def _set_keywords(project: Project, keywords: list[str]) -> None:
    # Keep rows for keywords that stay (replacing them would insert a duplicate before the old row is deleted).
    existing = {k.text: k for k in project.keywords}
    project.keywords[:] = [existing.get(text) or Keyword(text=text) for text in keywords]


# ---------------------------------------------------------------- projects


@bp.get("/projects")
@login_required
def list_projects():
    projects = Project.query.filter_by(user_id=current_user().id).order_by(Project.id).all()
    last = _last_analyzed([p.id for p in projects])
    return jsonify({"projects": [p.to_dict(last_analyzed_at=last.get(p.id)) for p in projects]})


@bp.post("/projects")
@login_required
def create_project():
    user = current_user()
    data = json_body()
    name = validate_name(data.get("name"))
    url, domain = validate_website_url(data.get("website_url"))
    keywords = validate_keywords(data.get("keywords"), plan_keyword_limit(user))
    location = validate_location(data.get("location_name"), current_app.config["DEFAULT_LOCATION_NAME"])
    language = validate_language(data.get("language_code"), current_app.config["DEFAULT_LANGUAGE_CODE"])
    if Project.query.filter_by(user_id=user.id).count() >= current_app.config["MAX_PROJECTS_PER_USER"]:
        return error("You have reached the maximum number of projects.", "project_limit", 409)
    project = Project(user_id=user.id, name=name, website_url=url, domain=domain, location_name=location, language_code=language)
    _set_keywords(project, keywords)
    db.session.add(project)
    db.session.commit()
    return jsonify({"project": project.to_dict()}), 201


@bp.get("/projects/<int:project_id>")
@login_required
def get_project(project_id: int):
    project = owned_project(project_id)
    if project is None:
        return not_found("Project not found.")
    last = _last_analyzed([project.id]).get(project.id)
    return jsonify({"project": project.to_dict(last_analyzed_at=last)})


@bp.patch("/projects/<int:project_id>")
@login_required
def update_project(project_id: int):
    project = owned_project(project_id)
    if project is None:
        return not_found("Project not found.")
    data = json_body()
    if "name" in data:
        project.name = validate_name(data["name"])
    if "website_url" in data:
        project.website_url, project.domain = validate_website_url(data["website_url"])
    if "keywords" in data:
        _set_keywords(project, validate_keywords(data["keywords"], plan_keyword_limit(current_user())))
    if "location_name" in data:
        project.location_name = validate_location(data["location_name"], current_app.config["DEFAULT_LOCATION_NAME"])
    if "language_code" in data:
        project.language_code = validate_language(data["language_code"], current_app.config["DEFAULT_LANGUAGE_CODE"])
    db.session.commit()
    last = _last_analyzed([project.id]).get(project.id)
    return jsonify({"project": project.to_dict(last_analyzed_at=last)})


@bp.delete("/projects/<int:project_id>")
@login_required
def delete_project(project_id: int):
    project = owned_project(project_id)
    if project is None:
        return not_found("Project not found.")
    db.session.delete(project)
    db.session.commit()
    return "", 204


# ---------------------------------------------------------------- analysis


def _provider_failure(exc: ProviderError):
    """A provider error as an API response. The messages are written not to contain credentials."""
    if isinstance(exc, ProviderAuthError):
        return error("The rank-data provider rejected the configured credentials.", "provider_auth_failed", 502)
    if isinstance(exc, ProviderPaymentError):
        return error("The rank-data provider reports a billing problem (balance or cost limit).", "provider_payment_required", 502)
    if isinstance(exc, ProviderRateLimitError):
        extra = {"retry_after": exc.retry_after} if exc.retry_after else {}
        return error("The rank-data provider is rate limiting requests. Try again in a minute.", "provider_rate_limited", 429, **extra)
    return error(f"The rank-data provider failed: {exc}", "provider_error", 502)


@bp.post("/projects/<int:project_id>/analyze")
@login_required
def analyze(project_id: int):
    project = owned_project(project_id)
    if project is None:
        return not_found("Project not found.")
    user = current_user()
    config = current_app.config
    provider = current_app.extensions["siktio_provider"]

    since = utcnow() - timedelta(days=1)
    used = (
        AnalysisRun.query.join(Project, AnalysisRun.project_id == Project.id)
        .filter(Project.user_id == user.id, AnalysisRun.created_at >= since)
        .count()
    )
    if used >= config["MAX_ANALYSES_PER_USER_PER_DAY"]:
        return error("Daily analysis limit reached. Try again tomorrow.", "analysis_quota", 429)

    # Only compare with an earlier run of the same kind, so sample and real data are never mixed.
    previous = (
        AnalysisRun.query.filter_by(project_id=project.id, provider=provider.name)
        .order_by(AnalysisRun.id.desc())
        .first()
    )
    previous_ranks = {row["keyword"]: row["rank"] for row in previous.result["keywords"]} if previous else {}

    try:
        result = run_analysis(
            provider,
            website_url=project.website_url,
            domain=project.domain,
            keywords=project.keyword_list(),
            location_name=project.location_name,
            language_code=project.language_code,
            depth=config["SERP_DEPTH"],
            previous_ranks=previous_ranks,
        )
    except ProviderError as exc:
        return _provider_failure(exc)

    run = AnalysisRun(project_id=project.id, provider=provider.name, is_sample=provider.is_sample, result=result)
    db.session.add(run)
    db.session.commit()
    return jsonify({"analysis": run.to_dict()}), 201


@bp.get("/projects/<int:project_id>/analyses/latest")
@login_required
def latest_analysis(project_id: int):
    project = owned_project(project_id)
    if project is None:
        return not_found("Project not found.")
    run = _latest_analysis(project.id)
    if run is None:
        return not_found("No analysis has been run for this project yet.")
    return jsonify({"analysis": run.to_dict()})


def _stats(result: dict) -> dict:
    keywords = result["keywords"]
    volumes = [k["search_volume"] for k in keywords if k.get("search_volume") is not None]
    compared = [k for k in keywords if k["rank"] is not None and k.get("previous_rank") is not None]
    return {
        "keywords_tracked": len(keywords),
        "in_top_3": sum(1 for k in keywords if k["rank"] is not None and k["rank"] <= 3),
        "in_top_10": sum(1 for k in keywords if k["rank"] is not None and k["rank"] <= 10),
        "not_found": sum(1 for k in keywords if k["rank"] is None),
        "average_search_volume": round(sum(volumes) / len(volumes)) if volumes else None,
        "competitors_found": len(result["competitors"]),
        "moved_up": sum(1 for k in compared if k["rank"] < k["previous_rank"]),
        "moved_down": sum(1 for k in compared if k["rank"] > k["previous_rank"]),
    }


@bp.get("/projects/<int:project_id>/dashboard")
@login_required
def dashboard(project_id: int):
    project = owned_project(project_id)
    if project is None:
        return not_found("Project not found.")
    run = _latest_analysis(project.id)
    reports = Report.query.filter_by(project_id=project.id).order_by(Report.id.desc()).limit(20).all()
    provider = current_app.extensions["siktio_provider"]
    source_provider, source_sample = (run.provider, run.is_sample) if run else (provider.name, provider.is_sample)
    return jsonify(
        {
            "project": project.to_dict(last_analyzed_at=run.created_at if run else None),
            "data_source": {
                "provider": source_provider,
                "is_sample": source_sample,
                "label": data_label(source_sample, source_provider),
            },
            "latest_analysis": run.to_dict() if run else None,
            "stats": _stats(run.result) if run else None,
            "reports": [r.summary() for r in reports],
        }
    )


# ---------------------------------------------------------------- reports


@bp.post("/projects/<int:project_id>/reports")
@login_required
def create_report(project_id: int):
    project = owned_project(project_id)
    if project is None:
        return not_found("Project not found.")
    data = json_body(required=False)
    analysis_id = data.get("analysis_id")
    if analysis_id is None:
        run = _latest_analysis(project.id)
    elif isinstance(analysis_id, int) and not isinstance(analysis_id, bool):
        run = AnalysisRun.query.filter_by(id=analysis_id, project_id=project.id).first()
        if run is None:
            return not_found("Analysis not found.")
    else:
        raise ValidationError("analysis_id must be a number.", "analysis_id")
    if run is None:
        return error("Run an analysis first: a report needs rank data to describe.", "no_analysis", 409)

    config = current_app.config
    content = generate_report(
        run.result,
        {"name": project.name, "website_url": project.website_url},
        mode=config["REPORT_GENERATOR"],
        openai_api_key=config["OPENAI_API_KEY"],
        openai_model=config["OPENAI_MODEL"],
        openai_timeout=config["OPENAI_TIMEOUT_SECONDS"],
        llm=current_app.extensions.get("siktio_llm"),
    )
    report = Report(
        project_id=project.id,
        analysis_id=run.id,
        generator=content["generated_by"]["kind"],
        model=content["generated_by"]["model"],
        is_sample=run.is_sample,
        content=content,
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({"report": report.to_dict()}), 201


@bp.get("/projects/<int:project_id>/reports")
@login_required
def list_reports(project_id: int):
    project = owned_project(project_id)
    if project is None:
        return not_found("Project not found.")
    reports = Report.query.filter_by(project_id=project.id).order_by(Report.id.desc()).all()
    return jsonify({"reports": [r.summary() for r in reports]})


def _owned_report(report_id: int) -> Report | None:
    return (
        Report.query.join(Project, Report.project_id == Project.id)
        .filter(Report.id == report_id, Project.user_id == current_user().id)
        .first()
    )


@bp.get("/reports/<int:report_id>")
@login_required
def get_report(report_id: int):
    report = _owned_report(report_id)
    if report is None:
        return not_found("Report not found.")
    return jsonify({"report": report.to_dict()})


@bp.post("/reports/<int:report_id>/review")
@login_required
def mark_reviewed(report_id: int):
    report = _owned_report(report_id)
    if report is None:
        return not_found("Report not found.")
    if report.reviewed_at is None:
        report.reviewed_at = utcnow()
        db.session.commit()
    return jsonify({"report": report.to_dict()})


@bp.delete("/reports/<int:report_id>")
@login_required
def delete_report(report_id: int):
    report = _owned_report(report_id)
    if report is None:
        return not_found("Report not found.")
    db.session.delete(report)
    db.session.commit()
    return "", 204

