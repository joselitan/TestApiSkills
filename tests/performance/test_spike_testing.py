"""Spike Testing - Test system behavior during sudden load spikes"""

import pytest
import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class TestSpikeTesting:
    """Spike testing to verify system handles sudden traffic increases"""

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
                    f"{self.base_url}{endpoint}", headers=self.headers, timeout=15
                )
            elif method == "POST":
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers=self.headers,
                    timeout=15,
                )

            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code < 400,
                "timestamp": start_time,
            }
        except Exception as e:
            end_time = time.time()
            return {
                "status_code": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e),
                "timestamp": start_time,
            }

    def test_sudden_user_spike(self):
        """Test sudden spike from 1 to 30 concurrent users"""
        print("Testing sudden user spike...")

        # Phase 1: Normal load (1 user)
        normal_results = []
        for _ in range(5):
            result = self._make_request("/api/guestbook")
            normal_results.append(result)
            time.sleep(0.5)

        # Phase 2: Sudden spike (30 users simultaneously)
        spike_users = 30
        requests_per_user = 3

        def spike_user_session():
            results = []
            for _ in range(requests_per_user):
                result = self._make_request("/api/guestbook")
                results.append(result)
            return results

        spike_start_time = time.time()
        spike_results = []

        with ThreadPoolExecutor(max_workers=spike_users) as executor:
            futures = [executor.submit(spike_user_session) for _ in range(spike_users)]
            for future in as_completed(futures):
                spike_results.extend(future.result())

        spike_end_time = time.time()
        spike_duration = spike_end_time - spike_start_time

        # Phase 3: Return to normal (1 user)
        time.sleep(2)  # Brief recovery period
        recovery_results = []
        for _ in range(5):
            result = self._make_request("/api/guestbook")
            recovery_results.append(result)
            time.sleep(0.5)

        # Analyze results
        normal_success_rate = sum(1 for r in normal_results if r["success"]) / len(
            normal_results
        )
        spike_success_rate = sum(1 for r in spike_results if r["success"]) / len(
            spike_results
        )
        recovery_success_rate = sum(1 for r in recovery_results if r["success"]) / len(
            recovery_results
        )

        normal_avg_time = statistics.mean(
            [r["response_time"] for r in normal_results if r["success"]]
        )
        spike_successful = [r for r in spike_results if r["success"]]
        spike_avg_time = (
            statistics.mean([r["response_time"] for r in spike_successful])
            if spike_successful
            else 0
        )
        recovery_avg_time = statistics.mean(
            [r["response_time"] for r in recovery_results if r["success"]]
        )

        throughput = len(spike_results) / spike_duration

        print(f"Sudden Spike Test Results:")
        print(f"- Normal phase success rate: {normal_success_rate:.2%}")
        print(f"- Spike phase success rate: {spike_success_rate:.2%}")
        print(f"- Recovery phase success rate: {recovery_success_rate:.2%}")
        print(f"- Normal avg response time: {normal_avg_time:.3f}s")
        print(f"- Spike avg response time: {spike_avg_time:.3f}s")
        print(f"- Recovery avg response time: {recovery_avg_time:.3f}s")
        print(f"- Spike throughput: {throughput:.2f} req/sec")

        # Assertions
        assert (
            spike_success_rate >= 0.70
        ), f"Spike success rate {spike_success_rate:.2%} below 70%"
        assert (
            recovery_success_rate >= 0.90
        ), f"Recovery success rate {recovery_success_rate:.2%} below 90%"
        assert (
            recovery_avg_time <= normal_avg_time * 2
        ), "Recovery time too slow compared to normal"

    def test_traffic_burst_pattern(self):
        """Test repeated traffic bursts"""
        burst_cycles = 3
        burst_users = 20
        burst_duration = 3  # seconds
        rest_duration = 2  # seconds

        all_burst_results = []

        for cycle in range(burst_cycles):
            print(f"Executing burst cycle {cycle + 1}/{burst_cycles}")

            # Burst phase
            def burst_session():
                results = []
                end_time = time.time() + burst_duration
                while time.time() < end_time:
                    result = self._make_request("/api/guestbook")
                    results.append(result)
                    time.sleep(0.1)  # Small delay to prevent overwhelming
                return results

            burst_results = []
            with ThreadPoolExecutor(max_workers=burst_users) as executor:
                futures = [executor.submit(burst_session) for _ in range(burst_users)]
                for future in as_completed(futures):
                    burst_results.extend(future.result())

            all_burst_results.extend(burst_results)

            # Rest phase
            if cycle < burst_cycles - 1:  # Don't rest after last cycle
                time.sleep(rest_duration)

        # Analyze burst pattern results
        success_rate = sum(1 for r in all_burst_results if r["success"]) / len(
            all_burst_results
        )
        successful_requests = [r for r in all_burst_results if r["success"]]

        if successful_requests:
            avg_response_time = statistics.mean(
                [r["response_time"] for r in successful_requests]
            )
            max_response_time = max([r["response_time"] for r in successful_requests])
        else:
            avg_response_time = 0
            max_response_time = 0

        print(f"Traffic Burst Pattern Results:")
        print(f"- Total burst cycles: {burst_cycles}")
        print(f"- Total requests: {len(all_burst_results)}")
        print(f"- Overall success rate: {success_rate:.2%}")
        print(f"- Average response time: {avg_response_time:.3f}s")
        print(f"- Max response time: {max_response_time:.3f}s")

        # Assertions
        assert (
            success_rate >= 0.75
        ), f"Burst pattern success rate {success_rate:.2%} below 75%"
        assert (
            avg_response_time < 4.0
        ), f"Burst avg response time {avg_response_time:.2f}s exceeds 4s"

    def test_gradual_spike_buildup(self):
        """Test gradual increase in load leading to spike"""
        stages = [
            {"users": 5, "duration": 2},
            {"users": 10, "duration": 2},
            {"users": 20, "duration": 2},
            {"users": 40, "duration": 3},  # Peak spike
        ]

        stage_results = {}

        for i, stage in enumerate(stages):
            print(f"Stage {i+1}: {stage['users']} users for {stage['duration']}s")

            def stage_session():
                results = []
                end_time = time.time() + stage["duration"]
                while time.time() < end_time:
                    result = self._make_request("/api/guestbook")
                    results.append(result)
                    time.sleep(0.2)
                return results

            stage_start = time.time()
            results = []

            with ThreadPoolExecutor(max_workers=stage["users"]) as executor:
                futures = [
                    executor.submit(stage_session) for _ in range(stage["users"])
                ]
                for future in as_completed(futures):
                    results.extend(future.result())

            stage_end = time.time()
            actual_duration = stage_end - stage_start

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

            stage_results[i + 1] = {
                "users": stage["users"],
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "throughput": throughput,
                "total_requests": len(results),
            }

        # Analyze gradual spike results
        print("Gradual Spike Buildup Results:")
        for stage_num, results in stage_results.items():
            print(
                f"- Stage {stage_num} ({results['users']} users): "
                f"{results['success_rate']:.2%} success, "
                f"{results['avg_response_time']:.3f}s avg, "
                f"{results['throughput']:.2f} req/sec"
            )

        # Assertions - each stage should maintain reasonable performance
        for stage_num, results in stage_results.items():
            assert (
                results["success_rate"] >= 0.70
            ), f"Stage {stage_num} success rate {results['success_rate']:.2%} below 70%"

        # Peak stage (stage 4) should handle the spike
        peak_results = stage_results[4]
        assert (
            peak_results["success_rate"] >= 0.60
        ), f"Peak spike success rate {peak_results['success_rate']:.2%} below 60%"

    def test_mixed_operation_spike(self):
        """Test spike with mixed read/write operations"""
        spike_users = 25
        spike_duration = 4

        def mixed_spike_session():
            results = []
            end_time = time.time() + spike_duration
            request_count = 0

            while time.time() < end_time:
                request_count += 1
                # 80% reads, 20% writes during spike
                if request_count % 5 == 0:  # Every 5th request is write
                    data = {
                        "name": f"Spike User {threading.current_thread().ident}",
                        "email": f"spike{threading.current_thread().ident}@test.com",
                        "comment": f"Spike test entry {request_count}",
                    }
                    result = self._make_request("/api/guestbook", "POST", data)
                else:
                    result = self._make_request("/api/guestbook")

                results.append(result)
                time.sleep(0.1)

            return results

        # Execute mixed operation spike
        all_results = []
        with ThreadPoolExecutor(max_workers=spike_users) as executor:
            futures = [executor.submit(mixed_spike_session) for _ in range(spike_users)]
            for future in as_completed(futures):
                all_results.extend(future.result())

        # Analyze mixed spike results
        success_rate = sum(1 for r in all_results if r["success"]) / len(all_results)
        successful_requests = [r for r in all_results if r["success"]]

        if successful_requests:
            avg_response_time = statistics.mean(
                [r["response_time"] for r in successful_requests]
            )
        else:
            avg_response_time = 0

        print(f"Mixed Operation Spike Results:")
        print(f"- Total requests: {len(all_results)}")
        print(f"- Success rate: {success_rate:.2%}")
        print(f"- Average response time: {avg_response_time:.3f}s")

        # Assertions
        assert (
            success_rate >= 0.65
        ), f"Mixed spike success rate {success_rate:.2%} below 65%"
        assert (
            avg_response_time < 5.0
        ), f"Mixed spike avg response time {avg_response_time:.2f}s exceeds 5s"
