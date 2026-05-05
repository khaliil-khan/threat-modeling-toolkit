"""
Threat Analytics Module
Provides comprehensive analytics, filtering, and reporting functionality for threats.

Author: Waleed Ahmad
Email: waleed3339321607@gmail.com
Date: May 2026
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from ..models import Threat, ThreatModel
import json

class ThreatAnalytics:
    """Handle threat analytics and statistical analysis"""
    
    @staticmethod
    def get_threat_statistics(user_id, days=30):
        """
        Get comprehensive threat statistics for a user
        
        Args:
            user_id: User ID for filtering
            days: Number of days to look back (default: 30)
        
        Returns:
            Dictionary containing threat statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all threats for user's models
        threats = Threat.query.join(ThreatModel).filter(
            and_(
                ThreatModel.user_id == user_id,
                Threat.created_at >= cutoff_date
            )
        ).all()
        
        if not threats:
            return {
                'total_threats': 0,
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
                'open_count': 0,
                'closed_count': 0,
                'avg_dread_score': 0,
                'threats_by_stride': {}
            }
        
        # Calculate statistics
        risk_counts = {
            'Critical': 0,
            'High': 0,
            'Medium': 0,
            'Low': 0
        }
        
        status_counts = {
            'Open': 0,
            'Closed': 0,
            'In Progress': 0
        }
        
        stride_counts = {}
        dread_scores = []
        
        for threat in threats:
            risk_counts[threat.risk_level] = risk_counts.get(threat.risk_level, 0) + 1
            status_counts[threat.status] = status_counts.get(threat.status, 0) + 1
            stride_counts[threat.stride_category] = stride_counts.get(threat.stride_category, 0) + 1
            dread_scores.append(threat.dread_score)
        
        avg_dread = sum(dread_scores) / len(dread_scores) if dread_scores else 0
        
        return {
            'total_threats': len(threats),
            'critical_count': risk_counts.get('Critical', 0),
            'high_count': risk_counts.get('High', 0),
            'medium_count': risk_counts.get('Medium', 0),
            'low_count': risk_counts.get('Low', 0),
            'open_count': status_counts.get('Open', 0),
            'closed_count': status_counts.get('Closed', 0),
            'in_progress_count': status_counts.get('In Progress', 0),
            'avg_dread_score': round(avg_dread, 2),
            'threats_by_stride': stride_counts,
            'timeframe_days': days
        }
    
    @staticmethod
    def get_threat_by_risk_level(model_id, user_id):
        """Get threats grouped by risk level"""
        model = ThreatModel.query.get_or_404(model_id)
        if model.user_id != user_id:
            return None
        
        threats = Threat.query.filter_by(model_id=model_id).all()
        grouped = {
            'Critical': [],
            'High': [],
            'Medium': [],
            'Low': []
        }
        
        for threat in threats:
            if threat.risk_level in grouped:
                grouped[threat.risk_level].append({
                    'id': threat.id,
                    'title': threat.title,
                    'dread_score': threat.dread_score,
                    'status': threat.status
                })
        
        return grouped
    
    @staticmethod
    def get_threat_by_stride(model_id, user_id):
        """Get threats grouped by STRIDE category"""
        model = ThreatModel.query.get_or_404(model_id)
        if model.user_id != user_id:
            return None
        
        stride_categories = ['Spoofing', 'Tampering', 'Repudiation', 'Information Disclosure', 'Denial of Service', 'Elevation of Privilege']
        threats = Threat.query.filter_by(model_id=model_id).all()
        
        grouped = {}
        for category in stride_categories:
            grouped[category] = [
                {
                    'id': t.id,
                    'title': t.title,
                    'dread_score': t.dread_score,
                    'risk_level': t.risk_level
                }
                for t in threats if t.stride_category == category
            ]
        
        return grouped


