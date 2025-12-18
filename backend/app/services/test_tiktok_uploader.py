"""
Unit tests for TikTok Uploader and related services.

Run with: pytest app/services/test_tiktok_uploader.py -v
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from captcha_solver import SadCaptchaSolver, CaptchaType
from tiktok_uploader import TikTokUploader, TikTokUploadError
from cookie_manager import CookieManager


# Fixtures

@pytest.fixture
def sample_cookies():
    """Sample TikTok cookies for testing."""
    return [
        {
            'name': 'sessionid',
            'value': 'test_session_12345',
            'domain': '.tiktok.com',
            'path': '/',
            'expires': 1735689600,
            'httpOnly': True,
            'secure': True,
            'sameSite': 'None'
        },
        {
            'name': 'sid_tt',
            'value': 'test_sid_67890',
            'domain': '.tiktok.com',
            'path': '/',
            'expires': 1735689600,
            'httpOnly': True,
            'secure': True,
            'sameSite': 'None'
        },
        {
            'name': 'sid_guard',
            'value': 'test_guard_abcdef',
            'domain': '.tiktok.com',
            'path': '/',
            'expires': 1735689600,
            'httpOnly': True,
            'secure': True,
            'sameSite': 'None'
        }
    ]


@pytest.fixture
def temp_cookie_file(tmp_path, sample_cookies):
    """Create temporary cookie file."""
    cookie_file = tmp_path / "cookies.json"
    with open(cookie_file, 'w') as f:
        json.dump(sample_cookies, f)
    return cookie_file


@pytest.fixture
def cookie_manager(tmp_path):
    """Create CookieManager instance with temp storage."""
    return CookieManager(storage_path=str(tmp_path / "cookies"))


# CookieManager Tests

class TestCookieManager:
    """Test CookieManager functionality."""

    def test_save_and_load_cookies(self, cookie_manager, sample_cookies):
        """Test saving and loading cookies."""
        account_id = "test_account"

        # Save cookies
        filepath = cookie_manager.save_cookies(sample_cookies, account_id)
        assert Path(filepath).exists()

        # Load cookies
        loaded = cookie_manager.load_cookies(account_id)
        assert loaded is not None
        assert len(loaded) == len(sample_cookies)
        assert loaded[0]['name'] == 'sessionid'

    def test_validate_cookies_success(self, cookie_manager, sample_cookies):
        """Test cookie validation with valid cookies."""
        result = cookie_manager.validate_cookies(sample_cookies)

        assert result['valid'] is True
        assert len(result['missing_cookies']) == 0
        assert len(result['expired_cookies']) == 0

    def test_validate_cookies_missing(self, cookie_manager):
        """Test cookie validation with missing required cookies."""
        incomplete_cookies = [
            {
                'name': 'sessionid',
                'value': 'test',
                'domain': '.tiktok.com',
                'path': '/',
                'expires': 1735689600
            }
        ]

        result = cookie_manager.validate_cookies(incomplete_cookies)

        assert result['valid'] is False
        assert 'sid_tt' in result['missing_cookies']
        assert 'sid_guard' in result['missing_cookies']

    def test_convert_chrome_cookies(self, cookie_manager):
        """Test Chrome cookie format conversion."""
        chrome_cookies = [
            {
                'name': 'sessionid',
                'value': 'test',
                'domain': '.tiktok.com',
                'expirationDate': 1735689600,
                'httpOnly': True,
                'secure': True
            }
        ]

        playwright_cookies = cookie_manager.convert_chrome_cookies(chrome_cookies)

        assert len(playwright_cookies) == 1
        assert playwright_cookies[0]['name'] == 'sessionid'
        assert playwright_cookies[0]['expires'] == 1735689600

    def test_filter_tiktok_cookies(self, cookie_manager):
        """Test filtering TikTok cookies from mixed list."""
        mixed_cookies = [
            {'name': 'tiktok_cookie', 'domain': '.tiktok.com'},
            {'name': 'other_cookie', 'domain': '.example.com'},
            {'name': 'another_tiktok', 'domain': 'www.tiktok.com'}
        ]

        filtered = cookie_manager.filter_tiktok_cookies(mixed_cookies)

        assert len(filtered) == 2
        assert all('.tiktok.com' in c['domain'] or 'www.tiktok.com' in c['domain'] for c in filtered)

    def test_get_cookie_value(self, cookie_manager, sample_cookies):
        """Test getting specific cookie value."""
        value = cookie_manager.get_cookie_value(sample_cookies, 'sessionid')
        assert value == 'test_session_12345'

        missing = cookie_manager.get_cookie_value(sample_cookies, 'nonexistent')
        assert missing is None

    def test_delete_cookies(self, cookie_manager, sample_cookies):
        """Test deleting saved cookies."""
        account_id = "test_account"

        # Save then delete
        cookie_manager.save_cookies(sample_cookies, account_id)
        assert cookie_manager.delete_cookies(account_id) is True

        # Verify deleted
        loaded = cookie_manager.load_cookies(account_id)
        assert loaded is None

    def test_list_accounts(self, cookie_manager, sample_cookies):
        """Test listing accounts with saved cookies."""
        # Save cookies for multiple accounts
        cookie_manager.save_cookies(sample_cookies, "account1")
        cookie_manager.save_cookies(sample_cookies, "account2")
        cookie_manager.save_cookies(sample_cookies, "account3")

        accounts = cookie_manager.list_accounts()

        assert len(accounts) == 3
        assert "account1" in accounts
        assert "account2" in accounts
        assert "account3" in accounts

    def test_get_account_info(self, cookie_manager, sample_cookies):
        """Test getting account cookie information."""
        account_id = "test_account"
        cookie_manager.save_cookies(sample_cookies, account_id)

        info = cookie_manager.get_account_info(account_id)

        assert info is not None
        assert info['account_id'] == account_id
        assert info['cookie_count'] == len(sample_cookies)
        assert info['valid'] is True


# SadCaptchaSolver Tests

class TestSadCaptchaSolver:
    """Test SadCaptchaSolver functionality."""

    @pytest.fixture
    def captcha_solver(self):
        """Create captcha solver instance."""
        return SadCaptchaSolver(api_key='test_api_key')

    @patch('captcha_solver.requests.Session.post')
    def test_solve_puzzle_success(self, mock_post, captcha_solver):
        """Test successful puzzle captcha solving."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'x_position': 150,
            'y_position': 20,
            'duration': 2.5,
            'solution_id': 'sol_12345'
        }
        mock_post.return_value = mock_response

        # Test solve
        image_data = b'fake_image_data'
        result = captcha_solver.solve_puzzle(image_data)

        assert result is not None
        assert result['success'] is True
        assert result['x_position'] == 150
        assert result['y_position'] == 20
        assert result['solution_id'] == 'sol_12345'

    @patch('captcha_solver.requests.Session.post')
    def test_solve_puzzle_failure(self, mock_post, captcha_solver):
        """Test failed puzzle captcha solving."""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': False,
            'error': 'Invalid captcha image'
        }
        mock_post.return_value = mock_response

        # Test solve
        result = captcha_solver.solve_puzzle(b'bad_data')

        assert result is not None
        assert result['success'] is False
        assert 'error' in result

    @patch('captcha_solver.requests.Session.post')
    def test_solve_rotate(self, mock_post, captcha_solver):
        """Test rotation captcha solving."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'angle': 45,
            'duration': 1.5,
            'solution_id': 'sol_67890'
        }
        mock_post.return_value = mock_response

        result = captcha_solver.solve_rotate(b'rotate_image_data')

        assert result['success'] is True
        assert result['angle'] == 45

    @patch('captcha_solver.requests.Session.post')
    def test_solve_shapes(self, mock_post, captcha_solver):
        """Test 3D shapes captcha solving."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'shapes': ['cube', 'sphere'],
            'coordinates': [
                {'x': 100, 'y': 150},
                {'x': 200, 'y': 250}
            ],
            'solution_id': 'sol_shapes'
        }
        mock_post.return_value = mock_response

        result = captcha_solver.solve_shapes(b'shapes_image_data')

        assert result['success'] is True
        assert len(result['shapes']) == 2
        assert len(result['coordinates']) == 2

    @patch('captcha_solver.requests.Session.post')
    def test_report_solution(self, mock_post, captcha_solver):
        """Test reporting solution success/failure."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Should not raise exception
        captcha_solver.report_solution('sol_12345', success=True)

        assert mock_post.called


# TikTokUploader Tests

class TestTikTokUploader:
    """Test TikTokUploader functionality."""

    @pytest.fixture
    def uploader(self, temp_cookie_file):
        """Create uploader instance."""
        return TikTokUploader(
            cookies=str(temp_cookie_file),
            headless=True,
            captcha_api_key='test_key'
        )

    def test_initialization(self, uploader):
        """Test uploader initialization."""
        assert uploader is not None
        assert uploader.headless is True
        assert uploader.captcha_solver is not None

    def test_default_profile(self, uploader):
        """Test default profile generation."""
        profile = uploader._default_profile()

        assert 'user_agent' in profile
        assert 'viewport' in profile
        assert 'timezone' in profile
        assert 'locale' in profile

    def test_format_caption(self, uploader):
        """Test caption formatting with hashtags."""
        caption = "My awesome video"
        hashtags = ['fyp', 'viral', 'trending']

        formatted = uploader._format_caption(caption, hashtags)

        assert 'My awesome video' in formatted
        assert '#fyp' in formatted
        assert '#viral' in formatted
        assert '#trending' in formatted

    def test_format_caption_no_hashtags(self, uploader):
        """Test caption formatting without hashtags."""
        caption = "Simple caption"
        formatted = uploader._format_caption(caption, None)

        assert formatted == "Simple caption"

    def test_format_caption_strip_hash(self, uploader):
        """Test that hashtags with # are handled correctly."""
        caption = "Test"
        hashtags = ['#tag1', 'tag2']

        formatted = uploader._format_caption(caption, hashtags)

        # Should have only one # per tag
        assert '#tag1' in formatted
        assert '#tag2' in formatted
        assert '##' not in formatted


