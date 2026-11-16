"""Database models. Every row that belongs to a customer hangs off `User`."""
from __future__ import annotations

from datetime import datetime, timezone

from .extensions import db


def utcnow() -> datetime:
    # Stored naive (UTC) so SQLite and other databases behave the same way.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() + "Z" if value else None


class SchemaInfo(db.Model):
    __tablename__ = "schema_info"
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.Integer, nullable=False)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(20), nullable=False, default="starter")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    projects = db.relationship("Project", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        # password_hash is never serialised.
        return {"id": self.id, "email": self.email, "plan": self.plan, "created_at": iso(self.created_at)}


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    website_url = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    location_name = db.Column(db.String(100), nullable=False)
    language_code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    keywords = db.relationship(
        "Keyword", backref="project", lazy=True, cascade="all, delete-orphan", order_by="Keyword.id"
    )
    analyses = db.relationship(
        "AnalysisRun", backref="project", lazy=True, cascade="all, delete-orphan", order_by="AnalysisRun.id"
    )
    reports = db.relationship("Report", backref="project", lazy=True, cascade="all, delete-orphan", order_by="Report.id")

    def keyword_list(self) -> list[str]:
        return [k.text for k in self.keywords]

    def to_dict(self, *, last_analyzed_at: datetime | None = None) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "website_url": self.website_url,
            "domain": self.domain,
            "location_name": self.location_name,
            "language_code": self.language_code,
            "keywords": self.keyword_list(),
            "created_at": iso(self.created_at),
            "last_analyzed_at": iso(last_analyzed_at),
        }


class Keyword(db.Model):
    __tablename__ = "keywords"
    __table_args__ = (db.UniqueConstraint("project_id", "text", name="uq_keyword_project_text"),)
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    text = db.Column(db.String(255), nullable=False)


class AnalysisRun(db.Model):
    """One fetch of rank data for a project. `result` is the normalised payload from `analysis.py`."""

    __tablename__ = "analysis_runs"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    provider = db.Column(db.String(30), nullable=False)
    is_sample = db.Column(db.Boolean, nullable=False)
    result = db.Column(db.JSON, nullable=False)

    # Declared so deleting a run (or its project) removes the reports built from it first.
    reports = db.relationship("Report", backref="analysis", lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "created_at": iso(self.created_at),
            "provider": self.provider,
            "is_sample": self.is_sample,
            "result": self.result,
        }


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analysis_runs.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    generator = db.Column(db.String(20), nullable=False)  # 'openai' or 'template'
    model = db.Column(db.String(80))
    is_sample = db.Column(db.Boolean, nullable=False)
    content = db.Column(db.JSON, nullable=False)
    reviewed_at = db.Column(db.DateTime)

    def summary(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "analysis_id": self.analysis_id,
            "created_at": iso(self.created_at),
            "generator": self.generator,
            "model": self.model,
            "is_sample": self.is_sample,
            "reviewed_at": iso(self.reviewed_at),
            "needs_human_review": self.reviewed_at is None,
        }

    def to_dict(self) -> dict:
        data = self.summary()
        data["content"] = self.content
        return data
