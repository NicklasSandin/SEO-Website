from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    website_url = db.Column(db.String(255), nullable=False)
    target_keywords = db.Column(db.Text, nullable=False)  # JSON string of keywords
    subscription_plan = db.Column(db.String(50), nullable=False)  # starter, professional, enterprise
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_report_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    keywords = db.relationship('Keyword', backref='customer', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='customer', lazy=True, cascade='all, delete-orphan')
    competitors = db.relationship('Competitor', backref='customer', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Customer {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'website_url': self.website_url,
            'target_keywords': json.loads(self.target_keywords) if self.target_keywords else [],
            'subscription_plan': self.subscription_plan,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_report_date': self.last_report_date.isoformat() if self.last_report_date else None,
            'is_active': self.is_active
        }

class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    current_rank = db.Column(db.Integer)
    previous_rank = db.Column(db.Integer)
    search_volume = db.Column(db.Integer)
    difficulty = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Keyword {self.keyword}>'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'keyword': self.keyword,
            'current_rank': self.current_rank,
            'previous_rank': self.previous_rank,
            'search_volume': self.search_volume,
            'difficulty': self.difficulty,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    report_date = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(255))
    ranking_changes = db.Column(db.Text)  # JSON string
    competitor_data = db.Column(db.Text)  # JSON string
    content_suggestions = db.Column(db.Text)  # JSON string
    technical_issues = db.Column(db.Text)  # JSON string
    ai_analysis = db.Column(db.Text)  # AI-generated analysis
    
    def __repr__(self):
        return f'<Report {self.id} for Customer {self.customer_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'pdf_path': self.pdf_path,
            'ranking_changes': json.loads(self.ranking_changes) if self.ranking_changes else {},
            'competitor_data': json.loads(self.competitor_data) if self.competitor_data else {},
            'content_suggestions': json.loads(self.content_suggestions) if self.content_suggestions else [],
            'technical_issues': json.loads(self.technical_issues) if self.technical_issues else [],
            'ai_analysis': self.ai_analysis
        }

class Competitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    competitor_url = db.Column(db.String(255), nullable=False)
    competitor_rank = db.Column(db.Integer)
    content_analysis = db.Column(db.Text)  # JSON string
    last_analyzed = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Competitor {self.competitor_url}>'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'competitor_url': self.competitor_url,
            'competitor_rank': self.competitor_rank,
            'content_analysis': json.loads(self.content_analysis) if self.content_analysis else {},
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None
        }

class DataForSEOCache(db.Model):
    """Cache for DataForSEO API responses to avoid unnecessary API calls"""
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), unique=True, nullable=False)
    cache_data = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<DataForSEOCache {self.cache_key}>'

    def to_dict(self):
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'cache_data': json.loads(self.cache_data) if self.cache_data else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

