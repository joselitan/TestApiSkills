"""
AI-Powered Testing API Blueprint - Fas 6 Implementation
"""
from flask import Blueprint, request, jsonify
from models import DatabaseManager, AITestSuggestion
import json
import re
from typing import List, Dict

ai_testing_bp = Blueprint('ai_testing', __name__)
db = DatabaseManager()


@ai_testing_bp.route('/ai/suggestions', methods=['GET'])
def get_ai_suggestions():
    """Get AI test suggestions"""
    status = request.args.get('status')
    
    try:
        suggestions = db.get_ai_suggestions(status)
        return jsonify([{
            'id': s.id,
            'test_name': s.test_name,
            'test_code': s.test_code,
            'confidence_score': s.confidence_score,
            'test_type': s.test_type,
            'generated_from': s.generated_from,
            'status': s.status,
            'created_at': s.created_at
        } for s in suggestions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_testing_bp.route('/ai/analyze-failures', methods=['POST'])
def analyze_test_failures():
    """Analyze test failures and generate suggestions"""
    data = request.json
    
    if not data.get('failures'):
        return jsonify({'error': 'Failures data is required'}), 400
    
    try:
        suggestions = []
        
        for failure in data['failures']:
            analysis = analyze_failure_pattern(failure)
            if analysis:
                suggestion = AITestSuggestion(
                    test_name=analysis['test_name'],
                    test_code=analysis['test_code'],
                    confidence_score=analysis['confidence_score'],
                    test_type=analysis['test_type'],
                    generated_from='failure_analysis',
                    status='pending'
                )
                
                suggestion_id = db.create_ai_suggestion(suggestion)
                suggestions.append({
                    'id': suggestion_id,
                    'test_name': analysis['test_name'],
                    'confidence_score': analysis['confidence_score']
                })
        
        return jsonify({
            'success': True,
            'suggestions_created': len(suggestions),
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_testing_bp.route('/ai/generate-tests', methods=['POST'])
def generate_tests_from_code():
    """Generate test suggestions from code analysis"""
    data = request.json
    
    if not data.get('code'):
        return jsonify({'error': 'Code is required'}), 400
    
    try:
        suggestions = analyze_code_for_tests(data['code'], data.get('file_path', ''))
        
        created_suggestions = []
        for suggestion in suggestions:
            ai_suggestion = AITestSuggestion(
                test_name=suggestion['test_name'],
                test_code=suggestion['test_code'],
                confidence_score=suggestion['confidence_score'],
                test_type=suggestion['test_type'],
                generated_from='code_analysis',
                status='pending'
            )
            
            suggestion_id = db.create_ai_suggestion(ai_suggestion)
            created_suggestions.append({
                'id': suggestion_id,
                'test_name': suggestion['test_name'],
                'confidence_score': suggestion['confidence_score']
            })
        
        return jsonify({
            'success': True,
            'suggestions_created': len(created_suggestions),
            'suggestions': created_suggestions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_testing_bp.route('/ai/suggestions/<int:suggestion_id>/approve', methods=['POST'])
def approve_suggestion(suggestion_id):
    """Approve an AI test suggestion"""
    try:
        # Update suggestion status
        success = update_suggestion_status(suggestion_id, 'approved')
        
        if success:
            # Optionally generate actual test file
            if request.json and request.json.get('generate_file', False):
                generate_test_file(suggestion_id)
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Suggestion not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_testing_bp.route('/ai/suggestions/<int:suggestion_id>/reject', methods=['POST'])
def reject_suggestion(suggestion_id):
    """Reject an AI test suggestion"""
    try:
        success = update_suggestion_status(suggestion_id, 'rejected')
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Suggestion not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_testing_bp.route('/ai/patterns/detect', methods=['POST'])
def detect_test_patterns():
    """Detect patterns in test execution data"""
    data = request.json
    
    try:
        patterns = analyze_test_patterns(data.get('test_runs', []))
        return jsonify({
            'success': True,
            'patterns': patterns
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_testing_bp.route('/ai/coverage/gaps', methods=['POST'])
def identify_coverage_gaps():
    """Identify test coverage gaps"""
    data = request.json
    
    if not data.get('coverage_data'):
        return jsonify({'error': 'Coverage data is required'}), 400
    
    try:
        gaps = analyze_coverage_gaps(data['coverage_data'])
        
        # Generate test suggestions for gaps
        suggestions = []
        for gap in gaps:
            if gap['priority'] == 'high':
                suggestion = generate_coverage_test(gap)
                if suggestion:
                    ai_suggestion = AITestSuggestion(
                        test_name=suggestion['test_name'],
                        test_code=suggestion['test_code'],
                        confidence_score=suggestion['confidence_score'],
                        test_type='unit',
                        generated_from='coverage_analysis',
                        status='pending'
                    )
                    
                    suggestion_id = db.create_ai_suggestion(ai_suggestion)
                    suggestions.append({
                        'id': suggestion_id,
                        'test_name': suggestion['test_name'],
                        'gap': gap
                    })
        
        return jsonify({
            'success': True,
            'gaps': gaps,
            'suggestions_created': len(suggestions),
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def analyze_failure_pattern(failure: Dict) -> Dict:
    """Analyze a test failure and suggest improvements"""
    error_message = failure.get('error_message', '')
    test_name = failure.get('test_name', '')
    
    # Simple pattern matching for common failures
    if 'AssertionError' in error_message:
        return {
            'test_name': f"test_{test_name}_assertion_fix",
            'test_code': generate_assertion_test(failure),
            'confidence_score': 0.7,
            'test_type': 'unit'
        }
    elif 'TimeoutError' in error_message:
        return {
            'test_name': f"test_{test_name}_timeout_handling",
            'test_code': generate_timeout_test(failure),
            'confidence_score': 0.8,
            'test_type': 'integration'
        }
    elif 'ConnectionError' in error_message:
        return {
            'test_name': f"test_{test_name}_connection_resilience",
            'test_code': generate_connection_test(failure),
            'confidence_score': 0.75,
            'test_type': 'integration'
        }
    
    return None


def analyze_code_for_tests(code: str, file_path: str) -> List[Dict]:
    """Analyze code and suggest tests"""
    suggestions = []
    
    # Find functions that need testing
    function_pattern = r'def\s+(\w+)\s*\([^)]*\):'
    functions = re.findall(function_pattern, code)
    
    for func_name in functions:
        if not func_name.startswith('test_'):
            suggestions.append({
                'test_name': f"test_{func_name}",
                'test_code': generate_basic_test(func_name, code),
                'confidence_score': 0.6,
                'test_type': 'unit'
            })
    
    # Find classes that need testing
    class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
    classes = re.findall(class_pattern, code)
    
    for class_name in classes:
        suggestions.append({
            'test_name': f"test_{class_name.lower()}_initialization",
            'test_code': generate_class_test(class_name, code),
            'confidence_score': 0.65,
            'test_type': 'unit'
        })
    
    return suggestions


def analyze_test_patterns(test_runs: List[Dict]) -> List[Dict]:
    """Analyze test execution patterns"""
    patterns = []
    
    # Flaky test detection
    flaky_tests = detect_flaky_tests(test_runs)
    if flaky_tests:
        patterns.append({
            'type': 'flaky_tests',
            'description': 'Tests with inconsistent results',
            'tests': flaky_tests,
            'recommendation': 'Add retry logic or fix timing issues'
        })
    
    # Slow test detection
    slow_tests = detect_slow_tests(test_runs)
    if slow_tests:
        patterns.append({
            'type': 'slow_tests',
            'description': 'Tests taking longer than expected',
            'tests': slow_tests,
            'recommendation': 'Optimize test execution or add performance tests'
        })
    
    return patterns


def analyze_coverage_gaps(coverage_data: Dict) -> List[Dict]:
    """Analyze test coverage and identify gaps"""
    gaps = []
    
    for file_path, file_coverage in coverage_data.items():
        uncovered_lines = file_coverage.get('uncovered_lines', [])
        total_lines = file_coverage.get('total_lines', 0)
        
        if uncovered_lines and total_lines > 0:
            coverage_percentage = ((total_lines - len(uncovered_lines)) / total_lines) * 100
            
            priority = 'high' if coverage_percentage < 70 else 'medium' if coverage_percentage < 85 else 'low'
            
            gaps.append({
                'file': file_path,
                'uncovered_lines': uncovered_lines,
                'coverage_percentage': round(coverage_percentage, 2),
                'priority': priority
            })
    
    return gaps


def generate_assertion_test(failure: Dict) -> str:
    """Generate test code for assertion failures"""
    return f"""
def test_{failure.get('test_name', 'assertion')}_improved():
    \"\"\"Improved test based on assertion failure analysis\"\"\"
    # TODO: Add proper setup
    result = your_function()
    
    # More specific assertions
    assert result is not None, "Result should not be None"
    assert isinstance(result, expected_type), f"Expected {{expected_type}}, got {{type(result)}}"
    assert result == expected_value, f"Expected {{expected_value}}, got {{result}}"
"""


def generate_timeout_test(failure: Dict) -> str:
    """Generate test code for timeout handling"""
    return f"""
def test_{failure.get('test_name', 'timeout')}_with_retry():
    \"\"\"Test with timeout handling and retry logic\"\"\"
    import time
    from unittest.mock import patch
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = your_function_with_timeout(timeout=5)
            assert result is not None
            break
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
"""


def generate_connection_test(failure: Dict) -> str:
    """Generate test code for connection resilience"""
    return f"""
def test_{failure.get('test_name', 'connection')}_resilience():
    \"\"\"Test connection resilience and error handling\"\"\"
    from unittest.mock import patch, Mock
    import requests
    
    # Test successful connection
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        result = your_api_function()
        assert result is not None
    
    # Test connection failure handling
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        try:
            your_api_function()
            assert False, "Should have raised an exception"
        except ConnectionError:
            pass  # Expected behavior
"""


def generate_basic_test(func_name: str, code: str) -> str:
    """Generate basic test for a function"""
    return f"""
def test_{func_name}():
    \"\"\"Test {func_name} function\"\"\"
    # TODO: Add proper test implementation
    result = {func_name}()
    assert result is not None
    # Add more specific assertions based on function behavior
"""


def generate_class_test(class_name: str, code: str) -> str:
    """Generate basic test for a class"""
    return f"""
def test_{class_name.lower()}_initialization():
    \"\"\"Test {class_name} class initialization\"\"\"
    instance = {class_name}()
    assert instance is not None
    # Add tests for class methods and properties
"""


def generate_coverage_test(gap: Dict) -> Dict:
    """Generate test for coverage gap"""
    file_name = gap['file'].split('/')[-1].replace('.py', '')
    
    return {
        'test_name': f"test_{file_name}_coverage_gap",
        'test_code': f"""
def test_{file_name}_coverage_gap():
    \"\"\"Test to cover uncovered lines in {gap['file']}\"\"\"
    # Lines {gap['uncovered_lines']} need coverage
    # TODO: Implement tests for these specific lines
    pass
""",
        'confidence_score': 0.5
    }


def detect_flaky_tests(test_runs: List[Dict]) -> List[str]:
    """Detect flaky tests from run history"""
    test_results = {}
    
    for run in test_runs:
        for test_case in run.get('test_cases', []):
            test_name = test_case.get('name')
            status = test_case.get('status')
            
            if test_name not in test_results:
                test_results[test_name] = []
            test_results[test_name].append(status)
    
    flaky_tests = []
    for test_name, results in test_results.items():
        if len(set(results)) > 1 and len(results) >= 3:  # Mixed results in multiple runs
            flaky_tests.append(test_name)
    
    return flaky_tests


def detect_slow_tests(test_runs: List[Dict]) -> List[Dict]:
    """Detect slow tests"""
    slow_tests = []
    
    for run in test_runs:
        for test_case in run.get('test_cases', []):
            duration = test_case.get('duration', 0)
            if duration > 10:  # Tests taking more than 10 seconds
                slow_tests.append({
                    'name': test_case.get('name'),
                    'duration': duration,
                    'run_date': run.get('timestamp')
                })
    
    return slow_tests


def update_suggestion_status(suggestion_id: int, status: str) -> bool:
    """Update AI suggestion status"""
    import sqlite3
    
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE ai_test_suggestions SET status = ? WHERE id = ?",
        (status, suggestion_id)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success


def generate_test_file(suggestion_id: int):
    """Generate actual test file from approved suggestion"""
    # This would generate a real test file in the project
    # Implementation depends on project structure
    pass