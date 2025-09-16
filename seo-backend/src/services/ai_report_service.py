import openai
import json
from datetime import datetime
from typing import Dict, List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os

class AIReportService:
    """Service for generating AI-powered SEO reports"""
    
    def __init__(self):
        # OpenAI is already configured via environment variables
        self.client = openai.OpenAI()
        
    def generate_seo_analysis(self, customer_data: Dict, seo_data: Dict) -> Dict:
        """Generate comprehensive SEO analysis using AI"""
        
        # Prepare data for AI analysis
        analysis_context = self._prepare_analysis_context(customer_data, seo_data)
        
        # Generate different sections of the report
        report_sections = {
            'executive_summary': self._generate_executive_summary(analysis_context),
            'ranking_analysis': self._generate_ranking_analysis(analysis_context),
            'competitor_analysis': self._generate_competitor_analysis(analysis_context),
            'content_suggestions': self._generate_content_suggestions(analysis_context),
            'technical_recommendations': self._generate_technical_recommendations(analysis_context),
            'action_plan': self._generate_action_plan(analysis_context)
        }
        
        return report_sections
    
    def _prepare_analysis_context(self, customer_data: Dict, seo_data: Dict) -> str:
        """Prepare context for AI analysis"""
        
        context = f"""
        SEO Analysis Context:
        
        Website: {customer_data.get('website_url', 'N/A')}
        Business Type: {self._infer_business_type(customer_data.get('website_url', ''))}
        Target Keywords: {', '.join(customer_data.get('target_keywords', []))}
        Subscription Plan: {customer_data.get('subscription_plan', 'N/A')}
        
        Current Rankings:
        """
        
        # Add keyword ranking data
        for keyword, ranking_data in seo_data.get('keyword_rankings', {}).items():
            current_rank = ranking_data.get('current_rank', 'Not ranking')
            context += f"- {keyword}: Position {current_rank}\n"
        
        # Add keyword data
        context += "\nKeyword Data:\n"
        for keyword, kw_data in seo_data.get('keyword_data', {}).items():
            volume = kw_data.get('search_volume', 0)
            difficulty = kw_data.get('difficulty', 0)
            context += f"- {keyword}: {volume} monthly searches, {difficulty}% difficulty\n"
        
        # Add competitor data
        context += "\nTop Competitors:\n"
        for i, competitor in enumerate(seo_data.get('competitors', [])[:5], 1):
            context += f"{i}. {competitor.get('url', 'N/A')} (Avg. rank: {competitor.get('average_rank', 'N/A')})\n"
        
        # Add technical issues
        technical_issues = seo_data.get('technical_audit', {})
        if technical_issues:
            context += "\nTechnical Issues:\n"
            for issue in technical_issues.get('critical', []):
                context += f"- CRITICAL: {issue}\n"
            for issue in technical_issues.get('warnings', []):
                context += f"- WARNING: {issue}\n"
        
        return context
    
    def _infer_business_type(self, website_url: str) -> str:
        """Infer business type from website URL"""
        url_lower = website_url.lower()
        
        if any(word in url_lower for word in ['restaurant', 'food', 'pizza', 'cafe']):
            return 'Restaurant/Food Service'
        elif any(word in url_lower for word in ['shop', 'store', 'buy', 'ecommerce']):
            return 'E-commerce'
        elif any(word in url_lower for word in ['law', 'legal', 'attorney']):
            return 'Legal Services'
        elif any(word in url_lower for word in ['health', 'medical', 'doctor']):
            return 'Healthcare'
        elif any(word in url_lower for word in ['tech', 'software', 'app']):
            return 'Technology'
        else:
            return 'General Business'
    
    def _generate_executive_summary(self, context: str) -> str:
        """Generate executive summary using AI"""
        
        prompt = f"""
        Based on the following SEO data, write a professional executive summary for a monthly SEO report. 
        The summary should be 2-3 paragraphs, highlighting key performance indicators, main opportunities, 
        and overall SEO health. Write in a confident, professional tone.
        
        {context}
        
        Executive Summary:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert SEO analyst writing professional reports for business clients."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._get_fallback_executive_summary()
    
    def _generate_ranking_analysis(self, context: str) -> str:
        """Generate ranking analysis using AI"""
        
        prompt = f"""
        Analyze the keyword ranking performance based on the data below. Provide specific insights about:
        1. Which keywords are performing well
        2. Which keywords need improvement
        3. Ranking trends and opportunities
        4. Specific recommendations for ranking improvements
        
        {context}
        
        Ranking Analysis:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an SEO expert analyzing keyword rankings for a client report."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI generation error: {e}")
            return "Ranking analysis data is being processed. Please check back in your next report."
    
    def _generate_competitor_analysis(self, context: str) -> str:
        """Generate competitor analysis using AI"""
        
        prompt = f"""
        Analyze the competitor landscape based on the data below. Provide insights about:
        1. Who the main competitors are
        2. What they're doing well
        3. Opportunities to outrank them
        4. Specific strategies to implement
        
        {context}
        
        Competitor Analysis:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an SEO strategist analyzing competitors for a client."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI generation error: {e}")
            return "Competitor analysis is being processed. Detailed insights will be available in your next report."
    
    def _generate_content_suggestions(self, context: str) -> List[Dict]:
        """Generate content suggestions using AI"""
        
        prompt = f"""
        Based on the SEO data below, suggest 5 specific content ideas that would help improve rankings. 
        For each suggestion, provide:
        1. Content title
        2. Target keyword
        3. Content type (blog post, page, etc.)
        4. Brief description
        
        Format as JSON array with objects containing: title, keyword, type, description
        
        {context}
        
        Content Suggestions (JSON format):
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a content strategist creating SEO-focused content ideas. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.8
            )
            
            content_text = response.choices[0].message.content.strip()
            # Try to parse JSON, fallback to default if parsing fails
            try:
                return json.loads(content_text)
            except json.JSONDecodeError:
                return self._get_fallback_content_suggestions()
                
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._get_fallback_content_suggestions()
    
    def _generate_technical_recommendations(self, context: str) -> List[str]:
        """Generate technical SEO recommendations using AI"""
        
        prompt = f"""
        Based on the technical SEO data below, provide 5-7 specific technical recommendations 
        to improve SEO performance. Focus on actionable items that can be implemented.
        
        {context}
        
        Technical Recommendations (one per line):
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a technical SEO expert providing actionable recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            recommendations = response.choices[0].message.content.strip().split('\n')
            return [rec.strip('- ').strip() for rec in recommendations if rec.strip()]
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._get_fallback_technical_recommendations()
    
    def _generate_action_plan(self, context: str) -> List[Dict]:
        """Generate prioritized action plan using AI"""
        
        prompt = f"""
        Create a prioritized action plan with 5 specific tasks to improve SEO performance. 
        For each task, provide:
        1. Task description
        2. Priority (High/Medium/Low)
        3. Estimated effort (1-5 scale)
        4. Expected impact (1-5 scale)
        
        Format as JSON array with objects containing: task, priority, effort, impact
        
        {context}
        
        Action Plan (JSON format):
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an SEO consultant creating actionable plans. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            action_text = response.choices[0].message.content.strip()
            try:
                return json.loads(action_text)
            except json.JSONDecodeError:
                return self._get_fallback_action_plan()
                
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._get_fallback_action_plan()
    
    def generate_pdf_report(self, customer_data: Dict, report_data: Dict, output_path: str) -> str:
        """Generate PDF report from analysis data"""
        
        try:
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#2563eb')
            )
            
            story.append(Paragraph(f"SEO Report - {customer_data.get('website_url', 'Website')}", title_style))
            story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            story.append(Paragraph(report_data.get('executive_summary', ''), styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Ranking Analysis
            story.append(Paragraph("Ranking Analysis", styles['Heading2']))
            story.append(Paragraph(report_data.get('ranking_analysis', ''), styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Competitor Analysis
            story.append(Paragraph("Competitor Analysis", styles['Heading2']))
            story.append(Paragraph(report_data.get('competitor_analysis', ''), styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Content Suggestions
            story.append(Paragraph("Content Suggestions", styles['Heading2']))
            content_suggestions = report_data.get('content_suggestions', [])
            for i, suggestion in enumerate(content_suggestions, 1):
                story.append(Paragraph(f"{i}. {suggestion.get('title', 'Content Idea')}", styles['Heading3']))
                story.append(Paragraph(f"Target Keyword: {suggestion.get('keyword', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"Type: {suggestion.get('type', 'N/A')}", styles['Normal']))
                story.append(Paragraph(suggestion.get('description', ''), styles['Normal']))
                story.append(Spacer(1, 10))
            
            # Technical Recommendations
            story.append(Paragraph("Technical Recommendations", styles['Heading2']))
            tech_recs = report_data.get('technical_recommendations', [])
            for rec in tech_recs:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Action Plan
            story.append(Paragraph("Action Plan", styles['Heading2']))
            action_plan = report_data.get('action_plan', [])
            for i, action in enumerate(action_plan, 1):
                story.append(Paragraph(f"{i}. {action.get('task', 'Action Item')}", styles['Heading3']))
                story.append(Paragraph(f"Priority: {action.get('priority', 'Medium')} | "
                                     f"Effort: {action.get('effort', 'N/A')}/5 | "
                                     f"Impact: {action.get('impact', 'N/A')}/5", styles['Normal']))
                story.append(Spacer(1, 10))
            
            doc.build(story)
            return output_path
            
        except Exception as e:
            print(f"PDF generation error: {e}")
            return None
    
    def _get_fallback_executive_summary(self) -> str:
        """Fallback executive summary when AI is unavailable"""
        return """Your SEO performance is being analyzed using advanced algorithms and competitor intelligence. 
        This month's data shows opportunities for improvement in keyword rankings and content optimization. 
        Our AI-powered analysis has identified specific strategies to enhance your search visibility and outrank competitors."""
    
    def _get_fallback_content_suggestions(self) -> List[Dict]:
        """Fallback content suggestions when AI is unavailable"""
        return [
            {
                "title": "Ultimate Guide to [Your Main Service]",
                "keyword": "main target keyword",
                "type": "Blog Post",
                "description": "Comprehensive guide covering all aspects of your main service offering"
            },
            {
                "title": "Local [Service] in [Your City] - Complete Guide",
                "keyword": "local service keyword",
                "type": "Service Page",
                "description": "Location-specific content targeting local search queries"
            },
            {
                "title": "Common [Industry] Questions Answered",
                "keyword": "industry FAQ keyword",
                "type": "FAQ Page",
                "description": "Address frequently asked questions in your industry"
            }
        ]
    
    def _get_fallback_technical_recommendations(self) -> List[str]:
        """Fallback technical recommendations when AI is unavailable"""
        return [
            "Optimize page loading speed for better user experience",
            "Add missing meta descriptions to improve click-through rates",
            "Implement structured data markup for rich snippets",
            "Improve internal linking structure",
            "Optimize images with proper alt text and compression"
        ]
    
    def _get_fallback_action_plan(self) -> List[Dict]:
        """Fallback action plan when AI is unavailable"""
        return [
            {
                "task": "Optimize top-performing pages for target keywords",
                "priority": "High",
                "effort": 3,
                "impact": 4
            },
            {
                "task": "Create content targeting competitor keywords",
                "priority": "High",
                "effort": 4,
                "impact": 4
            },
            {
                "task": "Fix technical SEO issues",
                "priority": "Medium",
                "effort": 2,
                "impact": 3
            }
        ]