class ThreatFilter:
    """Handle threat filtering and search functionality"""
    
    @staticmethod
    def filter_threats(query_object, filters):
        """
        Apply filters to threat query
        
        Args:
            query_object: SQLAlchemy query object
            filters: Dictionary of filter criteria
        
        Returns:
            Filtered query object
        """
        if not filters:
            return query_object
        
        # Risk level filter
        if 'risk_level' in filters and filters['risk_level']:
            risk_levels = filters['risk_level'] if isinstance(filters['risk_level'], list) else [filters['risk_level']]
            query_object = query_object.filter(Threat.risk_level.in_(risk_levels))
        
        # Status filter
        if 'status' in filters and filters['status']:
            statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
            query_object = query_object.filter(Threat.status.in_(statuses))
        
        # STRIDE category filter
        if 'stride_category' in filters and filters['stride_category']:
            categories = filters['stride_category'] if isinstance(filters['stride_category'], list) else [filters['stride_category']]
            query_object = query_object.filter(Threat.stride_category.in_(categories))
        
        # DREAD score range filter
        if 'min_dread_score' in filters and filters['min_dread_score'] is not None:
            query_object = query_object.filter(Threat.dread_score >= filters['min_dread_score'])
        
        if 'max_dread_score' in filters and filters['max_dread_score'] is not None:
            query_object = query_object.filter(Threat.dread_score <= filters['max_dread_score'])
        
        # Search in title and description
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query_object = query_object.filter(
                or_(
                    Threat.title.ilike(search_term),
                    Threat.description.ilike(search_term)
                )
            )
        
        # Date range filter
        if 'date_from' in filters and filters['date_from']:
            query_object = query_object.filter(Threat.created_at >= filters['date_from'])
        
        if 'date_to' in filters and filters['date_to']:
            query_object = query_object.filter(Threat.created_at <= filters['date_to'])
        
        return query_object
    
    @staticmethod
    def search_threats(model_id, user_id, search_term, filters=None):
        """
        Comprehensive threat search with filtering
        
        Args:
            model_id: Threat model ID
            user_id: User ID for authorization
            search_term: Search term for title/description
            filters: Additional filter criteria
        
        Returns:
            List of filtered threats
        """
        model = ThreatModel.query.get_or_404(model_id)
        if model.user_id != user_id:
            return []
        
        query = Threat.query.filter_by(model_id=model_id)
        
        # Add search term
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Threat.title.ilike(search_pattern),
                    Threat.description.ilike(search_pattern),
                    Threat.countermeasure.ilike(search_pattern)
                )
            )
        
        # Apply additional filters
        if filters:
            query = ThreatFilter.filter_threats(query, filters)
        
        return query.all()


class ThreatReporter:
    """Generate threat reports and exports"""
    
    @staticmethod
    def generate_json_report(model_id, user_id):
        """
        Generate comprehensive JSON report of threats
        
        Args:
            model_id: Threat model ID
            user_id: User ID for authorization
        
        Returns:
            JSON formatted threat report
        """
        model = ThreatModel.query.get_or_404(model_id)
        if model.user_id != user_id:
            return None
        
        threats = Threat.query.filter_by(model_id=model_id).all()
        
        report = {
            'model': {
                'id': model.id,
                'name': model.name,
                'description': model.description,
                'methodology': model.methodology,
                'status': model.status,
                'created_at': model.created_at.isoformat()
            },
            'generated_at': datetime.utcnow().isoformat(),
            'total_threats': len(threats),
            'threats': []
        }
        
        for threat in threats:
            report['threats'].append({
                'id': threat.id,
                'title': threat.title,
                'description': threat.description,
                'stride_category': threat.stride_category,
                'status': threat.status,
                'risk_level': threat.risk_level,
                'dread_score': threat.dread_score,
                'dread_components': {
                    'damage': threat.damage,
                    'reproducibility': threat.reproducibility,
                    'exploitability': threat.exploitability,
                    'affected_users': threat.affected_users,
                    'discoverability': threat.discoverability
                },
                'countermeasure': threat.countermeasure,
                'created_at': threat.created_at.isoformat()
            })
        
        return json.dumps(report, indent=2)
    
    @staticmethod
    def generate_summary_report(model_id, user_id):
        """Generate a summary report with key metrics"""
        model = ThreatModel.query.get_or_404(model_id)
        if model.user_id != user_id:
            return None
        
        threats = Threat.query.filter_by(model_id=model_id).all()
        analytics = ThreatAnalytics.get_threat_by_risk_level(model_id, user_id)
        stride_grouped = ThreatAnalytics.get_threat_by_stride(model_id, user_id)
        
        report_lines = [
            "=" * 60,
            f"THREAT MODEL REPORT: {model.name}",
            "=" * 60,
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Methodology: {model.methodology}",
            f"Model Status: {model.status}",
            "",
            "SUMMARY STATISTICS",
            "-" * 60,
            f"Total Threats: {len(threats)}",
            f"Critical: {len(analytics.get('Critical', []))}",
            f"High: {len(analytics.get('High', []))}",
            f"Medium: {len(analytics.get('Medium', []))}",
            f"Low: {len(analytics.get('Low', []))}",
            "",
            "THREATS BY STRIDE CATEGORY",
            "-" * 60,
        ]
        
        for category, threat_list in stride_grouped.items():
            if threat_list:
                report_lines.append(f"{category}: {len(threat_list)} threats")
        
        report_lines.extend([
            "",
            "TOP THREATS BY DREAD SCORE",
            "-" * 60,
        ])
        
        sorted_threats = sorted(threats, key=lambda t: t.dread_score, reverse=True)[:10]
        for i, threat in enumerate(sorted_threats, 1):
            report_lines.append(f"{i}. {threat.title} - DREAD: {threat.dread_score} ({threat.risk_level})")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
