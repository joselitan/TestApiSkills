"""Stress Testing - Test system behavior under extreme load and recovery"""

import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
import requests


class TestStressTesting:
    """Stress testing to find system breaking points and test recovery"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.base_url = "http://localhost:5000"
        self.token = self._get_auth_token()
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _get_auth_token(self):
        """Get authentication token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/login",
                json={"username": "admin", "password": "password123"},
                timeout=5,
            )
            if response.status_code == 200:
                return response.json()["token"]
        except:
            pass
        return None

    def _make_request(self, endpoint, method="GET", data=None, timeout=15):
        """Make HTTP request with stress testing parameters"""
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(
                    f"{self.base_url}{endpoint}", headers=self.headers, timeout=timeout
                )
            elif method == "POST":
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers=self.headers,
                    timeout=timeout,
                )

            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code < 400,
            }
        except Exception as e:
            end_time = time.time()
            return {
                "status_code": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e),
            }

    def test_high_concurrency_stress(self):
        """Test system under high concurrent user load"""
        concurrent_users = 50  # High concurrency
        requests_per_user = 3

        def stress_user_session():
            results = []
            for _ in range(requests_per_user):
                result = self._make_request("/api/guestbook")
                results.append(result)
                # No delay - maximum stress
            return results

        # Execute high concurrency stress test
        all_results = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(stress_user_session) for _ in range(concurrent_users)
            ]
            for future in as_completed(futures):
                all_results.extend(future.result())

        end_time = time.time()
        total_duration = end_time - start_time

        # Analyze results
        successful_requests = [r for r in all_results if r["success"]]
        failed_requests = [r for r in all_results if not r["success"]]

        success_rate = len(successful_requests) / len(all_results)
        throughput = len(all_results) / total_duration

        if successful_requests:
            avg_response_time = statistics.mean(
                [r["response_time"] for r in successful_requests]
            )
            max_response_time = max([r["response_time"] for r in successful_requests])
        else:
            avg_response_time = 0
            max_response_time = 0

        print(f"High Concurrency Stress Test Results:")
        print(f"- Concurrent users: {concurrent_users}")
        print(f"- Total requests: {len(all_results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Failed requests: {len(failed_requests)}")
        print(f"- Throughput: {throughput:.2f} req/sec")
        print(f"- Average response time: {avg_response_time:.3f}s")
        print(f"- Max response time: {max_response_time:.3f}s")

        # Stress test should handle at least 60% success rate under extreme load
        assert (
            success_rate >= 0.60
        ), f"Stress test success rate {success_rate:.2%} below 60%"

    def test_rapid_fire_requests(self):
        """Test system with rapid consecutive requests"""
        rapid_requests = 100
        max_response_time = 10.0  # Allow longer response times under stress

        results = []
        start_time = time.time()

        # Fire requests as fast as possible
        for i in range(rapid_requests):
            result = self._make_request("/api/guestbook", timeout=max_response_time)
            results.append(result)

        end_time = time.time()
        total_duration = end_time - start_time

        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        success_rate = len(successful_requests) / len(results)
        throughput = len(results) / total_duration

        if successful_requests:
            avg_response_time = statistics.mean(
                [r["response_time"] for r in successful_requests]
            )
        else:
            avg_response_time = 0

        print(f"Rapid Fire Stress Test Results:")
        print(f"- Total requests: {len(results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Throughput: {throughput:.2f} req/sec")
        print(f"- Average response time: {avg_response_time:.3f}s")

        # Should handle at least 70% of rapid requests
        assert (
            success_rate >= 0.70
        ), f"Rapid fire success rate {success_rate:.2%} below 70%"

    def test_memory_stress_large_payloads(self):
        """Test system with large payload requests"""
        large_comment = "X" * 5000  # 5KB comment
        concurrent_users = 10

        def large_payload_session():
            results = []
            for i in range(3):
                data = {
                    "name": f"Stress Test User {threading.current_thread().ident}",
                    "email": f"stress{threading.current_thread().ident}@test.com",
                    "comment": large_comment,
                }
                result = self._make_request("/api/guestbook", "POST", data, timeout=20)
                results.append(result)
                time.sleep(0.5)  # Brief pause between large requests
            return results

        # Execute large payload stress test
        all_results = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(large_payload_session) for _ in range(concurrent_users)
            ]
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analyze results
        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)
        successful_requests = [r for r in all_results if r["success"]]

        if successful_requests:
            avg_response_time = statistics.mean(
                [r["response_time"] for r in successful_requests]
            )
        else:
            avg_response_time = 0

        print(f"Large Payload Stress Test Results:")
        print(f"- Payload size: 5KB per request")
        print(f"- Total requests: {len(all_results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Average response time: {avg_response_time:.3f}s")

        # Should handle large payloads with reasonable success rate
        assert (
            success_rate >= 0.80
        ), f"Large payload success rate {success_rate:.2%} below 80%"

    def test_recovery_after_stress(self):
        """Test system recovery after stress period"""
        # Phase 1: Apply stress
        stress_users = 30
        stress_duration = 5  # seconds

        def stress_phase():
            results = []
            end_time = time.time() + stress_duration
            while time.time() < end_time:
                result = self._make_request("/api/guestbook")
                results.append(result)
            return results

        print("Applying stress load...")
        stress_results = []
        with ThreadPoolExecutor(max_workers=stress_users) as executor:
            futures = [executor.submit(stress_phase) for _ in range(stress_users)]
            for future in as_completed(futures):
                stress_results.extend(future.result())

        # Phase 2: Recovery period
        print("Waiting for recovery...")
        time.sleep(3)  # Allow system to recover

        # Phase 3: Test normal operations
        recovery_results = []
        for _ in range(10):
            result = self._make_request("/api/guestbook")
            recovery_results.append(result)
            time.sleep(0.5)

        # Analyze recovery
        stress_success_rate = sum(1 for r in stress_results if r["success"]) / len(
            stress_results
        )
        recovery_success_rate = sum(1 for r in recovery_results if r["success"]) / len(
            recovery_results
        )

        recovery_response_times = [
            r["response_time"] for r in recovery_results if r["success"]
        ]
        if recovery_response_times:
            avg_recovery_time = statistics.mean(recovery_response_times)
        else:
            avg_recovery_time = 0

        print(f"Recovery Test Results:")
        print(f"- Stress phase success rate: {stress_success_rate:.2%}")
        print(f"- Recovery phase success rate: {recovery_success_rate:.2%}")
        print(f"- Recovery avg response time: {avg_recovery_time:.3f}s")

        # System should recover to normal operation
        assert (
            recovery_success_rate >= 0.90
        ), f"Recovery success rate {recovery_success_rate:.2%} below 90%"
        assert (
            avg_recovery_time < 2.0
        ), f"Recovery response time {avg_recovery_time:.2f}s too slow"
