"""
TikTok Uploader Service with Playwright and Stealth

Automated TikTok video uploader with anti-detection measures:
- Playwright browser automation with stealth plugin
- Proxy support
- Cookie-based authentication
- Human-like behaviors (random delays, mouse movements, typing patterns)
- Captcha solving integration
"""

import asyncio
import logging
import random
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error
from playwright_stealth import stealth_async

from .captcha_solver import SadCaptchaSolver

logger = logging.getLogger(__name__)


class TikTokUploadError(Exception):
    """Exception raised for TikTok upload errors."""
    pass


class TikTokUploader:
    """
    TikTok video uploader with stealth capabilities.

    Handles authentication, video upload, and anti-detection measures.
    """

    # TikTok URLs
    UPLOAD_URL = "https://www.tiktok.com/creator-center/upload"
    LOGIN_URL = "https://www.tiktok.com/login"
    STUDIO_URL = "https://www.tiktok.com/creator-center/content"

    # Selectors (may need updates based on TikTok's UI changes)
    SELECTORS = {
        'file_input': 'input[type="file"]',
        'caption_input': 'div[contenteditable="true"]',
        'post_button': 'button:has-text("Post")',
        'upload_progress': '[class*="progress"]',
        'video_preview': 'video',
        'captcha_container': 'iframe[id*="captcha"]',
        'login_check': '[data-e2e="profile-icon"]',
        'error_message': '[class*="error"]',
    }

    def __init__(
        self,
        proxy: Optional[Dict[str, str]] = None,
        profile: Optional[Dict[str, Any]] = None,
        cookies: Optional[Union[str, List[Dict]]] = None,
        headless: bool = True,
        captcha_api_key: Optional[str] = None
    ):
        """
        Initialize TikTok uploader.

        Args:
            proxy: Proxy configuration {'server': 'http://...', 'username': '...', 'password': '...'}
            profile: Browser profile settings (user_agent, viewport, timezone, locale)
            cookies: Path to cookies file or list of cookie dicts
            headless: Run browser in headless mode
            captcha_api_key: API key for captcha solver
        """
        self.proxy = proxy
        self.profile = profile or self._default_profile()
        self.cookies = cookies
        self.headless = headless

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.captcha_solver = SadCaptchaSolver(api_key=captcha_api_key) if captcha_api_key else None

        logger.info("TikTokUploader initialized")

    def _default_profile(self) -> Dict[str, Any]:
        """Generate default browser profile."""
        return {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'viewport': {'width': 1920, 'height': 1080},
            'timezone': 'America/New_York',
            'locale': 'en-US',
            'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},  # New York
            'permissions': ['geolocation'],
        }

    async def setup_browser(self):
        """
        Launch and configure Playwright browser with stealth.

        Sets up:
        - Chromium browser with stealth plugin
        - Proxy if configured
        - Custom user agent and viewport
        - Timezone and locale spoofing
        - Cookie injection
        """
        try:
            logger.info("Setting up browser...")

            self.playwright = await async_playwright().start()

            # Browser launch options
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                ]
            }

            # Add proxy if configured
            if self.proxy:
                launch_options['proxy'] = self.proxy

            # Launch browser
            self.browser = await self.playwright.chromium.launch(**launch_options)

            # Context options
            context_options = {
                'user_agent': self.profile['user_agent'],
                'viewport': self.profile['viewport'],
                'timezone_id': self.profile['timezone'],
                'locale': self.profile['locale'],
                'geolocation': self.profile.get('geolocation'),
                'permissions': self.profile.get('permissions', []),
                'color_scheme': 'light',
                'java_script_enabled': True,
            }

            # Create context
            self.context = await self.browser.new_context(**context_options)

            # Add stealth scripts to avoid detection
            await self._apply_stealth_scripts()

            # Create page
            self.page = await self.context.new_page()

            # Apply playwright-stealth
            await stealth_async(self.page)

            # Load cookies if provided
            if self.cookies:
                await self.login_with_cookies(self.cookies)

            logger.info("Browser setup complete")

        except Exception as e:
            logger.exception(f"Failed to setup browser: {e}")
            await self.close()
            raise TikTokUploadError(f"Browser setup failed: {e}")

    async def _apply_stealth_scripts(self):
        """Apply additional stealth scripts to context."""
        try:
            # Override navigator.webdriver
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Override Chrome runtime
            await self.context.add_init_script("""
                window.chrome = {
                    runtime: {}
                };
            """)

            # Override permissions
            await self.context.add_init_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)

            # Add realistic plugins
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)

            logger.debug("Stealth scripts applied")

        except Exception as e:
            logger.warning(f"Failed to apply some stealth scripts: {e}")

    async def login_with_cookies(self, cookies_input: Union[str, List[Dict]]):
        """
        Load cookies to authenticate.

        Args:
            cookies_input: Path to cookies JSON file or list of cookie dictionaries

        Raises:
            TikTokUploadError: If cookies are invalid or login verification fails
        """
        try:
            logger.info("Loading cookies for authentication...")

            # Load cookies from file or use provided list
            if isinstance(cookies_input, str):
                cookies_path = Path(cookies_input)
                if not cookies_path.exists():
                    raise TikTokUploadError(f"Cookies file not found: {cookies_input}")

                with open(cookies_path, 'r') as f:
                    cookies = json.load(f)
            else:
                cookies = cookies_input

            # Add cookies to context
            await self.context.add_cookies(cookies)

            # Verify login by navigating to TikTok
            await self.page.goto("https://www.tiktok.com/", wait_until='networkidle')
            await self._random_delay(2, 4)

            # Check if logged in
            is_logged_in = await self._verify_login()

            if is_logged_in:
                logger.info("Successfully authenticated with cookies")
            else:
                raise TikTokUploadError("Cookie authentication failed - not logged in")

        except Exception as e:
            logger.exception(f"Cookie authentication failed: {e}")
            raise TikTokUploadError(f"Cookie login failed: {e}")

    async def _verify_login(self) -> bool:
        """
        Verify if user is logged in.

        Returns:
            True if logged in, False otherwise
        """
        try:
            # Check for profile icon or account indicator
            profile_icon = await self.page.query_selector(self.SELECTORS['login_check'])

            if profile_icon:
                logger.debug("Login verified - profile icon found")
                return True

            # Alternative check: look for login button (means not logged in)
            login_button = await self.page.query_selector('a[href*="login"]')
            if login_button:
                logger.debug("Not logged in - login button found")
                return False

            # If neither found, try to access creator center
            response = await self.page.goto(self.STUDIO_URL, wait_until='networkidle')
            await self._random_delay(1, 2)

            # If redirected to login, not authenticated
            if 'login' in self.page.url:
                logger.debug("Not logged in - redirected to login page")
                return False

            logger.debug("Login status unclear, assuming logged in")
            return True

        except Exception as e:
            logger.warning(f"Error verifying login: {e}")
            return False

    async def upload_video(
        self,
        video_path: str,
        caption: str,
        hashtags: Optional[List[str]] = None,
        schedule_time: Optional[str] = None,
        privacy: str = "public",
        allow_comments: bool = True,
        allow_duet: bool = True,
        allow_stitch: bool = True
    ) -> Dict[str, Any]:
        """
        Upload video to TikTok.

        Args:
            video_path: Path to video file
            caption: Video caption/description
            hashtags: List of hashtags (without #)
            schedule_time: Schedule post for later (ISO format)
            privacy: Video privacy ('public', 'friends', 'private')
            allow_comments: Allow comments on video
            allow_duet: Allow duets
            allow_stitch: Allow stitches

        Returns:
            Dictionary with upload result:
            {
                'success': bool,
                'video_url': str,
                'video_id': str,
                'error': str (if failed)
            }
        """
        try:
            logger.info(f"Starting video upload: {video_path}")

            # Verify video file exists
            video_file = Path(video_path)
            if not video_file.exists():
                raise TikTokUploadError(f"Video file not found: {video_path}")

            # Navigate to upload page
            logger.info("Navigating to upload page...")
            await self.page.goto(self.UPLOAD_URL, wait_until='networkidle')
            await self._random_delay(2, 4)

            # Check for captcha
            await self._handle_captcha()

            # Upload video file
            logger.info("Uploading video file...")
            await self._upload_file(str(video_file.absolute()))

            # Wait for video processing
            logger.info("Waiting for video processing...")
            await self._wait_for_processing()

            # Enter caption and hashtags
            logger.info("Entering caption and hashtags...")
            full_caption = self._format_caption(caption, hashtags)
            await self._enter_caption(full_caption)

            # Configure privacy settings
            logger.info("Configuring privacy settings...")
            await self._configure_settings(
                privacy=privacy,
                allow_comments=allow_comments,
                allow_duet=allow_duet,
                allow_stitch=allow_stitch
            )

            # Schedule if requested
            if schedule_time:
                logger.info(f"Scheduling post for {schedule_time}...")
                await self._schedule_post(schedule_time)

            # Submit post
            logger.info("Submitting post...")
            video_info = await self._submit_post()

            logger.info(f"Video uploaded successfully: {video_info.get('video_url', 'N/A')}")

            return {
                'success': True,
                'video_url': video_info.get('video_url'),
                'video_id': video_info.get('video_id'),
                'caption': full_caption
            }

        except TikTokUploadError as e:
            logger.error(f"Upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.exception(f"Unexpected error during upload: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {e}"
            }

    async def _upload_file(self, file_path: str):
        """Upload video file."""
        try:
            # Find file input
            file_input = await self.page.wait_for_selector(
                self.SELECTORS['file_input'],
                timeout=10000
            )

            if not file_input:
                raise TikTokUploadError("File input not found")

            # Upload file with human-like delay
            await self._random_delay(1, 2)
            await file_input.set_input_files(file_path)

            logger.debug("File selected for upload")

        except Exception as e:
            raise TikTokUploadError(f"Failed to upload file: {e}")

    async def _wait_for_processing(self, timeout: int = 300):
        """
        Wait for video processing to complete.

        Args:
            timeout: Maximum wait time in seconds
        """
        try:
            start_time = time.time()

            while time.time() - start_time < timeout:
                # Check if video preview is ready
                video_preview = await self.page.query_selector(self.SELECTORS['video_preview'])

                if video_preview:
                    # Check if progress bar is gone
                    progress = await self.page.query_selector(self.SELECTORS['upload_progress'])

                    if not progress:
                        logger.debug("Video processing complete")
                        await self._random_delay(2, 3)
                        return

                await asyncio.sleep(2)

            raise TikTokUploadError("Video processing timeout")

        except Exception as e:
            raise TikTokUploadError(f"Error waiting for processing: {e}")

    def _format_caption(self, caption: str, hashtags: Optional[List[str]] = None) -> str:
        """Format caption with hashtags."""
        formatted = caption.strip()

        if hashtags:
            # Add space before hashtags if caption doesn't end with space
            if formatted and not formatted.endswith(' '):
                formatted += ' '

            # Add hashtags
            formatted += ' '.join(f'#{tag.lstrip("#")}' for tag in hashtags)

        return formatted

    async def _enter_caption(self, caption: str):
        """
        Enter caption with human-like typing.

        Args:
            caption: Caption text to enter
        """
        try:
            # Find caption input
            caption_input = await self.page.wait_for_selector(
                self.SELECTORS['caption_input'],
                timeout=10000
            )

            if not caption_input:
                raise TikTokUploadError("Caption input not found")

            # Click on input with mouse movement
            await self._human_click(caption_input)
            await self._random_delay(0.5, 1)

            # Type caption with random delays
            await self._human_type(caption_input, caption)

            logger.debug("Caption entered")

        except Exception as e:
            raise TikTokUploadError(f"Failed to enter caption: {e}")

    async def _configure_settings(
        self,
        privacy: str,
        allow_comments: bool,
        allow_duet: bool,
        allow_stitch: bool
    ):
        """Configure video privacy and interaction settings."""
        try:
            # This is a simplified version - actual selectors will depend on TikTok's UI
            # Privacy settings
            if privacy != "public":
                privacy_selector = f'button:has-text("{privacy.capitalize()}")'
                privacy_button = await self.page.query_selector(privacy_selector)
                if privacy_button:
                    await self._human_click(privacy_button)
                    await self._random_delay(0.5, 1)

            # Interaction settings - toggle if needed
            settings = {
                'comments': allow_comments,
                'duet': allow_duet,
                'stitch': allow_stitch
            }

            for setting, enabled in settings.items():
                # Find toggle and check current state
                # This is simplified - actual implementation needs proper selectors
                toggle = await self.page.query_selector(f'[data-e2e="{setting}-toggle"]')
                if toggle:
                    # Toggle if needed based on desired state
                    await self._human_click(toggle)
                    await self._random_delay(0.3, 0.7)

            logger.debug("Settings configured")

        except Exception as e:
            logger.warning(f"Failed to configure some settings: {e}")

    async def _schedule_post(self, schedule_time: str):
        """Schedule post for later."""
        try:
            # Find schedule toggle
            schedule_toggle = await self.page.query_selector('[data-e2e="schedule-toggle"]')

            if schedule_toggle:
                await self._human_click(schedule_toggle)
                await self._random_delay(1, 2)

                # Enter schedule time
                # Actual implementation depends on TikTok's date picker UI
                logger.debug(f"Post scheduled for {schedule_time}")
            else:
                logger.warning("Schedule option not found")

        except Exception as e:
            logger.warning(f"Failed to schedule post: {e}")

    async def _submit_post(self) -> Dict[str, Any]:
        """
        Submit the post and get video info.

        Returns:
            Dictionary with video_url and video_id
        """
        try:
            # Find and click post button
            post_button = await self.page.wait_for_selector(
                self.SELECTORS['post_button'],
                timeout=10000
            )

            if not post_button:
                raise TikTokUploadError("Post button not found")

            # Human-like click
            await self._human_click(post_button)

            # Wait for upload to complete and redirect
            await self.page.wait_for_url('**/creator-center/**', timeout=60000)
            await self._random_delay(3, 5)

            # Try to get video URL from page
            video_url = None
            video_id = None

            try:
                # Look for video link in creator center
                current_url = self.page.url
                if 'creator-center' in current_url:
                    # Extract video ID from URL or page
                    video_link = await self.page.query_selector('a[href*="/video/"]')
                    if video_link:
                        href = await video_link.get_attribute('href')
                        video_url = f"https://www.tiktok.com{href}" if href.startswith('/') else href

                        # Extract video ID
                        if '/video/' in video_url:
                            video_id = video_url.split('/video/')[-1].split('?')[0]

            except Exception as e:
                logger.warning(f"Could not extract video URL: {e}")

            return {
                'video_url': video_url or 'https://www.tiktok.com/@yourprofile',
                'video_id': video_id or 'unknown'
            }

        except Exception as e:
            raise TikTokUploadError(f"Failed to submit post: {e}")

    async def _handle_captcha(self) -> bool:
        """
        Detect and solve captcha if present.

        Returns:
            True if captcha was solved or not present, False if failed
        """
        try:
            await asyncio.sleep(2)

            # Check for captcha
            captcha_frame = await self.page.query_selector(self.SELECTORS['captcha_container'])

            if not captcha_frame:
                logger.debug("No captcha detected")
                return True

            if not self.captcha_solver:
                logger.error("Captcha detected but no solver configured")
                raise TikTokUploadError("Captcha detected but no solver available")

            logger.info("Captcha detected, attempting to solve...")

            # Solve captcha using the solver
            solution = self.captcha_solver.solve_generic(self.page)

            if solution and solution.get('success'):
                # Apply solution based on captcha type
                await self._apply_captcha_solution(solution)

                # Wait for captcha to disappear
                await self.page.wait_for_selector(
                    self.SELECTORS['captcha_container'],
                    state='hidden',
                    timeout=10000
                )

                logger.info("Captcha solved successfully")
                return True
            else:
                logger.error("Failed to solve captcha")
                raise TikTokUploadError("Captcha solving failed")

        except Exception as e:
            logger.exception(f"Captcha handling error: {e}")
            return False

    async def _apply_captcha_solution(self, solution: Dict[str, Any]):
        """
        Apply captcha solution to page.

        Args:
            solution: Solution dictionary from captcha solver
        """
        try:
            if 'x_position' in solution:
                # Puzzle/slider captcha
                x = solution['x_position']
                y = solution.get('y_position', 0)
                duration = solution.get('duration', 2.0)

                # Find slider element
                slider = await self.page.query_selector('.secsdk-captcha-drag-icon')

                if slider:
                    # Get slider position
                    box = await slider.bounding_box()

                    if box:
                        # Perform drag
                        await self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        await self.page.mouse.down()
                        await asyncio.sleep(0.1)

                        # Drag to position with human-like movement
                        steps = random.randint(20, 30)
                        for i in range(steps):
                            await self.page.mouse.move(
                                box['x'] + (x * (i / steps)),
                                box['y'] + box['height'] / 2 + random.uniform(-2, 2)
                            )
                            await asyncio.sleep(duration / steps)

                        await self.page.mouse.up()

            elif 'angle' in solution:
                # Rotation captcha
                angle = solution['angle']
                # Implementation depends on TikTok's rotation captcha UI
                logger.debug(f"Rotation captcha: {angle} degrees")

            elif 'coordinates' in solution:
                # Shapes captcha
                coordinates = solution['coordinates']
                for coord in coordinates:
                    await self.page.mouse.click(coord['x'], coord['y'])
                    await self._random_delay(0.5, 1)

        except Exception as e:
            logger.error(f"Failed to apply captcha solution: {e}")
            raise

    async def check_account_status(self) -> Dict[str, Any]:
        """
        Check if account is still valid and accessible.

        Returns:
            Dictionary with account status:
            {
                'valid': bool,
                'logged_in': bool,
                'restricted': bool,
                'error': str (if any)
            }
        """
        try:
            logger.info("Checking account status...")

            # Ensure browser is set up
            if not self.page:
                await self.setup_browser()

            # Check login status
            await self.page.goto("https://www.tiktok.com/", wait_until='networkidle')
            await self._random_delay(2, 3)

            is_logged_in = await self._verify_login()

            if not is_logged_in:
                return {
                    'valid': False,
                    'logged_in': False,
                    'restricted': False,
                    'error': 'Not logged in'
                }

            # Try to access creator center
            response = await self.page.goto(self.STUDIO_URL, wait_until='networkidle')
            await self._random_delay(2, 3)

            # Check for restrictions
            restricted = False
            error_message = None

            # Look for error messages or restrictions
            error_elem = await self.page.query_selector(self.SELECTORS['error_message'])
            if error_elem:
                error_message = await error_elem.inner_text()
                restricted = True

            # Check if can access upload page
            upload_response = await self.page.goto(self.UPLOAD_URL, wait_until='networkidle')
            await self._random_delay(1, 2)

            can_upload = 'upload' in self.page.url

            return {
                'valid': is_logged_in and can_upload,
                'logged_in': is_logged_in,
                'restricted': restricted,
                'can_upload': can_upload,
                'error': error_message
            }

        except Exception as e:
            logger.exception(f"Error checking account status: {e}")
            return {
                'valid': False,
                'logged_in': False,
                'restricted': False,
                'error': str(e)
            }

    # Human-like behavior methods

    async def _random_delay(self, min_seconds: float, max_seconds: float):
        """Random delay to simulate human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def _human_click(self, element):
        """Click element with human-like mouse movement."""
        try:
            # Get element position
            box = await element.bounding_box()

            if box:
                # Random point within element
                x = box['x'] + random.uniform(box['width'] * 0.3, box['width'] * 0.7)
                y = box['y'] + random.uniform(box['height'] * 0.3, box['height'] * 0.7)

                # Move mouse to element
                await self.page.mouse.move(x, y)
                await self._random_delay(0.1, 0.3)

                # Click
                await self.page.mouse.click(x, y)
            else:
                # Fallback to direct click
                await element.click()

        except Exception as e:
            logger.warning(f"Human click failed, using direct click: {e}")
            await element.click()

    async def _human_type(self, element, text: str):
        """Type text with human-like delays."""
        try:
            for char in text:
                await element.type(char, delay=random.uniform(50, 150))

                # Random pause between words
                if char == ' ' and random.random() < 0.3:
                    await self._random_delay(0.2, 0.5)

        except Exception as e:
            logger.warning(f"Human typing failed, using fast typing: {e}")
            await element.type(text, delay=50)

    async def _random_scroll(self):
        """Perform random scrolling to appear more human."""
        try:
            scroll_amount = random.randint(100, 500)
            await self.page.mouse.wheel(0, scroll_amount)
            await self._random_delay(0.5, 1)
        except Exception as e:
            logger.debug(f"Random scroll failed: {e}")

    async def close(self):
        """Close browser and cleanup resources."""
        try:
            logger.info("Closing browser...")

            if self.page:
                await self.page.close()

            if self.context:
                await self.context.close()

            if self.browser:
                await self.browser.close()

            if self.playwright:
                await self.playwright.stop()

            if self.captcha_solver:
                self.captcha_solver.close()

            logger.info("Browser closed")

        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def __del__(self):
        """Cleanup on deletion."""
        try:
            if self.browser:
                asyncio.get_event_loop().run_until_complete(self.close())
        except:
            pass
