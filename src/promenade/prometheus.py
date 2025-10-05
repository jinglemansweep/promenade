"""Prometheus client integration."""

import os
from typing import Any
from urllib.parse import urljoin

import requests


class PrometheusClient:
    """Client for querying Prometheus."""

    def __init__(self, base_url: str, timeout: int = 10) -> None:
        """Initialize the Prometheus client.

        Args:
            base_url: Base URL of the Prometheus server (e.g., 'http://localhost:9090')
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def query(self, query_string: str) -> Any:
        """Execute a Prometheus instant query.

        Args:
            query_string: PromQL query to execute

        Returns:
            Query result value (scalar, vector, matrix, or string)

        Raises:
            requests.RequestException: If the request fails
            ValueError: If the response format is unexpected
        """
        url = urljoin(self.base_url + "/", "api/v1/query")
        params = {"query": query_string}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                error = data.get("error", "Unknown error")
                raise ValueError(f"Prometheus query failed: {error}")

            result = data.get("data", {}).get("result", [])

            # Handle different result types
            if not result:
                return None

            # For instant vectors, return the first value
            if isinstance(result, list) and len(result) > 0:
                first_result = result[0]
                if "value" in first_result:
                    # Returns [timestamp, value]
                    return first_result["value"][1]

            return None

        except requests.RequestException as e:
            raise ValueError(f"Failed to query Prometheus: {e}") from e

    def query_batch(self, queries: list[str]) -> dict[str, Any]:
        """Execute multiple Prometheus queries efficiently.

        This uses multiple concurrent queries to Prometheus. While Prometheus doesn't
        have a native batch API, we can execute queries concurrently for better performance.

        Args:
            queries: List of PromQL query strings

        Returns:
            Dictionary mapping query string to result value

        Raises:
            requests.RequestException: If requests fail
        """
        results: dict[str, Any] = {}

        # Execute all queries (in sequence for now, could be parallelized)
        for query_string in queries:
            try:
                results[query_string] = self.query(query_string)
            except Exception as e:
                # Store the error for this specific query
                results[query_string] = f"Error: {e}"

        return results

    def close(self) -> None:
        """Close the client session."""
        self.session.close()


def create_prometheus_client_from_env(
    url_arg: str | None = None,
) -> PrometheusClient:
    """Create a Prometheus client from environment variables and arguments.

    Priority: CLI argument > Environment variable > Default

    Args:
        url_arg: Prometheus URL from CLI argument

    Returns:
        Configured PrometheusClient

    Raises:
        ValueError: If no Prometheus URL is configured
    """
    prometheus_url = url_arg or os.getenv("PROMETHEUS_URL") or os.getenv("PROM_URL")

    if not prometheus_url:
        raise ValueError(
            "Prometheus URL not configured. "
            "Provide via --prometheus-url or PROMETHEUS_URL environment variable"
        )

    timeout = int(os.getenv("PROMETHEUS_TIMEOUT", "10"))

    return PrometheusClient(base_url=prometheus_url, timeout=timeout)
