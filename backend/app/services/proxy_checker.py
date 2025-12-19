"""
Proxy Checker Service

This service verifies proxy connectivity, latency, and geolocation.
"""

import logging
import time
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ProxyCheckerError(Exception):
    """Custom exception for proxy checker errors."""
    pass


class ProxyChecker:
    """
    Proxy connectivity and latency checker.

    Features:
    - HTTP/HTTPS proxy testing
    - Latency measurement
    - IP geolocation detection
    - Timeout handling
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize proxy checker.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.test_urls = [
            "https://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "https://ifconfig.me/all.json"
        ]

    def check_proxy(self, proxy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a proxy is working and measure its latency.

        Args:
            proxy_config: Proxy configuration dictionary with:
                - host: Proxy host/IP
                - port: Proxy port
                - username: Optional username
                - password: Optional password
                - type: Proxy type (http, https, socks5)

        Returns:
            Dictionary with check results:
            {
                "is_working": bool,
                "latency_ms": int (if working),
                "ip_address": str (if working),
                "country": str (if working),
                "error": str (if not working)
            }
        """
        host = proxy_config.get("host")
        port = proxy_config.get("port")
        username = proxy_config.get("username")
        password = proxy_config.get("password")
        proxy_type = proxy_config.get("type", "http")

        logger.info(f"Checking proxy: {host}:{port}")

        try:
            # Build proxy URL
            if username and password:
                proxy_url = f"{proxy_type}://{username}:{password}@{host}:{port}"
            else:
                proxy_url = f"{proxy_type}://{host}:{port}"

            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

            # Test proxy and measure latency
            start_time = time.time()

            response = requests.get(
                self.test_urls[0],
                proxies=proxies,
                timeout=self.timeout
            )

            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)

            if response.status_code == 200:
                # Extract IP from response
                try:
                    data = response.json()
                    ip_address = data.get("origin", "").split(",")[0].strip()
                except Exception:
                    ip_address = response.text.strip()

                # Get geolocation
                country = self._get_country(ip_address)

                logger.info(
                    f"Proxy {host}:{port} is working "
                    f"(latency: {latency_ms}ms, IP: {ip_address}, country: {country})"
                )

                return {
                    "is_working": True,
                    "latency_ms": latency_ms,
                    "ip_address": ip_address,
                    "country": country
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                logger.warning(f"Proxy {host}:{port} returned error: {error_msg}")
                return {
                    "is_working": False,
                    "error": error_msg
                }

        except requests.exceptions.ProxyError as e:
            error_msg = f"Proxy connection failed: {str(e)}"
            logger.error(f"Proxy {host}:{port} - {error_msg}")
            return {
                "is_working": False,
                "error": error_msg
            }

        except requests.exceptions.Timeout:
            error_msg = f"Proxy timeout after {self.timeout}s"
            logger.error(f"Proxy {host}:{port} - {error_msg}")
            return {
                "is_working": False,
                "error": error_msg
            }

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Proxy {host}:{port} - {error_msg}")
            return {
                "is_working": False,
                "error": error_msg
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"Proxy {host}:{port} - {error_msg}")
            return {
                "is_working": False,
                "error": error_msg
            }

    def _get_country(self, ip_address: str) -> str:
        """
        Get country for an IP address using geolocation API.

        Args:
            ip_address: IP address to lookup

        Returns:
            Country code or "Unknown"
        """
        try:
            # Use free geolocation API
            response = requests.get(
                f"https://ipapi.co/{ip_address}/country/",
                timeout=5
            )

            if response.status_code == 200:
                country = response.text.strip()
                logger.debug(f"IP {ip_address} is from {country}")
                return country
            else:
                logger.warning(f"Geolocation lookup failed for {ip_address}")
                return "Unknown"

        except Exception as e:
            logger.error(f"Error getting country for {ip_address}: {str(e)}")
            return "Unknown"

    def check_multiple(self, proxy_configs: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Check multiple proxies in sequence.

        Args:
            proxy_configs: List of proxy configuration dictionaries

        Returns:
            List of check results for each proxy
        """
        results = []

        for idx, proxy_config in enumerate(proxy_configs):
            logger.info(f"Checking proxy {idx + 1}/{len(proxy_configs)}")

            result = self.check_proxy(proxy_config)
            result["proxy_config"] = proxy_config

            results.append(result)

            # Add small delay between checks to be nice to test APIs
            if idx < len(proxy_configs) - 1:
                time.sleep(1)

        working_count = sum(1 for r in results if r["is_working"])
        logger.info(
            f"Proxy check completed: {working_count}/{len(proxy_configs)} working"
        )

        return results
