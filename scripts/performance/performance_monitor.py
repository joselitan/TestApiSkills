"""Performance Monitoring and Reporting Script"""
import requests
import time
import json
import statistics
import psutil
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import argparse

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.token = self._get_auth_token()
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.metrics = {
            'response_times': [],
            'success_rates': [],
            'throughput': [],
            'system_metrics': [],
            'error_counts': {},
            'timestamps': []
        }
    
    def _get_auth_token(self):
        """Get authentication token"""
        try:
            response = requests.post(f"{self.base_url}/api/login", json={
                "username": "admin",
                "password": "password123"
            }, timeout=5)
            if response.status_code == 200:
                return response.json()['token']
        except:
            pass
        return None
    
    def _make_request(self, endpoint, method="GET", data=None):
        """Make HTTP request and collect metrics"""
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      headers=self.headers, timeout=10)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", 
                                       json=data, headers=self.headers, timeout=10)
            
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code < 400,
                'timestamp': datetime.now()
            }
        except Exception as e:
            end_time = time.time()
            return {
                'status_code': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'timestamp': datetime.now()
            }
        except:
            return None
    
    def run_performance_test(self, duration=60, concurrent_users=5, requests_per_user=10):
        """Run comprehensive performance test"""
        print(f"Starting performance test: {duration}s duration, {concurrent_users} users, {requests_per_user} requests/user")
        
        def user_session():
            results = []
            for _ in range(requests_per_user):
                result = self._make_request("/api/guestbook")
                results.append(result)
                time.sleep(1)  # 1 second between requests
            return results
        
        # Start system monitoring
        system_metrics = []
        test_start = time.time()
        
        # Collect baseline system metrics
        baseline_metrics = self._collect_system_metrics()
        if baseline_metrics:
            system_metrics.append(baseline_metrics)
        
        # Execute performance test
        all_results = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_session) for _ in range(concurrent_users)]
            
            # Collect system metrics during test
            while any(not future.done() for future in futures):
                metrics = self._collect_system_metrics()
                if metrics:
                    system_metrics.append(metrics)
                time.sleep(5)  # Collect metrics every 5 seconds
            
            # Collect results
            for future in futures:
                all_results.extend(future.result())
        
        test_end = time.time()
        actual_duration = test_end - test_start
        
        # Analyze results
        self._analyze_results(all_results, system_metrics, actual_duration)
        
        return self.metrics
    
    def _analyze_results(self, results, system_metrics, duration):
        """Analyze performance test results"""
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        # Response time metrics
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            self.metrics['response_times'] = {
                'min': min(response_times),
                'max': max(response_times),
                'avg': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': self._percentile(response_times, 95),
                'p99': self._percentile(response_times, 99)
            }
        
        # Success rate
        success_rate = len(successful_requests) / len(results) if results else 0
        self.metrics['success_rates'] = success_rate
        
        # Throughput
        throughput = len(results) / duration if duration > 0 else 0
        self.metrics['throughput'] = throughput
        
        # Error analysis
        error_counts = {}
        for request in failed_requests:
            error_type = str(request.get('error', 'Unknown'))
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        self.metrics['error_counts'] = error_counts
        
        # System metrics analysis
        if system_metrics:
            cpu_values = [m['cpu_percent'] for m in system_metrics if 'cpu_percent' in m]
            memory_values = [m['memory_percent'] for m in system_metrics if 'memory_percent' in m]
            
            self.metrics['system_metrics'] = {
                'cpu_avg': statistics.mean(cpu_values) if cpu_values else 0,
                'cpu_max': max(cpu_values) if cpu_values else 0,
                'memory_avg': statistics.mean(memory_values) if memory_values else 0,
                'memory_max': max(memory_values) if memory_values else 0
            }
        
        # Test metadata
        self.metrics['test_metadata'] = {
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'test_duration': duration,
            'timestamp': datetime.now().isoformat()
        }
    
    def _percentile(self, data, percentile):
        """Calculate percentile value"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def generate_report(self, output_file=None):
        """Generate performance test report"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"performance_report_{timestamp}.json"
        
        # Create reports directory if it doesn't exist
        reports_dir = "reports/performance"
        os.makedirs(reports_dir, exist_ok=True)
        report_path = os.path.join(reports_dir, output_file)
        
        # Generate comprehensive report
        report = {
            'test_summary': {
                'test_type': 'Performance Monitoring',
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics
            },
            'performance_analysis': self._generate_analysis(),
            'recommendations': self._generate_recommendations()
        }
        
        # Save report
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Performance report saved to: {report_path}")
        return report_path
    
    def _generate_analysis(self):
        """Generate performance analysis"""
        analysis = {}
        
        # Response time analysis
        if 'response_times' in self.metrics and self.metrics['response_times']:
            rt = self.metrics['response_times']
            analysis['response_time'] = {
                'status': 'GOOD' if rt['avg'] < 1.0 else 'WARNING' if rt['avg'] < 2.0 else 'CRITICAL',
                'avg_response_time': f"{rt['avg']:.3f}s",
                'p95_response_time': f"{rt['p95']:.3f}s",
                'assessment': self._assess_response_time(rt['avg'])
            }
        
        # Throughput analysis
        if 'throughput' in self.metrics:
            throughput = self.metrics['throughput']
            analysis['throughput'] = {
                'status': 'GOOD' if throughput > 10 else 'WARNING' if throughput > 5 else 'CRITICAL',
                'requests_per_second': f"{throughput:.2f}",
                'assessment': self._assess_throughput(throughput)
            }
        
        # Success rate analysis
        if 'success_rates' in self.metrics:
            success_rate = self.metrics['success_rates']
            analysis['reliability'] = {
                'status': 'GOOD' if success_rate > 0.95 else 'WARNING' if success_rate > 0.90 else 'CRITICAL',
                'success_rate': f"{success_rate:.2%}",
                'assessment': self._assess_success_rate(success_rate)
            }
        
        # System resource analysis
        if 'system_metrics' in self.metrics:
            sys_metrics = self.metrics['system_metrics']
            analysis['system_resources'] = {
                'cpu_status': 'GOOD' if sys_metrics['cpu_avg'] < 70 else 'WARNING' if sys_metrics['cpu_avg'] < 85 else 'CRITICAL',
                'memory_status': 'GOOD' if sys_metrics['memory_avg'] < 80 else 'WARNING' if sys_metrics['memory_avg'] < 90 else 'CRITICAL',
                'cpu_usage': f"{sys_metrics['cpu_avg']:.1f}%",
                'memory_usage': f"{sys_metrics['memory_avg']:.1f}%"
            }
        
        return analysis
    
    def _assess_response_time(self, avg_time):
        """Assess response time performance"""
        if avg_time < 0.5:
            return "Excellent response times"
        elif avg_time < 1.0:
            return "Good response times"
        elif avg_time < 2.0:
            return "Acceptable response times, monitor for degradation"
        else:
            return "Poor response times, optimization needed"
    
    def _assess_throughput(self, throughput):
        """Assess throughput performance"""
        if throughput > 20:
            return "High throughput capacity"
        elif throughput > 10:
            return "Good throughput capacity"
        elif throughput > 5:
            return "Moderate throughput, consider optimization"
        else:
            return "Low throughput, performance tuning required"
    
    def _assess_success_rate(self, success_rate):
        """Assess success rate"""
        if success_rate > 0.99:
            return "Excellent reliability"
        elif success_rate > 0.95:
            return "Good reliability"
        elif success_rate > 0.90:
            return "Acceptable reliability, monitor error patterns"
        else:
            return "Poor reliability, investigate failures"
    
    def _generate_recommendations(self):
        """Generate performance recommendations"""
        recommendations = []
        
        # Response time recommendations
        if 'response_times' in self.metrics and self.metrics['response_times']:
            avg_time = self.metrics['response_times']['avg']
            if avg_time > 2.0:
                recommendations.append("Consider database query optimization and caching")
            elif avg_time > 1.0:
                recommendations.append("Monitor response times and consider performance tuning")
        
        # Throughput recommendations
        if 'throughput' in self.metrics:
            throughput = self.metrics['throughput']
            if throughput < 10:
                recommendations.append("Consider scaling application instances or optimizing bottlenecks")
        
        # Success rate recommendations
        if 'success_rates' in self.metrics:
            success_rate = self.metrics['success_rates']
            if success_rate < 0.95:
                recommendations.append("Investigate error patterns and improve error handling")
        
        # System resource recommendations
        if 'system_metrics' in self.metrics:
            sys_metrics = self.metrics['system_metrics']
            if sys_metrics['cpu_avg'] > 80:
                recommendations.append("High CPU usage detected, consider CPU optimization or scaling")
            if sys_metrics['memory_avg'] > 85:
                recommendations.append("High memory usage detected, check for memory leaks or increase memory")
        
        # Error pattern recommendations
        if 'error_counts' in self.metrics and self.metrics['error_counts']:
            recommendations.append("Review error logs and implement appropriate error handling")
        
        return recommendations
    
    def print_summary(self):
        """Print performance test summary"""
        print("\n" + "="*60)
        print("PERFORMANCE TEST SUMMARY")
        print("="*60)
        
        if 'test_metadata' in self.metrics:
            metadata = self.metrics['test_metadata']
            print(f"Total Requests: {metadata['total_requests']}")
            print(f"Successful: {metadata['successful_requests']}")
            print(f"Failed: {metadata['failed_requests']}")
            print(f"Test Duration: {metadata['test_duration']:.1f}s")
        
        if 'response_times' in self.metrics and self.metrics['response_times']:
            rt = self.metrics['response_times']
            print(f"\nResponse Times:")
            print(f"  Average: {rt['avg']:.3f}s")
            print(f"  Median: {rt['median']:.3f}s")
            print(f"  95th percentile: {rt['p95']:.3f}s")
            print(f"  Min/Max: {rt['min']:.3f}s / {rt['max']:.3f}s")
        
        if 'success_rates' in self.metrics:
            print(f"\nSuccess Rate: {self.metrics['success_rates']:.2%}")
        
        if 'throughput' in self.metrics:
            print(f"Throughput: {self.metrics['throughput']:.2f} req/sec")
        
        if 'system_metrics' in self.metrics:
            sys_metrics = self.metrics['system_metrics']
            print(f"\nSystem Resources:")
            print(f"  CPU Usage: {sys_metrics['cpu_avg']:.1f}% (max: {sys_metrics['cpu_max']:.1f}%)")
            print(f"  Memory Usage: {sys_metrics['memory_avg']:.1f}% (max: {sys_metrics['memory_max']:.1f}%)")
        
        print("="*60)

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Performance Monitoring Tool')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--users', type=int, default=5, help='Number of concurrent users')
    parser.add_argument('--requests', type=int, default=10, help='Requests per user')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL to test')
    parser.add_argument('--output', help='Output report filename')
    
    args = parser.parse_args()
    
    # Run performance monitoring
    monitor = PerformanceMonitor(args.url)
    monitor.run_performance_test(args.duration, args.users, args.requests)
    monitor.print_summary()
    monitor.generate_report(args.output)

if __name__ == "__main__":
    main()