from flask import Blueprint, request, jsonify, send_from_directory
from datetime import datetime
import json
import os
from src.models.seo_models import db, Customer, Keyword, Report, Competitor
from src.services.dataforseo_service import DataForSEOService

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/customers', methods=['POST'])
def create_customer():
    """Create a new customer account"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'website_url', 'target_keywords', 'subscription_plan']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if customer already exists
        existing_customer = Customer.query.filter_by(email=data['email']).first()
        if existing_customer:
            return jsonify({'error': 'Customer with this email already exists'}), 409
        
        # Parse keywords (expecting comma-separated string)
        keywords = [k.strip() for k in data['target_keywords'].split(',') if k.strip()]
        
        # Create new customer
        customer = Customer(
            name=data['name'],
            email=data['email'],
            website_url=data['website_url'],
            target_keywords=json.dumps(keywords),
            subscription_plan=data['subscription_plan']
        )
        
        db.session.add(customer)
        db.session.commit()
        
        # Create keyword entries
        for keyword in keywords:
            keyword_entry = Keyword(
                customer_id=customer.id,
                keyword=keyword
            )
            db.session.add(keyword_entry)
        
        db.session.commit()
        
        # Trigger initial SEO analysis
        try:
            seo_service = DataForSEOService()
            analysis_results = seo_service.analyze_customer_seo({
                'website_url': customer.website_url,
                'target_keywords': keywords
            })
            
            # Update keyword data
            for keyword in keywords:
                keyword_entry = Keyword.query.filter_by(
                    customer_id=customer.id, 
                    keyword=keyword
                ).first()
                
                if keyword_entry and keyword in analysis_results.get('keyword_rankings', {}):
                    ranking_data = analysis_results['keyword_rankings'][keyword]
                    keyword_entry.current_rank = ranking_data.get('current_rank')
                    
                if keyword_entry and keyword in analysis_results.get('keyword_data', {}):
                    kw_data = analysis_results['keyword_data'][keyword]
                    keyword_entry.search_volume = kw_data.get('search_volume')
                    keyword_entry.difficulty = kw_data.get('difficulty')
            
            # Store competitors
            for competitor_data in analysis_results.get('competitors', []):
                competitor = Competitor(
                    customer_id=customer.id,
                    competitor_url=competitor_data['url'],
                    competitor_rank=int(competitor_data['average_rank']),
                    content_analysis=json.dumps(competitor_data)
                )
                db.session.add(competitor)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Error in initial SEO analysis: {e}")
        
        return jsonify({
            'message': 'Customer created successfully',
            'customer': customer.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get customer details"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        return jsonify(customer.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/customers/<int:customer_id>/keywords', methods=['GET'])
def get_customer_keywords(customer_id):
    """Get all keywords for a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        keywords = Keyword.query.filter_by(customer_id=customer_id).all()
        return jsonify([keyword.to_dict() for keyword in keywords])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/customers/<int:customer_id>/competitors', methods=['GET'])
def get_customer_competitors(customer_id):
    """Get all competitors for a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        competitors = Competitor.query.filter_by(customer_id=customer_id).all()
        return jsonify([competitor.to_dict() for competitor in competitors])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/customers/<int:customer_id>/reports', methods=['GET'])
def get_customer_reports(customer_id):
    """Get all reports for a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        reports = Report.query.filter_by(customer_id=customer_id).order_by(Report.report_date.desc()).all()
        return jsonify([report.to_dict() for report in reports])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/customers/<int:customer_id>/analyze', methods=['POST'])
