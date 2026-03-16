"""
Test Cases API Blueprint - Fas 6 Implementation
"""
from flask import Blueprint, request, jsonify
from models import DatabaseManager, TestCase
import json

test_cases_bp = Blueprint('test_cases', __name__)
db = DatabaseManager()


@test_cases_bp.route('/test-cases', methods=['GET'])
def get_test_cases():
    """Get all test cases with optional filtering"""
    filters = {}
    
    # Extract query parameters
    if request.args.get('test_type'):
        filters['test_type'] = request.args.get('test_type')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    
    try:
        test_cases = db.get_test_cases(filters)
        return jsonify([{
            'id': tc.id,
            'name': tc.name,
            'description': tc.description,
            'test_type': tc.test_type,
            'priority': tc.priority,
            'status': tc.status,
            'tags': json.loads(tc.tags) if tc.tags else [],
            'created_at': tc.created_at,
            'updated_at': tc.updated_at,
            'created_by': tc.created_by
        } for tc in test_cases])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@test_cases_bp.route('/test-cases', methods=['POST'])
def create_test_case():
    """Create a new test case"""
    data = request.json
    
    if not data.get('name') or not data.get('test_type'):
        return jsonify({'error': 'Name and test_type are required'}), 400
    
    try:
        test_case = TestCase(
            name=data['name'],
            description=data.get('description', ''),
            test_type=data['test_type'],
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'active'),
            tags=json.dumps(data.get('tags', [])),
            created_by=data.get('created_by', 'system')
        )
        
        test_case_id = db.create_test_case(test_case)
        return jsonify({'success': True, 'id': test_case_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@test_cases_bp.route('/test-cases/<int:test_case_id>', methods=['PUT'])
def update_test_case(test_case_id):
    """Update an existing test case"""
    data = request.json
    
    # Prepare updates dictionary
    updates = {}
    allowed_fields = ['name', 'description', 'test_type', 'priority', 'status', 'tags', 'created_by']
    
    for field in allowed_fields:
        if field in data:
            if field == 'tags':
                updates[field] = json.dumps(data[field])
            else:
                updates[field] = data[field]
    
    if not updates:
        return jsonify({'error': 'No valid fields to update'}), 400
    
    try:
        success = db.update_test_case(test_case_id, updates)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Test case not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@test_cases_bp.route('/test-cases/<int:test_case_id>', methods=['DELETE'])
def delete_test_case(test_case_id):
    """Delete a test case"""
    try:
        success = db.delete_test_case(test_case_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Test case not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@test_cases_bp.route('/test-cases/stats', methods=['GET'])
def get_test_case_stats():
    """Get test case statistics"""
    try:
        analytics = db.get_dashboard_analytics()
        return jsonify(analytics['test_cases'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@test_cases_bp.route('/test-cases/bulk-import', methods=['POST'])
def bulk_import_test_cases():
    """Bulk import test cases from JSON"""
    data = request.json
    
    if not isinstance(data, list):
        return jsonify({'error': 'Expected array of test cases'}), 400
    
    created_count = 0
    errors = []
    
    for i, test_case_data in enumerate(data):
        try:
            if not test_case_data.get('name') or not test_case_data.get('test_type'):
                errors.append(f"Row {i+1}: Name and test_type are required")
                continue
            
            test_case = TestCase(
                name=test_case_data['name'],
                description=test_case_data.get('description', ''),
                test_type=test_case_data['test_type'],
                priority=test_case_data.get('priority', 'medium'),
                status=test_case_data.get('status', 'active'),
                tags=json.dumps(test_case_data.get('tags', [])),
                created_by=test_case_data.get('created_by', 'bulk_import')
            )
            
            db.create_test_case(test_case)
            created_count += 1
            
        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
    
    return jsonify({
        'success': True,
        'created_count': created_count,
        'errors': errors
    })