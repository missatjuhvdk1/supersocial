"""
Cookie Manager for TikTok Authentication

Handles cookie extraction, validation, and management for TikTok accounts.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class CookieManager:
    """
    Manages TikTok authentication cookies.

    Handles cookie storage, validation, and expiration tracking.
    """

    # Required TikTok cookies for authentication
    REQUIRED_COOKIES = ['sessionid', 'sid_tt', 'sid_guard']

    # Cookie domains
    TIKTOK_DOMAINS = ['.tiktok.com', 'www.tiktok.com', 'tiktok.com']

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize cookie manager.

        Args:
            storage_path: Directory to store cookies. Defaults to './cookies'
        """
        self.storage_path = Path(storage_path) if storage_path else Path('./cookies')
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cookie manager initialized with storage: {self.storage_path}")

    def save_cookies(self, cookies: List[Dict[str, Any]], account_id: str) -> str:
        """
        Save cookies for an account.

        Args:
            cookies: List of cookie dictionaries
            account_id: Unique identifier for the account

        Returns:
            Path to saved cookies file
        """
        try:
            filepath = self.storage_path / f'{account_id}_cookies.json'

            # Add metadata
            cookie_data = {
                'account_id': account_id,
                'saved_at': datetime.now().isoformat(),
                'cookies': cookies
            }

            with open(filepath, 'w') as f:
                json.dump(cookie_data, f, indent=2)

            logger.info(f"Cookies saved for account {account_id}")
            return str(filepath)

        except Exception as e:
            logger.exception(f"Failed to save cookies: {e}")
            raise

    def load_cookies(self, account_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load cookies for an account.

        Args:
            account_id: Account identifier

        Returns:
            List of cookie dictionaries or None if not found
        """
        try:
            filepath = self.storage_path / f'{account_id}_cookies.json'

            if not filepath.exists():
                logger.warning(f"Cookie file not found for account {account_id}")
                return None

            with open(filepath, 'r') as f:
                cookie_data = json.load(f)

            cookies = cookie_data.get('cookies', [])
            logger.info(f"Loaded {len(cookies)} cookies for account {account_id}")

            return cookies

        except Exception as e:
            logger.exception(f"Failed to load cookies: {e}")
            return None

    def validate_cookies(self, cookies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate cookies for completeness and expiration.

        Args:
            cookies: List of cookie dictionaries

        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'missing_cookies': List[str],
                'expired_cookies': List[str],
                'expires_soon': List[Dict]  # Cookies expiring in < 7 days
            }
        """
        result = {
            'valid': True,
            'missing_cookies': [],
            'expired_cookies': [],
            'expires_soon': []
        }

        # Check for required cookies
        cookie_names = [c.get('name') for c in cookies]

        for required in self.REQUIRED_COOKIES:
            if required not in cookie_names:
                result['missing_cookies'].append(required)
                result['valid'] = False

        # Check expiration
        current_time = time.time()
        seven_days = 7 * 24 * 60 * 60

        for cookie in cookies:
            expires = cookie.get('expires', cookie.get('expirationDate'))

            if expires:
                # Handle different expiration formats
                if isinstance(expires, str):
                    try:
                        expires = datetime.fromisoformat(expires).timestamp()
                    except:
                        continue

                # Check if expired
                if expires < current_time:
                    result['expired_cookies'].append(cookie['name'])
                    if cookie['name'] in self.REQUIRED_COOKIES:
                        result['valid'] = False

                # Check if expires soon
                elif expires < (current_time + seven_days):
                    result['expires_soon'].append({
                        'name': cookie['name'],
                        'expires_in_days': (expires - current_time) / (24 * 60 * 60)
                    })

        return result

    def is_expired(self, account_id: str, max_age_days: int = 30) -> bool:
        """
        Check if cookies are too old.

        Args:
            account_id: Account identifier
            max_age_days: Maximum age in days

        Returns:
            True if cookies are expired or too old
        """
        try:
            filepath = self.storage_path / f'{account_id}_cookies.json'

            if not filepath.exists():
                return True

            with open(filepath, 'r') as f:
                cookie_data = json.load(f)

            saved_at = datetime.fromisoformat(cookie_data.get('saved_at', ''))
            age = datetime.now() - saved_at

            if age.days > max_age_days:
                logger.info(f"Cookies for {account_id} are {age.days} days old (max: {max_age_days})")
                return True

            # Also validate cookie content
            cookies = cookie_data.get('cookies', [])
            validation = self.validate_cookies(cookies)

            return not validation['valid']

        except Exception as e:
            logger.warning(f"Error checking cookie expiration: {e}")
            return True

    def convert_chrome_cookies(self, chrome_cookies: List[Dict]) -> List[Dict[str, Any]]:
        """
        Convert Chrome cookie format to Playwright format.

        Args:
            chrome_cookies: Cookies from Chrome/browser export

        Returns:
            Cookies in Playwright format
        """
        playwright_cookies = []

        for cookie in chrome_cookies:
            # Map Chrome format to Playwright format
            playwright_cookie = {
                'name': cookie.get('name', ''),
                'value': cookie.get('value', ''),
                'domain': cookie.get('domain', '.tiktok.com'),
                'path': cookie.get('path', '/'),
                'expires': cookie.get('expirationDate', cookie.get('expires', -1)),
                'httpOnly': cookie.get('httpOnly', False),
                'secure': cookie.get('secure', True),
                'sameSite': cookie.get('sameSite', 'None')
            }

            # Convert sameSite to proper case
            if playwright_cookie['sameSite']:
                playwright_cookie['sameSite'] = playwright_cookie['sameSite'].capitalize()

            playwright_cookies.append(playwright_cookie)

        logger.info(f"Converted {len(playwright_cookies)} Chrome cookies to Playwright format")
        return playwright_cookies

    def convert_netscape_cookies(self, netscape_file: str) -> List[Dict[str, Any]]:
        """
        Convert Netscape cookie format to Playwright format.

        Args:
            netscape_file: Path to Netscape cookies.txt file

        Returns:
            Cookies in Playwright format
        """
        cookies = []

        try:
            with open(netscape_file, 'r') as f:
                for line in f:
                    # Skip comments and empty lines
                    if line.startswith('#') or not line.strip():
                        continue

                    try:
                        parts = line.strip().split('\t')

                        if len(parts) >= 7:
                            cookie = {
                                'name': parts[5],
                                'value': parts[6],
                                'domain': parts[0],
                                'path': parts[2],
                                'expires': int(parts[4]) if parts[4] != '0' else -1,
                                'secure': parts[3].upper() == 'TRUE',
                                'httpOnly': False,
                                'sameSite': 'None'
                            }
                            cookies.append(cookie)

                    except Exception as e:
                        logger.warning(f"Failed to parse cookie line: {e}")
                        continue

            logger.info(f"Converted {len(cookies)} Netscape cookies to Playwright format")
            return cookies

        except Exception as e:
            logger.exception(f"Failed to convert Netscape cookies: {e}")
            return []

    def extract_from_browser(self, browser: str = 'chrome') -> List[Dict[str, Any]]:
        """
        Extract cookies from local browser installation.

        Args:
            browser: Browser name ('chrome', 'firefox', 'edge')

        Returns:
            List of cookies
        """
        try:
            import browser_cookie3

            logger.info(f"Extracting cookies from {browser}...")

            # Get browser cookie loader
            loaders = {
                'chrome': browser_cookie3.chrome,
                'firefox': browser_cookie3.firefox,
                'edge': browser_cookie3.edge,
                'chromium': browser_cookie3.chromium,
            }

            loader = loaders.get(browser.lower())

            if not loader:
                raise ValueError(f"Unsupported browser: {browser}")

            # Load cookies for TikTok domain
            jar = loader(domain_name='tiktok.com')

            # Convert to list of dicts
            cookies = []
            for cookie in jar:
                if any(domain in cookie.domain for domain in self.TIKTOK_DOMAINS):
                    cookies.append({
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path,
                        'expires': cookie.expires if cookie.expires else -1,
                        'secure': cookie.secure,
                        'httpOnly': cookie.has_nonstandard_attr('HttpOnly'),
                        'sameSite': 'None'
                    })

            logger.info(f"Extracted {len(cookies)} cookies from {browser}")
            return cookies

        except ImportError:
            logger.error("browser_cookie3 not installed. Install with: pip install browser-cookie3")
            return []
        except Exception as e:
            logger.exception(f"Failed to extract cookies from browser: {e}")
            return []

    def get_cookie_value(self, cookies: List[Dict], cookie_name: str) -> Optional[str]:
        """
        Get value of a specific cookie by name.

        Args:
            cookies: List of cookies
            cookie_name: Name of cookie to find

        Returns:
            Cookie value or None
        """
        for cookie in cookies:
            if cookie.get('name') == cookie_name:
                return cookie.get('value')
        return None

    def filter_tiktok_cookies(self, cookies: List[Dict]) -> List[Dict]:
        """
        Filter cookies to only include TikTok-related ones.

        Args:
            cookies: List of all cookies

        Returns:
            List of TikTok cookies only
        """
        tiktok_cookies = [
            cookie for cookie in cookies
            if any(domain in cookie.get('domain', '') for domain in self.TIKTOK_DOMAINS)
        ]

        logger.info(f"Filtered {len(tiktok_cookies)} TikTok cookies from {len(cookies)} total")
        return tiktok_cookies

    def delete_cookies(self, account_id: str) -> bool:
        """
        Delete saved cookies for an account.

        Args:
            account_id: Account identifier

        Returns:
            True if deleted successfully
        """
        try:
            filepath = self.storage_path / f'{account_id}_cookies.json'

            if filepath.exists():
                filepath.unlink()
                logger.info(f"Deleted cookies for account {account_id}")
                return True
            else:
                logger.warning(f"No cookies found to delete for account {account_id}")
                return False

        except Exception as e:
            logger.exception(f"Failed to delete cookies: {e}")
            return False

    def list_accounts(self) -> List[str]:
        """
        List all accounts with saved cookies.

        Returns:
            List of account IDs
        """
        try:
            account_ids = []

            for filepath in self.storage_path.glob('*_cookies.json'):
                account_id = filepath.stem.replace('_cookies', '')
                account_ids.append(account_id)

            logger.info(f"Found {len(account_ids)} accounts with saved cookies")
            return account_ids

        except Exception as e:
            logger.exception(f"Failed to list accounts: {e}")
            return []

    def get_account_info(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about saved cookies for an account.

        Args:
            account_id: Account identifier

        Returns:
            Dictionary with account cookie info
        """
        try:
            filepath = self.storage_path / f'{account_id}_cookies.json'

            if not filepath.exists():
                return None

            with open(filepath, 'r') as f:
                cookie_data = json.load(f)

            cookies = cookie_data.get('cookies', [])
            validation = self.validate_cookies(cookies)

            saved_at = datetime.fromisoformat(cookie_data.get('saved_at', ''))
            age_days = (datetime.now() - saved_at).days

            return {
                'account_id': account_id,
                'saved_at': cookie_data.get('saved_at'),
                'age_days': age_days,
                'cookie_count': len(cookies),
                'valid': validation['valid'],
                'missing_cookies': validation['missing_cookies'],
                'expired_cookies': validation['expired_cookies'],
                'expires_soon': validation['expires_soon']
            }

        except Exception as e:
            logger.exception(f"Failed to get account info: {e}")
            return None
