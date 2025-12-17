"""
Prometheus and Grafana Verification Test Script
================================================
This script verifies that Prometheus and Grafana are properly configured
and working in the Pharma FastAPI microservices project.
"""

import requests
import json
import sys
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    PASS = "[PASS]"
    FAIL = "[FAIL]"
    WARN = "[WARN]"
    SKIP = "[SKIP]"


@dataclass
class TestResult:
    test_name: str
    status: TestStatus
    message: str
    details: str = ""


class PrometheusGrafanaVerifier:
    def __init__(self):
        self.results: List[TestResult] = []
        self.services = {
            "auth": "http://localhost:9001",
            "catalog": "http://localhost:9002",
            "orders": "http://localhost:9003",
            "inventory": "http://localhost:9004"
        }
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3000"

    def test_service_health(self, service_name: str, base_url: str) -> TestResult:
        """Test if a service is healthy"""
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return TestResult(
                        test_name=f"{service_name.upper()} Service Health",
                        status=TestStatus.PASS,
                        message=f"{service_name} service is healthy",
                        details=f"Response: {data}"
                    )
            return TestResult(
                test_name=f"{service_name.upper()} Service Health",
                status=TestStatus.FAIL,
                message=f"Unexpected response from {service_name}",
                details=f"Status: {response.status_code}, Body: {response.text[:200]}"
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                test_name=f"{service_name.upper()} Service Health",
                status=TestStatus.FAIL,
                message=f"{service_name} service is not accessible",
                details=str(e)
            )

    def test_service_metrics(self, service_name: str, base_url: str) -> TestResult:
        """Test if a service exposes Prometheus metrics"""
        try:
            response = requests.get(f"{base_url}/metrics", timeout=5)
            if response.status_code == 200:
                content = response.text
                # Check for expected metrics
                required_metrics = [
                    "http_requests_total",
                    "http_request_duration_seconds"
                ]
                missing_metrics = [m for m in required_metrics if m not in content]
                
                if not missing_metrics:
                    metric_count = content.count('\n')
                    return TestResult(
                        test_name=f"{service_name.upper()} Metrics Endpoint",
                        status=TestStatus.PASS,
                        message=f"{service_name} exposes Prometheus metrics",
                        details=f"Found {metric_count} metric lines"
                    )
                else:
                    return TestResult(
                        test_name=f"{service_name.upper()} Metrics Endpoint",
                        status=TestStatus.WARN,
                        message=f"Metrics missing: {', '.join(missing_metrics)}",
                        details=f"Metrics endpoint exists but missing expected metrics"
                    )
            return TestResult(
                test_name=f"{service_name.upper()} Metrics Endpoint",
                status=TestStatus.FAIL,
                message=f"Cannot access metrics endpoint",
                details=f"Status: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                test_name=f"{service_name.upper()} Metrics Endpoint",
                status=TestStatus.FAIL,
                message=f"Metrics endpoint not accessible",
                details=str(e)
            )

    def test_prometheus_health(self) -> TestResult:
        """Test if Prometheus is healthy"""
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            if response.status_code == 200 and "Healthy" in response.text:
                return TestResult(
                    test_name="Prometheus Health",
                    status=TestStatus.PASS,
                    message="Prometheus is healthy and running",
                    details=response.text.strip()
                )
            return TestResult(
                test_name="Prometheus Health",
                status=TestStatus.FAIL,
                message="Prometheus health check failed",
                details=f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                test_name="Prometheus Health",
                status=TestStatus.FAIL,
                message="Cannot connect to Prometheus",
                details=str(e)
            )

    def test_prometheus_targets(self) -> TestResult:
        """Test if Prometheus is scraping all configured targets"""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    active_targets = data["data"]["activeTargets"]
                    
                    # Analyze targets
                    target_results = []
                    for target in active_targets:
                        job = target["labels"]["job"]
                        instance = target["labels"]["instance"]
                        health = target["health"]
                        target_results.append(f"{job} ({instance}): {health}")
                    
                    up_targets = [t for t in target_results if "up" in t.lower()]
                    down_targets = [t for t in target_results if "up" not in t.lower()]
                    
                    if not down_targets:
                        return TestResult(
                            test_name="Prometheus Targets",
                            status=TestStatus.PASS,
                            message=f"All {len(up_targets)} targets are UP",
                            details=f"UP: {', '.join(up_targets)}"
                        )
                    else:
                        return TestResult(
                            test_name="Prometheus Targets",
                            status=TestStatus.WARN,
                            message=f"{len(down_targets)} target(s) are DOWN",
                            details=f"DOWN: {', '.join(down_targets)} | UP: {', '.join(up_targets)}"
                        )
            return TestResult(
                test_name="Prometheus Targets",
                status=TestStatus.FAIL,
                message="Failed to get targets from Prometheus",
                details=f"Status: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                test_name="Prometheus Targets",
                status=TestStatus.FAIL,
                message="Cannot query Prometheus targets API",
                details=str(e)
            )

    def test_prometheus_metrics_collection(self) -> TestResult:
        """Test if Prometheus is collecting metrics"""
        try:
            # Query for http_requests_total metric
            query = "http_requests_total"
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    results = data["data"]["result"]
                    if results:
                        service_counts = {}
                        for result in results:
                            service = result["metric"].get("service", "unknown")
                            value = result["value"][1]
                            service_counts[service] = value
                        
                        return TestResult(
                            test_name="Metrics Collection",
                            status=TestStatus.PASS,
                            message=f"Prometheus is collecting metrics from {len(service_counts)} service(s)",
                            details=f"Services: {', '.join(service_counts.keys())}"
                        )
                    else:
                        return TestResult(
                            test_name="Metrics Collection",
                            status=TestStatus.WARN,
                            message="No metrics collected yet",
                            details="Prometheus may need time to collect data or services need traffic"
                        )
            return TestResult(
                test_name="Metrics Collection",
                status=TestStatus.FAIL,
                message="Failed to query metrics",
                details=f"Status: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                test_name="Metrics Collection",
                status=TestStatus.FAIL,
                message="Cannot query Prometheus",
                details=str(e)
            )

    def test_grafana_accessibility(self) -> TestResult:
        """Test if Grafana is accessible"""
        try:
            response = requests.get(self.grafana_url, timeout=5, allow_redirects=False)
            # Grafana typically redirects to /login if not authenticated
            if response.status_code in [200, 302, 303]:
                return TestResult(
                    test_name="Grafana Accessibility",
                    status=TestStatus.PASS,
                    message="Grafana is accessible",
                    details=f"Status: {response.status_code} - Grafana UI is running"
                )
            return TestResult(
                test_name="Grafana Accessibility",
                status=TestStatus.FAIL,
                message="Unexpected Grafana response",
                details=f"Status: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            return TestResult(
                test_name="Grafana Accessibility",
                status=TestStatus.FAIL,
                message="Cannot connect to Grafana",
                details=str(e)
            )

    def run_all_tests(self):
        """Run all verification tests"""
        print("=" * 70)
        print("PROMETHEUS & GRAFANA VERIFICATION TEST SUITE")
        print("=" * 70)
        print()

        # Test Prometheus first
        print("Testing Prometheus...")
        self.results.append(self.test_prometheus_health())
        self.results.append(self.test_prometheus_targets())
        self.results.append(self.test_prometheus_metrics_collection())
        print()

        # Test Grafana
        print("Testing Grafana...")
        self.results.append(self.test_grafana_accessibility())
        print()

        # Test all services
        print("Testing Services...")
        for service_name, base_url in self.services.items():
            self.results.append(self.test_service_health(service_name, base_url))
            self.results.append(self.test_service_metrics(service_name, base_url))
        print()

        # Print results
        self.print_results()

    def print_results(self):
        """Print test results in a formatted table"""
        print("=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print()

        for result in self.results:
            print(f"{result.status.value} {result.test_name}")
            print(f"   {result.message}")
            if result.details:
                print(f"   Details: {result.details}")
            print()

        # Summary
        pass_count = sum(1 for r in self.results if r.status == TestStatus.PASS)
        fail_count = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        warn_count = sum(1 for r in self.results if r.status == TestStatus.WARN)
        total_count = len(self.results)

        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {total_count}")
        print(f"Passed:   {pass_count}")
        print(f"Failed:   {fail_count}")
        print(f"Warnings: {warn_count}")
        print()

        if fail_count == 0:
            print("ALL CRITICAL TESTS PASSED!")
            print("Prometheus and Grafana are configured correctly.")
        else:
            print("SOME TESTS FAILED")
            print("Please check the failed tests above and ensure all services are running.")
            print("Run 'docker-compose up -d' to start all services if needed.")

        print("=" * 70)

        # Return exit code
        sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    # Redirect stdout to a file while keeping it on console
    class Tee:
        def __init__(self, name, mode):
            self.file = open(name, mode, encoding="utf-8")
            self.stdout = sys.stdout
        def write(self, data):
            self.file.write(data)
            self.stdout.write(data)
        def flush(self):
            if not self.file.closed:
                self.file.flush()
            self.stdout.flush()
        def close(self):
            self.file.close()

    tee = Tee("verification_report.txt", "w")
    sys.stdout = tee
    
    try:
        verifier = PrometheusGrafanaVerifier()
        verifier.run_all_tests()
    finally:
        tee.close()
