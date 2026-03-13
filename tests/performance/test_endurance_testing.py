"""Endurance Testing - Test system performance over extended periods"""

import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest
import requests


class TestEnduranceTesting:
    """Endurance testing to verify system stability over long periods"""

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

    def _make_request(self, endpoint, method="GET", data=None):
        """Make HTTP request and measure response time"""
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(
                    f"{self.base_url}{endpoint}", headers=self.headers, timeout=10
                )
            elif method == "POST":
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers=self.headers,
                    timeout=10,
                )

            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code < 400,
                "timestamp": datetime.now(),
            }
        except Exception as e:
            end_time = time.time()
            return {
                "status_code": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(),
            }

    def test_sustained_load_endurance(self):
        """Test sustained moderate load over extended period"""
        test_duration = 60  # 1 minute for testing (would be hours in production)
        concurrent_users = 8
        requests_per_minute = 30  # Moderate sustained load

        print(
            f"Starting {test_duration}s endurance test with {concurrent_users} users..."
        )

        def endurance_user_session():
            results = []
            end_time = time.time() + test_duration
            request_interval = 60.0 / requests_per_minute  # Seconds between requests

            while time.time() < end_time:
                result = self._make_request("/api/guestbook")
                results.append(result)
                time.sleep(request_interval)

            return results

        # Execute endurance test
        start_time = time.time()
        all_results = []

        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(endurance_user_session) for _ in range(concurrent_users)
            ]
            for future in futures:
                all_results.extend(future.result())

        end_time = time.time()
        actual_duration = end_time - start_time

        # Analyze endurance results
        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)
        successful_requests = [r for r in all_results if r["success"]]
        failed_requests = [r for r in all_results if not r["success"]]

        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            # Check for performance degradation over time
            first_half = successful_requests[: len(successful_requests) // 2]
            second_half = successful_requests[len(successful_requests) // 2 :]

            first_half_avg = statistics.mean([r["response_time"] for r in first_half])
            second_half_avg = statistics.mean([r["response_time"] for r in second_half])
            degradation = (second_half_avg - first_half_avg) / first_half_avg * 100
        else:
            avg_response_time = 0
            max_response_time = 0
            min_response_time = 0
            degradation = 0

        throughput = len(all_results) / actual_duration

        print(f"Sustained Load Endurance Results:")
        print(f"- Test duration: {actual_duration:.1f}s")
        print(f"- Total requests: {len(all_results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Failed requests: {len(failed_requests)}")
        print(f"- Average response time: {avg_response_time:.3f}s")
        print(
            f"- Min/Max response time: {min_response_time:.3f}s / {max_response_time:.3f}s"
        )
        print(f"- Throughput: {throughput:.2f} req/sec")
        print(f"- Performance degradation: {degradation:.1f}%")

        # Assertions
        assert (
            success_rate >= 0.95
        ), f"Endurance success rate {success_rate:.2%} below 95%"
        assert (
            avg_response_time < 3.0
        ), f"Endurance avg response time {avg_response_time:.2f}s exceeds 3s"
        assert degradation < 50, f"Performance degradation {degradation:.1f}% too high"

    def test_memory_leak_detection(self):
        """Test for memory leaks during extended operation"""
        test_duration = 45  # 45 seconds
        concurrent_users = 5

        print(f"Starting memory leak detection test for {test_duration}s...")

        def memory_test_session():
            results = []
            end_time = time.time() + test_duration
            request_count = 0

            while time.time() < end_time:
                request_count += 1

                # Mix of operations that could cause memory leaks
                if request_count % 4 == 0:
                    # Create entry (potential memory allocation)
                    data = {
                        "name": f"Memory Test User {threading.current_thread().ident}",
                        "email": f"memory{threading.current_thread().ident}@test.com",
                        "comment": f"Memory leak test entry {request_count} "
                        + "X" * 100,  # Larger payload
                    }
                    result = self._make_request("/api/guestbook", "POST", data)
                else:
                    # Read operations
                    result = self._make_request("/api/guestbook")

                results.append(result)
                time.sleep(0.5)  # Moderate pace

            return results

        # Execute memory leak test
        all_results = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(memory_test_session) for _ in range(concurrent_users)
            ]
            for future in futures:
                all_results.extend(future.result())

        # Analyze for memory leak indicators
        successful_requests = [r for r in all_results if r["success"]]

        if len(successful_requests) >= 10:
            # Divide into time segments to check for increasing response times
            segment_size = len(successful_requests) // 5
            segments = []

            for i in range(5):
                start_idx = i * segment_size
                end_idx = (
                    start_idx + segment_size if i < 4 else len(successful_requests)
                )
                segment = successful_requests[start_idx:end_idx]

                if segment:
                    avg_time = statistics.mean([r["response_time"] for r in segment])
                    segments.append(avg_time)

            # Check for consistent increase in response times (memory leak indicator)
            increasing_trend = all(
                segments[i] <= segments[i + 1] * 1.2 for i in range(len(segments) - 1)
            )
            max_increase = (
                (max(segments) - min(segments)) / min(segments) * 100 if segments else 0
            )

            print(f"Memory Leak Detection Results:")
            print(f"- Total requests: {len(all_results)}")
            print(f"- Successful requests: {len(successful_requests)}")
            print(f"- Response time segments: {[f'{t:.3f}s' for t in segments]}")
            print(f"- Max response time increase: {max_increase:.1f}%")
            print(f"- Consistent increase trend: {increasing_trend}")

            # Assertions
            assert (
                max_increase < 100
            ), f"Response time increase {max_increase:.1f}% suggests memory leak"
            assert not (
                increasing_trend and max_increase > 50
            ), "Consistent response time increase suggests memory leak"

    def test_connection_pool_endurance(self):
        """Test connection pool behavior over extended period"""
        test_duration = 30  # 30 seconds
        burst_users = 15
        burst_interval = 5  # Burst every 5 seconds

        print(f"Starting connection pool endurance test for {test_duration}s...")

        all_results = []
        test_start = time.time()

        while time.time() - test_start < test_duration:
            # Create burst of connections
            def burst_session():
                results = []
                for _ in range(3):  # 3 requests per burst user
                    result = self._make_request("/api/guestbook")
                    results.append(result)
                return results

            burst_results = []
            with ThreadPoolExecutor(max_workers=burst_users) as executor:
                futures = [executor.submit(burst_session) for _ in range(burst_users)]
                for future in futures:
                    burst_results.extend(future.result())

            all_results.extend(burst_results)

            # Wait before next burst
            time.sleep(burst_interval)

        # Analyze connection pool results
        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)
        connection_errors = sum(
            1
            for r in all_results
            if not r["success"] and "connection" in str(r.get("error", "")).lower()
        )
        timeout_errors = sum(
            1
            for r in all_results
            if not r["success"] and "timeout" in str(r.get("error", "")).lower()
        )

        successful_requests = [r for r in all_results if r["success"]]
        if successful_requests:
            avg_response_time = statistics.mean(
                [r["response_time"] for r in successful_requests]
            )
        else:
            avg_response_time = 0

        print(f"Connection Pool Endurance Results:")
        print(f"- Total requests: {len(all_results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Connection errors: {connection_errors}")
        print(f"- Timeout errors: {timeout_errors}")
        print(f"- Average response time: {avg_response_time:.3f}s")

        # Assertions
        assert (
            success_rate >= 0.90
        ), f"Connection pool success rate {success_rate:.2%} below 90%"
        assert (
            connection_errors < len(all_results) * 0.05
        ), f"Too many connection errors: {connection_errors}"

    def test_gradual_load_increase_endurance(self):
        """Test system behavior with gradually increasing load over time"""
        phases = [
            {"users": 3, "duration": 10},
            {"users": 6, "duration": 10},
            {"users": 9, "duration": 10},
            {"users": 12, "duration": 10},
        ]

        phase_results = {}

        for i, phase in enumerate(phases):
            print(f"Phase {i+1}: {phase['users']} users for {phase['duration']}s")

            def phase_session():
                results = []
                end_time = time.time() + phase["duration"]

                while time.time() < end_time:
                    result = self._make_request("/api/guestbook")
                    results.append(result)
                    time.sleep(1.0)  # 1 request per second per user

                return results

            phase_start = time.time()
            results = []

            with ThreadPoolExecutor(max_workers=phase["users"]) as executor:
                futures = [
                    executor.submit(phase_session) for _ in range(phase["users"])
                ]
                for future in futures:
                    results.extend(future.result())

            phase_end = time.time()
            actual_duration = phase_end - phase_start

            success_rate = (
                sum(1 for r in results if r["success"]) / len(results) if results else 0
            )
            successful_requests = [r for r in results if r["success"]]
            avg_response_time = (
                statistics.mean([r["response_time"] for r in successful_requests])
                if successful_requests
                else 0
            )
            throughput = len(results) / actual_duration if actual_duration > 0 else 0

            phase_results[i + 1] = {
                "users": phase["users"],
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "throughput": throughput,
            }

        # Analyze gradual increase results
        print("Gradual Load Increase Endurance Results:")
        for phase_num, results in phase_results.items():
            print(
                f"- Phase {phase_num} ({results['users']} users): "
                f"{results['success_rate']:.2%} success, "
                f"{results['avg_response_time']:.3f}s avg, "
                f"{results['throughput']:.2f} req/sec"
            )

        # Check for performance degradation across phases
        response_times = [
            results["avg_response_time"] for results in phase_results.values()
        ]
        success_rates = [results["success_rate"] for results in phase_results.values()]

        # Assertions
        for phase_num, results in phase_results.items():
            assert (
                results["success_rate"] >= 0.85
            ), f"Phase {phase_num} success rate {results['success_rate']:.2%} below 85%"

        # Final phase should still maintain reasonable performance
        final_phase = phase_results[len(phases)]
        assert (
            final_phase["success_rate"] >= 0.80
        ), f"Final phase success rate {final_phase['success_rate']:.2%} below 80%"
        assert (
            final_phase["avg_response_time"] < 4.0
        ), f"Final phase response time {final_phase['avg_response_time']:.2f}s too slow"