# Integration Tests (require actual browser - marked as slow)

@pytest.mark.slow
class TestTikTokUploaderIntegration:
    """Integration tests requiring actual browser setup."""

    @pytest.mark.asyncio
    async def test_browser_setup(self, uploader):
        """Test browser setup and teardown."""
        try:
            await uploader.setup_browser()

            assert uploader.browser is not None
            assert uploader.context is not None
            assert uploader.page is not None

        finally:
            await uploader.close()

    @pytest.mark.asyncio
    async def test_login_with_cookies(self, uploader):
        """Test cookie-based authentication."""
        try:
            await uploader.setup_browser()

            # This will fail with test cookies, but tests the flow
            with pytest.raises(TikTokUploadError):
                await uploader.login_with_cookies(uploader.cookies)

        finally:
            await uploader.close()


# Performance Tests

class TestPerformance:
    """Performance and stress tests."""

    def test_cookie_manager_large_batch(self, cookie_manager, sample_cookies):
        """Test cookie manager with many accounts."""
        import time

        start = time.time()

        # Save 100 accounts
        for i in range(100):
            cookie_manager.save_cookies(sample_cookies, f"account_{i}")

        # List all
        accounts = cookie_manager.list_accounts()
        assert len(accounts) == 100

        end = time.time()
        duration = end - start

        # Should complete in reasonable time
        assert duration < 5.0  # 5 seconds for 100 accounts

    def test_cookie_validation_speed(self, cookie_manager):
        """Test cookie validation performance."""
        import time

        # Create large cookie list
        cookies = []
        for i in range(50):
            cookies.append({
                'name': f'cookie_{i}',
                'value': f'value_{i}',
                'domain': '.tiktok.com',
                'path': '/',
                'expires': 1735689600
            })

        start = time.time()

        for _ in range(100):
            cookie_manager.validate_cookies(cookies)

        end = time.time()
        duration = end - start

        # Should be very fast
        assert duration < 1.0  # 100 validations in < 1 second


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
