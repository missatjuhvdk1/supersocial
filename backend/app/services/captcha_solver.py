"""
TikTok Captcha Solver Service

Handles various TikTok captcha types using SadCaptcha API:
- Slider/Puzzle captchas
- Rotation captchas
- 3D shape captchas
"""

import logging
import time
import base64
import requests
from typing import Dict, Optional, Any
from io import BytesIO

logger = logging.getLogger(__name__)


class CaptchaType:
    """TikTok captcha types."""
    PUZZLE = "puzzle"
    ROTATE = "rotate"
    SHAPES = "shapes"
    SLIDER = "slider"


class SadCaptchaSolver:
    """
    Captcha solver using SadCaptcha API for TikTok captchas.

    Supports multiple captcha types that TikTok uses to prevent automation.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the captcha solver.

        Args:
            api_key: SadCaptcha API key. If not provided, will use environment variable.
        """
        self.api_key = api_key or self._get_api_key()
        self.base_url = "https://api.sadcaptcha.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })

    def _get_api_key(self) -> str:
        """Get API key from environment or config."""
        import os
        api_key = os.getenv('SADCAPTCHA_API_KEY')
        if not api_key:
            logger.warning("SADCAPTCHA_API_KEY not set in environment")
        return api_key or ""

    def solve_puzzle(self, image_data: bytes, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Solve slider/puzzle captcha.

        Args:
            image_data: Raw image bytes of the captcha
            **kwargs: Additional parameters (e.g., puzzle_url, site_key)

        Returns:
            Dictionary with solution data:
            {
                'success': bool,
                'x_position': int,  # X coordinate to slide to
                'y_position': int,  # Y coordinate
                'duration': float   # Suggested slide duration
            }
        """
        try:
            logger.info("Solving puzzle captcha")

            # Convert image to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')

            payload = {
                'type': CaptchaType.PUZZLE,
                'image': image_b64,
                'provider': 'tiktok',
                **kwargs
            }

            response = self.session.post(
                f"{self.base_url}/solve",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    logger.info(f"Puzzle captcha solved: x={result.get('x_position')}")
                    return {
                        'success': True,
                        'x_position': result.get('x_position', 0),
                        'y_position': result.get('y_position', 0),
                        'duration': result.get('duration', 2.0),
                        'solution_id': result.get('solution_id')
                    }
                else:
                    logger.error(f"Puzzle captcha solve failed: {result.get('error')}")
                    return {'success': False, 'error': result.get('error')}
            else:
                logger.error(f"Captcha API error: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'API error: {response.status_code}'}

        except Exception as e:
            logger.exception(f"Error solving puzzle captcha: {e}")
            return {'success': False, 'error': str(e)}

    def solve_rotate(self, image_data: bytes, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Solve rotation captcha.

        Args:
            image_data: Raw image bytes of the captcha
            **kwargs: Additional parameters

        Returns:
            Dictionary with solution data:
            {
                'success': bool,
                'angle': int,      # Rotation angle in degrees
                'duration': float  # Suggested rotation duration
            }
        """
        try:
            logger.info("Solving rotation captcha")

            image_b64 = base64.b64encode(image_data).decode('utf-8')

            payload = {
                'type': CaptchaType.ROTATE,
                'image': image_b64,
                'provider': 'tiktok',
                **kwargs
            }

            response = self.session.post(
                f"{self.base_url}/solve",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    logger.info(f"Rotation captcha solved: angle={result.get('angle')}")
                    return {
                        'success': True,
                        'angle': result.get('angle', 0),
                        'duration': result.get('duration', 1.5),
                        'solution_id': result.get('solution_id')
                    }
                else:
                    logger.error(f"Rotation captcha solve failed: {result.get('error')}")
                    return {'success': False, 'error': result.get('error')}
            else:
                logger.error(f"Captcha API error: {response.status_code}")
                return {'success': False, 'error': f'API error: {response.status_code}'}

        except Exception as e:
            logger.exception(f"Error solving rotation captcha: {e}")
            return {'success': False, 'error': str(e)}

    def solve_shapes(self, image_data: bytes, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Solve 3D shapes captcha.

        Args:
            image_data: Raw image bytes of the captcha
            **kwargs: Additional parameters

        Returns:
            Dictionary with solution data:
            {
                'success': bool,
                'shapes': List[str],  # Identified shapes
                'coordinates': List[Dict]  # Click coordinates for each shape
            }
        """
        try:
            logger.info("Solving 3D shapes captcha")

            image_b64 = base64.b64encode(image_data).decode('utf-8')

            payload = {
                'type': CaptchaType.SHAPES,
                'image': image_b64,
                'provider': 'tiktok',
                **kwargs
            }

            response = self.session.post(
                f"{self.base_url}/solve",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    logger.info(f"Shapes captcha solved: {len(result.get('shapes', []))} shapes")
                    return {
                        'success': True,
                        'shapes': result.get('shapes', []),
                        'coordinates': result.get('coordinates', []),
                        'solution_id': result.get('solution_id')
                    }
                else:
                    logger.error(f"Shapes captcha solve failed: {result.get('error')}")
                    return {'success': False, 'error': result.get('error')}
            else:
                logger.error(f"Captcha API error: {response.status_code}")
                return {'success': False, 'error': f'API error: {response.status_code}'}

        except Exception as e:
            logger.exception(f"Error solving shapes captcha: {e}")
            return {'success': False, 'error': str(e)}

    def solve_generic(self, page, captcha_type: str = CaptchaType.PUZZLE) -> Optional[Dict[str, Any]]:
        """
        Generic solve method that detects and solves captcha from a Playwright page.

        Args:
            page: Playwright page object
            captcha_type: Type of captcha expected

        Returns:
            Solution dictionary or None if no captcha detected
        """
        try:
            # Wait a bit for captcha to load
            time.sleep(2)

            # Try to find captcha container
            captcha_selectors = [
                'iframe[id*="captcha"]',
                'div[class*="captcha"]',
                'div[id*="captcha"]',
                '#captcha-verify-image',
                '.captcha_verify_img',
            ]

            captcha_element = None
            for selector in captcha_selectors:
                try:
                    captcha_element = page.wait_for_selector(selector, timeout=3000)
                    if captcha_element:
                        logger.info(f"Found captcha with selector: {selector}")
                        break
                except:
                    continue

            if not captcha_element:
                logger.debug("No captcha detected on page")
                return None

            # Take screenshot of captcha area
            screenshot_bytes = captcha_element.screenshot()

            # Solve based on type
            if captcha_type == CaptchaType.PUZZLE or captcha_type == CaptchaType.SLIDER:
                return self.solve_puzzle(screenshot_bytes)
            elif captcha_type == CaptchaType.ROTATE:
                return self.solve_rotate(screenshot_bytes)
            elif captcha_type == CaptchaType.SHAPES:
                return self.solve_shapes(screenshot_bytes)
            else:
                logger.warning(f"Unknown captcha type: {captcha_type}")
                return None

        except Exception as e:
            logger.exception(f"Error in generic captcha solve: {e}")
            return None

    def report_solution(self, solution_id: str, success: bool):
        """
        Report if a solution worked or failed.

        Args:
            solution_id: ID returned from solve methods
            success: Whether the solution worked
        """
        try:
            payload = {
                'solution_id': solution_id,
                'success': success
            }

            self.session.post(
                f"{self.base_url}/report",
                json=payload,
                timeout=10
            )

            logger.info(f"Reported solution {solution_id} as {'success' if success else 'failure'}")

        except Exception as e:
            logger.warning(f"Failed to report solution: {e}")

    def close(self):
        """Close the session."""
        self.session.close()
