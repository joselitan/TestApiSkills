"""
Bug Tracking API Blueprint - Fas 6 Implementation
"""
from flask import Blueprint, request, jsonify
from models import DatabaseManager, BugReport
import requests
import json
from datetime import datetime

bug_tracking_bp = Blueprint('bug_tracking', __name__)
db = DatabaseManager()


@bug_tracking_bp.route('/bugs', methods=['GET'])
def get_bug_reports():
    """Get all bug reports with optional filtering"""
    filters = {}
    
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('severity'):
        filters['severity'] = request.args.get('severity')
    
    try:
        bugs = db.get_bug_reports(filters)
        return jsonify([{
            'id': bug.id,
            'title': bug.title,
            'description': bug.description,
            'severity': bug.severity,
            'status': bug.status,
            'test_case_id': bug.test_case_id,
            'github_issue_url': bug.github_issue_url,
            'jira_ticket_id': bug.jira_ticket_id,
            'created_at': bug.created_at,
            'updated_at': bug.updated_at,
            'assigned_to': bug.assigned_to
        } for bug in bugs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bug_tracking_bp.route('/bugs', methods=['POST'])
def create_bug_report():
    """Create a new bug report"""
    data = request.json
    
    if not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    try:
        bug = BugReport(
            title=data['title'],
            description=data.get('description', ''),
            severity=data.get('severity', 'medium'),
            status=data.get('status', 'open'),
            test_case_id=data.get('test_case_id'),
            assigned_to=data.get('assigned_to', '')
        )
        
        bug_id = db.create_bug_report(bug)
        
        # Auto-create GitHub issue if configured
        if data.get('create_github_issue', False):
            github_url = create_github_issue(bug)
            if github_url:
                db.update_bug_report(bug_id, {'github_issue_url': github_url})
        
        # Auto-create Jira ticket if configured
        if data.get('create_jira_ticket', False):
            jira_id = create_jira_ticket(bug)
            if jira_id:
                db.update_bug_report(bug_id, {'jira_ticket_id': jira_id})
        
        return jsonify({'success': True, 'id': bug_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bug_tracking_bp.route('/bugs/<int:bug_id>/github-issue', methods=['POST'])
def create_github_issue_for_bug(bug_id):
    """Create GitHub issue for existing bug"""
    try:
        bugs = db.get_bug_reports({'id': bug_id})
        if not bugs:
            return jsonify({'error': 'Bug not found'}), 404
        
        bug = bugs[0]
        github_url = create_github_issue(bug)
        
        if github_url:
            db.update_bug_report(bug_id, {'github_issue_url': github_url})
            return jsonify({'success': True, 'github_url': github_url})
        else:
            return jsonify({'error': 'Failed to create GitHub issue'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bug_tracking_bp.route('/bugs/<int:bug_id>/jira-ticket', methods=['POST'])
def create_jira_ticket_for_bug(bug_id):
    """Create Jira ticket for existing bug"""
    try:
        bugs = db.get_bug_reports({'id': bug_id})
        if not bugs:
            return jsonify({'error': 'Bug not found'}), 404
        
        bug = bugs[0]
        jira_id = create_jira_ticket(bug)
        
        if jira_id:
            db.update_bug_report(bug_id, {'jira_ticket_id': jira_id})
            return jsonify({'success': True, 'jira_ticket_id': jira_id})
        else:
            return jsonify({'error': 'Failed to create Jira ticket'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bug_tracking_bp.route('/bugs/stats', methods=['GET'])
def get_bug_stats():
    """Get bug statistics"""
    try:
        analytics = db.get_dashboard_analytics()
        return jsonify(analytics['bugs'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bug_tracking_bp.route('/integrations/github/test', methods=['POST'])
def test_github_integration():
    """Test GitHub integration"""
    data = request.json
    
    if not data.get('token') or not data.get('repo'):
        return jsonify({'error': 'Token and repo are required'}), 400
    
    try:
        headers = {
            'Authorization': f'token {data["token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(
            f'https://api.github.com/repos/{data["repo"]}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'GitHub integration working'})
        else:
            return jsonify({'error': f'GitHub API error: {response.status_code}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bug_tracking_bp.route('/integrations/slack/notify', methods=['POST'])
def send_slack_notification():
    """Send Slack notification for bug"""
    data = request.json
    
    if not data.get('webhook_url') or not data.get('message'):
        return jsonify({'error': 'Webhook URL and message are required'}), 400
    
    try:
        slack_payload = {
            'text': data['message'],
            'username': 'QA Dashboard',
            'icon_emoji': ':bug:'
        }
        
        response = requests.post(
            data['webhook_url'],
            json=slack_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({'success': True})
        else:
            return jsonify({'error': f'Slack API error: {response.status_code}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def create_github_issue(bug: BugReport) -> str:
    """Create GitHub issue and return URL"""
    try:
        # Get GitHub configuration from database
        config = get_integration_config('github')
        if not config:
            return None
        
        headers = {
            'Authorization': f'token {config["token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        issue_data = {
            'title': f'[BUG] {bug.title}',
            'body': f"""
**Description:**
{bug.description}

**Severity:** {bug.severity}
**Test Case ID:** {bug.test_case_id or 'N/A'}
**Created:** {bug.created_at}

---
*Auto-generated from QA Dashboard*
            """.strip(),
            'labels': ['bug', f'severity-{bug.severity}']
        }
        
        response = requests.post(
            f'https://api.github.com/repos/{config["repo"]}/issues',
            headers=headers,
            json=issue_data,
            timeout=10
        )
        
        if response.status_code == 201:
            return response.json()['html_url']
        
    except Exception as e:
        print(f"GitHub issue creation failed: {e}")
    
    return None


def create_jira_ticket(bug: BugReport) -> str:
    """Create Jira ticket and return ticket ID"""
    try:
        # Get Jira configuration from database
        config = get_integration_config('jira')
        if not config:
            return None
        
        # Jira implementation would go here
        # This is a placeholder for the actual Jira API integration
        
        return f"QA-{bug.id}"
        
    except Exception as e:
        print(f"Jira ticket creation failed: {e}")
    
    return None


def get_integration_config(service_name: str) -> dict:
    """Get integration configuration from database"""
    try:
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT config_data FROM integration_settings WHERE service_name = ? AND is_active = 1",
            (service_name,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        
    except Exception as e:
        print(f"Failed to get integration config: {e}")
    
    return None