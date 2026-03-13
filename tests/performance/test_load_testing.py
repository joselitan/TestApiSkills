"""Load Testing - Test system performance under normal expected load"""

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
import requests


class TestLoadTesting:
    """Load testing to verify system performance under normal load"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.base_url = "http://localhost:8080"
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
            }
        except Exception as e:
            end_time = time.time()
            return {
                "status_code": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e),
            }

    def test_concurrent_read_load(self):
        """Test concurrent read operations under normal load"""
        concurrent_users = 10
        requests_per_user = 5

        def user_session():
            results = []
            for _ in range(requests_per_user):
                result = self._make_request("/api/guestbook")
                results.append(result)
                time.sleep(0.1)  # Small delay between requests
            return results

        # Execute concurrent requests
        all_results = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_session) for _ in range(concurrent_users)]
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analyze results
        response_times = [r["response_time"] for r in all_results if r["success"]]
        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)

        # Assertions
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
        assert (
            statistics.mean(response_times) < 2.0
        ), f"Average response time {statistics.mean(response_times):.2f}s exceeds 2s"
        assert (
            max(response_times) < 5.0
        ), f"Max response time {max(response_times):.2f}s exceeds 5s"

        print(f"Load Test Results:")
        print(f"- Total requests: {len(all_results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Average response time: {statistics.mean(response_times):.3f}s")
        print(f"- Max response time: {max(response_times):.3f}s")

    def test_mixed_operations_load(self):
        """Test mixed read/write operations under load"""
        concurrent_users = 8

        def mixed_user_session():
            results = []
            # 70% reads, 30% writes (realistic ratio)
            operations = ["read"] * 7 + ["write"] * 3

            for op in operations:
                if op == "read":
                    result = self._make_request("/api/guestbook")
                else:
                    data = {
                        "name": f"Load Test User {time.time()}",
                        "email": f"load{int(time.time())}@test.com",
                        "comment": "Load testing entry",
                    }
                    result = self._make_request("/api/guestbook", "POST", data)

                results.append(result)
                time.sleep(0.2)  # Realistic user think time

            return results

        # Execute mixed load test
        all_results = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(mixed_user_session) for _ in range(concurrent_users)
            ]
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analyze results
        read_results = [r for r in all_results if r.get("method", "GET") == "GET"]
        write_results = [r for r in all_results if r.get("method", "POST") == "POST"]

        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)
        avg_response_time = statistics.mean(
            [r["response_time"] for r in all_results if r["success"]]
        )

        # Assertions
        assert (
            success_rate >= 0.90
        ), f"Mixed load success rate {success_rate:.2%} below 90%"
        assert (
            avg_response_time < 3.0
        ), f"Mixed load avg response time {avg_response_time:.2f}s exceeds 3s"

        print(f"Mixed Load Test Results:")
        print(f"- Total operations: {len(all_results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Average response time: {avg_response_time:.3f}s")

    def test_pagination_load(self):
        """Test pagination performance under load"""
        concurrent_users = 5
        pages_per_user = 10

        def pagination_session():
            results = []
            for page in range(1, pages_per_user + 1):
                result = self._make_request(f"/api/guestbook?page={page}&limit=10")
                results.append(result)
                time.sleep(0.1)
            return results

        # Execute pagination load test
        all_results = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(pagination_session) for _ in range(concurrent_users)
            ]
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analyze results
        response_times = [r["response_time"] for r in all_results if r["success"]]
        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)

        # Assertions
        assert (
            success_rate >= 0.95
        ), f"Pagination load success rate {success_rate:.2%} below 95%"
        assert (
            statistics.mean(response_times) < 1.5
        ), f"Pagination avg response time {statistics.mean(response_times):.2f}s exceeds 1.5s"

        print(f"Pagination Load Test Results:")
        print(f"- Total pagination requests: {len(all_results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Average response time: {statistics.mean(response_times):.3f}s")