def analyze_customer_seo(customer_id):
    """Trigger SEO analysis for a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        keywords = json.loads(customer.target_keywords)
        
        # Initialize DataForSEO service
        seo_service = DataForSEOService()
        
        # Perform SEO analysis
        analysis_results = seo_service.analyze_customer_seo({
            'website_url': customer.website_url,
            'target_keywords': keywords
        })
        
        # Update keyword rankings
        for keyword in keywords:
            keyword_entry = Keyword.query.filter_by(
                customer_id=customer_id, 
                keyword=keyword
            ).first()
            
            if keyword_entry and keyword in analysis_results.get('keyword_rankings', {}):
                ranking_data = analysis_results['keyword_rankings'][keyword]
                
                # Store previous rank
                keyword_entry.previous_rank = keyword_entry.current_rank
                keyword_entry.current_rank = ranking_data.get('current_rank')
                keyword_entry.last_updated = datetime.utcnow()
                
            if keyword_entry and keyword in analysis_results.get('keyword_data', {}):
                kw_data = analysis_results['keyword_data'][keyword]
                keyword_entry.search_volume = kw_data.get('search_volume')
                keyword_entry.difficulty = kw_data.get('difficulty')
        
        # Update competitors
        Competitor.query.filter_by(customer_id=customer_id).delete()
        for competitor_data in analysis_results.get('competitors', []):
            competitor = Competitor(
                customer_id=customer_id,
                competitor_url=competitor_data['url'],
                competitor_rank=int(competitor_data['average_rank']),
                content_analysis=json.dumps(competitor_data)
            )
            db.session.add(competitor)
        
        db.session.commit()
        
        return jsonify({
            'message': 'SEO analysis completed successfully',
            'results': analysis_results
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/customers/<int:customer_id>/dashboard', methods=['GET'])
def get_customer_dashboard(customer_id):
    """Get dashboard data for a customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        keywords = Keyword.query.filter_by(customer_id=customer_id).all()
        competitors = Competitor.query.filter_by(customer_id=customer_id).limit(5).all()
        recent_reports = Report.query.filter_by(customer_id=customer_id).order_by(Report.report_date.desc()).limit(3).all()
        
        # Calculate ranking improvements
        ranking_improvements = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword.current_rank and keyword.previous_rank:
                if keyword.current_rank < keyword.previous_rank:  # Lower rank number is better
                    ranking_improvements += 1
        
        # Calculate average search volume
        total_volume = sum(k.search_volume or 0 for k in keywords)
        avg_search_volume = total_volume // total_keywords if total_keywords > 0 else 0
        
        dashboard_data = {
            'customer': customer.to_dict(),
            'stats': {
                'total_keywords': total_keywords,
                'ranking_improvements': ranking_improvements,
                'avg_search_volume': avg_search_volume,
                'total_competitors': len(competitors)
            },
            'keywords': [k.to_dict() for k in keywords],
            'competitors': [c.to_dict() for c in competitors],
            'recent_reports': [r.to_dict() for r in recent_reports]
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/test-dataforseo', methods=['GET'])
def test_dataforseo():
    """Test DataForSEO API connection"""
    try:
        seo_service = DataForSEOService()
        
        # Test with a simple keyword
        test_keyword = "SEO services"
        serp_results = seo_service.get_serp_results(test_keyword)
        
        return jsonify({
            'message': 'DataForSEO API test successful',
            'test_keyword': test_keyword,
            'status': serp_results.get('status_message', 'Unknown'),
            'has_results': bool(serp_results.get('tasks'))
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'SEO Backend API'
    })



@seo_bp.route('/customers/<int:customer_id>/generate-report', methods=['POST'])
def generate_ai_report(customer_id):
    """Generate AI-powered SEO report for a customer"""
    try:
        from src.services.ai_report_service import AIReportService
        
        customer = Customer.query.get_or_404(customer_id)
        keywords = json.loads(customer.target_keywords)
        
        # Get latest SEO data
        from src.services.dataforseo_service import DataForSEOService
        seo_service = DataForSEOService()
        
        seo_data = seo_service.analyze_customer_seo({
            'website_url': customer.website_url,
            'target_keywords': keywords
        })
        
        # Generate AI report
        ai_service = AIReportService()
        report_data = ai_service.generate_seo_analysis(customer.to_dict(), seo_data)
        
        # Create report record
        report = Report(
            customer_id=customer_id,
            ranking_changes=json.dumps(seo_data.get('keyword_rankings', {})),
            competitor_data=json.dumps(seo_data.get('competitors', [])),
            content_suggestions=json.dumps(report_data.get('content_suggestions', [])),
            technical_issues=json.dumps(seo_data.get('technical_audit', {})),
            ai_analysis=json.dumps({
                'executive_summary': report_data.get('executive_summary', ''),
                'ranking_analysis': report_data.get('ranking_analysis', ''),
                'competitor_analysis': report_data.get('competitor_analysis', ''),
                'technical_recommendations': report_data.get('technical_recommendations', []),
                'action_plan': report_data.get('action_plan', [])
            })
        )
        
        # Generate PDF if requested
        data = request.get_json() or {}
        if data.get('generate_pdf', False):
            import os
            pdf_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
            os.makedirs(pdf_dir, exist_ok=True)
            
            pdf_filename = f"seo_report_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            
            generated_pdf = ai_service.generate_pdf_report(customer.to_dict(), report_data, pdf_path)
            if generated_pdf:
                report.pdf_path = pdf_path
        
        db.session.add(report)
        
        # Update customer's last report date
        customer.last_report_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'AI report generated successfully',
            'report_id': report.id,
            'report_data': report_data
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """Get a specific report"""
    try:
        report = Report.query.get_or_404(report_id)
        return jsonify(report.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/reports/<int:report_id>/pdf', methods=['GET'])
def download_report_pdf(report_id):
    """Download PDF report"""
    try:
        report = Report.query.get_or_404(report_id)
        
        if not report.pdf_path or not os.path.exists(report.pdf_path):
            return jsonify({'error': 'PDF not found'}), 404
        
        return send_from_directory(
            os.path.dirname(report.pdf_path),
            os.path.basename(report.pdf_path),
            as_attachment=True,
            download_name=f"seo_report_{report.customer_id}_{report.report_date.strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@seo_bp.route('/customers/<int:customer_id>/content-ideas', methods=['GET'])
def get_content_ideas(customer_id):
    """Get AI-generated content ideas for a customer"""
    try:
        from src.services.ai_report_service import AIReportService
        
        customer = Customer.query.get_or_404(customer_id)
        keywords = json.loads(customer.target_keywords)
        
        # Get basic SEO context
        context = f"""
        Website: {customer.website_url}
        Target Keywords: {', '.join(keywords)}
        Business Type: General Business
        """
        
        ai_service = AIReportService()
        content_suggestions = ai_service._generate_content_suggestions(context)
        
        return jsonify({
            'customer_id': customer_id,
            'content_suggestions': content_suggestions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

