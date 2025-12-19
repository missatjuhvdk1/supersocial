"""Services package for TikTok auto-poster."""

from .captcha_solver import SadCaptchaSolver, CaptchaType
from .tiktok_uploader import TikTokUploader, TikTokUploadError
from .cookie_manager import CookieManager

try:
    from .video_processor import VideoProcessor, VideoProcessorError
    __all__ = [
        'SadCaptchaSolver',
        'CaptchaType',
        'TikTokUploader',
        'TikTokUploadError',
        'CookieManager',
        'VideoProcessor',
        'VideoProcessorError'
    ]
except ImportError:
    # video_processor may not exist yet
    __all__ = [
        'SadCaptchaSolver',
        'CaptchaType',
        'TikTokUploader',
        'TikTokUploadError',
        'CookieManager'
    ]
