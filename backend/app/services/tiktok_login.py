"""
TikTok Login Service

Automated TikTok login with email/password and cookie extraction:
- Playwright browser automation with stealth plugin
- Proxy support
- Human-like typing patterns and behaviors
- Captcha solving integration
- Session cookie extraction
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth_async

from .captcha_solver import SadCaptchaSolver

logger = logging.getLogger(__name__)


class TikTokLoginError(Exception):
    """Exception raised for TikTok login errors."""
    pass


class TikTokLoginService:
    """
    TikTok login service with stealth capabilities.

    Handles email/password authentication and cookie extraction.
    """

    # TikTok URLs
    LOGIN_URL = "https://www.tiktok.com/login/phone-or-email/email"
    HOME_URL = "https://www.tiktok.com/"

    # Selectors for login flow
    SELECTORS = {
        'email_input': 'input[name="username"]',
        'password_input': 'input[type="password"]',
        'login_button': 'button[type="submit"]',
        'captcha_container': 'iframe[id*="captcha"]',
        'profile_icon': '[data-e2e="profile-icon"]',
        'error_message': '[class*="error"]',
        'login_check': '[data-e2e="profile-icon"], a[href*="@"]',
    }

    def __init__(
        self,
        proxy: Optional[Dict[str, str]] = None,
        headless: bool = True,
        captcha_api_key: Optional[str] = None
    ):
        """
        Initialize TikTok login service.

        Args:
            proxy: Proxy configuration {'server': 'http://...', 'username': '...', 'password': '...'}
            headless: Run browser in headless mode
            captcha_api_key: API key for captcha solver
        """
        self.proxy = proxy
        self.headless = headless
        self.profile = self._default_profile()

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.captcha_solver = SadCaptchaSolver(api_key=captcha_api_key) if captcha_api_key else None

        logger.info("TikTokLoginService initialized")

    def _default_profile(self) -> Dict[str, Any]:
        """Generate default browser profile."""
        return {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'viewport': {'width': 1920, 'height': 1080},
            'timezone': 'America/New_York',
            'locale': 'en-US',
            'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},
            'permissions': ['geolocation'],
        }

    async def _setup_browser(self):
        """
        Launch and configure Playwright browser with stealth.

        Sets up:
        - Chromium browser with stealth plugin
        - Proxy if configured
        - Custom user agent and viewport
        - Timezone and locale spoofing
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

            logger.info("Browser setup complete")

        except Exception as e:
            logger.exception(f"Failed to setup browser: {e}")
            await self.close()
            raise TikTokLoginError(f"Browser setup failed: {e}")

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

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login to TikTok with email and password, then extract cookies.

        Args:
            email: TikTok account email
            password: TikTok account password

        Returns:
            Dictionary with login result:
            {
                'success': bool,
                'cookies': List[Dict],  # Browser cookies if successful
                'error': str  # Error message if failed
            }
        """
        try:
            logger.info(f"Starting login process for email: {email}")

            # Setup browser if not already done
            if not self.page:
                await self._setup_browser()

            # Navigate to login page
            logger.info("Navigating to TikTok login page...")
            await self.page.goto(self.LOGIN_URL, wait_until='networkidle')
            await self._random_delay(2, 3)

            # Enter email
            logger.info("Entering email...")
            await self._enter_email(email)
            await self._random_delay(1, 2)

            # Enter password
            logger.info("Entering password...")
            await self._enter_password(password)
            await self._random_delay(1, 2)

            # Click login button
            logger.info("Clicking login button...")
            await self._click_login_button()
            await self._random_delay(2, 3)

            # Handle captcha if present
            captcha_handled = await self._handle_captcha()
            if not captcha_handled:
                logger.warning("Captcha handling failed or timed out")
                # Continue anyway, might still work

            # Save screenshot after login attempt for debugging
            try:
                screenshot_path = f"/app/logs/login_attempt_{email.replace('@', '_at_')}.png"
                await self.page.screenshot(path=screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not save screenshot: {e}")

            # Wait for navigation/login to complete
            await self._wait_for_login_complete()

            # Save screenshot after waiting
            try:
                screenshot_path2 = f"/app/logs/login_result_{email.replace('@', '_at_')}.png"
                await self.page.screenshot(path=screenshot_path2)
                logger.info(f"Screenshot saved to {screenshot_path2}")
            except Exception as e:
                logger.warning(f"Could not save screenshot: {e}")

            # Log current URL for debugging
            logger.info(f"Current URL after login attempt: {self.page.url}")

            # Verify login success
            logger.info("Verifying login success...")
            is_logged_in = await self._verify_login()

            if not is_logged_in:
                # Check for error messages
                error_msg = await self._get_error_message()
                # Also get page content for debugging
                try:
                    page_title = await self.page.title()
                    logger.error(f"Login failed. Page title: {page_title}, URL: {self.page.url}")
                except:
                    pass
                raise TikTokLoginError(f"Login failed: {error_msg or 'Could not verify login'}")

            # Extract cookies
            logger.info("Extracting cookies...")
            cookies = await self._extract_cookies()

            logger.info(f"Login successful! Extracted {len(cookies)} cookies")

            return {
                'success': True,
                'cookies': cookies,
                'error': None
            }

        except TikTokLoginError as e:
            logger.error(f"Login failed: {e}")
            return {
                'success': False,
                'cookies': [],
                'error': str(e)
            }
        except Exception as e:
            logger.exception(f"Unexpected error during login: {e}")
            return {
                'success': False,
                'cookies': [],
                'error': f"Unexpected error: {e}"
            }

    async def _enter_email(self, email: str):
        """Enter email with human-like typing."""
        try:
            # Find email input
            email_input = await self.page.wait_for_selector(
                self.SELECTORS['email_input'],
                timeout=10000
            )

            if not email_input:
                raise TikTokLoginError("Email input field not found")

            # Click on input
            await self._human_click(email_input)
            await self._random_delay(0.3, 0.7)

            # Type email with human-like delays
            await self._human_type(email_input, email)

            logger.debug("Email entered")

        except Exception as e:
            raise TikTokLoginError(f"Failed to enter email: {e}")

    async def _enter_password(self, password: str):
        """Enter password with human-like typing."""
        try:
            # Find password input
            password_input = await self.page.wait_for_selector(
                self.SELECTORS['password_input'],
                timeout=10000
            )

            if not password_input:
                raise TikTokLoginError("Password input field not found")

            # Click on input
            await self._human_click(password_input)
            await self._random_delay(0.3, 0.7)

            # Type password with human-like delays
            await self._human_type(password_input, password)

            logger.debug("Password entered")

        except Exception as e:
            raise TikTokLoginError(f"Failed to enter password: {e}")

    async def _click_login_button(self):
        """Click the login button."""
        try:
            # Find login button
            login_button = await self.page.wait_for_selector(
                self.SELECTORS['login_button'],
                timeout=10000
            )

            if not login_button:
                raise TikTokLoginError("Login button not found")

            # Human-like click
            await self._human_click(login_button)

            logger.debug("Login button clicked")

        except Exception as e:
            raise TikTokLoginError(f"Failed to click login button: {e}")

    async def _wait_for_login_complete(self, timeout: int = 30):
        """
        Wait for login process to complete.

        Args:
            timeout: Maximum wait time in seconds
        """
        try:
            # Wait for either:
            # 1. Redirect to home page
            # 2. Profile icon appears
            # 3. URL changes from login page

            start_time = asyncio.get_event_loop().time()

            while (asyncio.get_event_loop().time() - start_time) < timeout:
                current_url = self.page.url

                # Check if redirected away from login
                if 'login' not in current_url:
                    logger.debug("Redirected from login page")
                    await self._random_delay(1, 2)
                    return

                # Check if profile icon appeared
                profile_icon = await self.page.query_selector(self.SELECTORS['profile_icon'])
                if profile_icon:
                    logger.debug("Profile icon appeared")
                    await self._random_delay(1, 2)
                    return

                await asyncio.sleep(1)

            # Timeout reached, but continue anyway
            logger.warning("Login completion wait timed out")

        except Exception as e:
            logger.warning(f"Error waiting for login complete: {e}")

    async def _handle_captcha(self, max_attempts: int = 3) -> bool:
        """
        Detect and solve captcha if present.

        Args:
            max_attempts: Maximum number of captcha solve attempts

        Returns:
            True if captcha was solved or not present, False if failed
        """
        try:
            await asyncio.sleep(2)

            for attempt in range(max_attempts):
                # Check for captcha
                captcha_frame = await self.page.query_selector(self.SELECTORS['captcha_container'])

                if not captcha_frame:
                    logger.debug("No captcha detected")
                    return True

                if not self.captcha_solver:
                    logger.error("Captcha detected but no solver configured")
                    raise TikTokLoginError("Captcha detected but no solver available")

                logger.info(f"Captcha detected, attempting to solve (attempt {attempt + 1}/{max_attempts})...")

                # Solve captcha using the solver
                solution = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.captcha_solver.solve_generic,
                    self.page
                )

                if solution and solution.get('success'):
                    # Apply solution based on captcha type
                    await self._apply_captcha_solution(solution)

                    # Wait for captcha to disappear
                    try:
                        await self.page.wait_for_selector(
                            self.SELECTORS['captcha_container'],
                            state='hidden',
                            timeout=10000
                        )
                        logger.info("Captcha solved successfully")
                        return True
                    except:
                        logger.warning("Captcha still present after solve attempt")
                        await self._random_delay(2, 3)
                        continue
                else:
                    logger.warning(f"Captcha solve attempt {attempt + 1} failed")
                    await self._random_delay(2, 3)

            logger.error("Failed to solve captcha after all attempts")
            return False

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
                logger.debug(f"Rotation captcha: {angle} degrees")
                # Implementation depends on TikTok's rotation captcha UI

            elif 'coordinates' in solution:
                # Shapes captcha
                coordinates = solution['coordinates']
                for coord in coordinates:
                    await self.page.mouse.click(coord['x'], coord['y'])
                    await self._random_delay(0.5, 1)

        except Exception as e:
            logger.error(f"Failed to apply captcha solution: {e}")
            raise

    async def _verify_login(self) -> bool:
        """
        Verify if user is logged in.

        Returns:
            True if logged in, False otherwise
        """
        try:
            # Navigate to home page
            await self.page.goto(self.HOME_URL, wait_until='networkidle')
            await self._random_delay(2, 3)

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

            logger.debug("Login status unclear, assuming not logged in")
            return False

        except Exception as e:
            logger.warning(f"Error verifying login: {e}")
            return False

    async def _get_error_message(self) -> Optional[str]:
        """Get error message from login page if present."""
        try:
            error_elem = await self.page.query_selector(self.SELECTORS['error_message'])
            if error_elem:
                return await error_elem.inner_text()
            return None
        except Exception as e:
            logger.debug(f"Could not get error message: {e}")
            return None

    async def _extract_cookies(self) -> List[Dict]:
        """
        Extract all cookies from the browser context.

        Returns:
            List of cookie dictionaries
        """
        try:
            cookies = await self.context.cookies()

            # Filter to only TikTok-related cookies
            tiktok_cookies = [
                cookie for cookie in cookies
                if 'tiktok.com' in cookie.get('domain', '')
            ]

            logger.debug(f"Extracted {len(tiktok_cookies)} TikTok cookies")

            return tiktok_cookies

        except Exception as e:
            logger.exception(f"Failed to extract cookies: {e}")
            return []

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

    def login_sync(self, email: str, password: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for login method.
        Use this when calling from a sync context (e.g., Celery tasks).

        Args:
            email: TikTok account email
            password: TikTok account password

        Returns:
            Dictionary with login result
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.login(email, password))
        finally:
            loop.run_until_complete(self.close())
            loop.close()

    def __del__(self):
        """Cleanup on deletion."""
        try:
            if self.browser:
                asyncio.get_event_loop().run_until_complete(self.close())
        except:
            pass
