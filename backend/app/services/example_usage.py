"""
Example usage of TikTok Uploader Service

This script demonstrates how to use the TikTokUploader class
for automated video uploads to TikTok.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services import TikTokUploader, SadCaptchaSolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_upload():
    """Basic example: Upload a single video with caption and hashtags."""

    logger.info("Starting basic upload example...")

    uploader = TikTokUploader(
        cookies='cookies.json',  # Path to your cookies file
        headless=False,  # Set to True for production
        captcha_api_key='your-sadcaptcha-api-key'
    )

    try:
        # Setup browser
        await uploader.setup_browser()

        # Upload video
        result = await uploader.upload_video(
            video_path='path/to/your/video.mp4',
            caption='This is my amazing video! Check it out!',
            hashtags=['fyp', 'viral', 'trending', 'funny'],
            privacy='public',
            allow_comments=True,
            allow_duet=True,
            allow_stitch=True
        )

        # Check result
        if result['success']:
            logger.info(f"✓ Video uploaded successfully!")
            logger.info(f"  URL: {result['video_url']}")
            logger.info(f"  Video ID: {result['video_id']}")
        else:
            logger.error(f"✗ Upload failed: {result['error']}")

    except Exception as e:
        logger.exception(f"Error during upload: {e}")

    finally:
        await uploader.close()


async def example_with_proxy():
    """Example: Upload video using a proxy for anonymity."""

    logger.info("Starting proxy upload example...")

    proxy_config = {
        'server': 'http://proxy.example.com:8080',
        'username': 'proxy_user',
        'password': 'proxy_pass'
    }

    uploader = TikTokUploader(
        proxy=proxy_config,
        cookies='cookies.json',
        headless=True,
        captcha_api_key='your-sadcaptcha-api-key'
    )

    try:
        await uploader.setup_browser()

        result = await uploader.upload_video(
            video_path='path/to/video.mp4',
            caption='Posted using a proxy!',
            hashtags=['secure', 'anonymous']
        )

        if result['success']:
            logger.info(f"✓ Video uploaded via proxy: {result['video_url']}")
        else:
            logger.error(f"✗ Upload failed: {result['error']}")

    finally:
        await uploader.close()


async def example_custom_profile():
    """Example: Upload with custom browser profile (user agent, timezone, etc.)."""

    logger.info("Starting custom profile upload example...")

    # Custom profile for a specific location/device
    custom_profile = {
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'viewport': {'width': 375, 'height': 812},  # iPhone dimensions
        'timezone': 'America/Los_Angeles',
        'locale': 'en-US',
        'geolocation': {'latitude': 34.0522, 'longitude': -118.2437},  # Los Angeles
        'permissions': ['geolocation']
    }

    uploader = TikTokUploader(
        profile=custom_profile,
        cookies='cookies.json',
        headless=True,
        captcha_api_key='your-sadcaptcha-api-key'
    )

    try:
        await uploader.setup_browser()

        result = await uploader.upload_video(
            video_path='path/to/video.mp4',
            caption='Posted from my iPhone! 📱',
            hashtags=['mobile', 'ios']
        )

        if result['success']:
            logger.info(f"✓ Video uploaded with custom profile: {result['video_url']}")
        else:
            logger.error(f"✗ Upload failed: {result['error']}")

    finally:
        await uploader.close()


async def example_batch_upload():
    """Example: Upload multiple videos in a batch."""

    logger.info("Starting batch upload example...")

    videos = [
        {
            'path': 'videos/video1.mp4',
            'caption': 'First video of the day!',
            'hashtags': ['morning', 'motivation']
        },
        {
            'path': 'videos/video2.mp4',
            'caption': 'Second video coming in hot!',
            'hashtags': ['trending', 'viral']
        },
        {
            'path': 'videos/video3.mp4',
            'caption': 'Last one for today!',
            'hashtags': ['night', 'chill']
        }
    ]

    uploader = TikTokUploader(
        cookies='cookies.json',
        headless=True,
        captcha_api_key='your-sadcaptcha-api-key'
    )

    try:
        await uploader.setup_browser()

        results = []
        for i, video in enumerate(videos, 1):
            logger.info(f"Uploading video {i}/{len(videos)}...")

            result = await uploader.upload_video(
                video_path=video['path'],
                caption=video['caption'],
                hashtags=video['hashtags']
            )

            results.append(result)

            if result['success']:
                logger.info(f"  ✓ Video {i} uploaded: {result['video_url']}")
            else:
                logger.error(f"  ✗ Video {i} failed: {result['error']}")

            # Wait between uploads to avoid rate limiting
            if i < len(videos):
                wait_time = 300  # 5 minutes
                logger.info(f"  Waiting {wait_time}s before next upload...")
                await asyncio.sleep(wait_time)

        # Summary
        successful = sum(1 for r in results if r['success'])
        logger.info(f"\nBatch upload complete: {successful}/{len(videos)} successful")

    finally:
        await uploader.close()


async def example_account_check():
    """Example: Check account status before uploading."""

    logger.info("Checking account status...")

    uploader = TikTokUploader(
        cookies='cookies.json',
        headless=True
    )

    try:
        await uploader.setup_browser()

        # Check account status
        status = await uploader.check_account_status()

        logger.info(f"Account Status:")
        logger.info(f"  Valid: {status['valid']}")
        logger.info(f"  Logged In: {status['logged_in']}")
        logger.info(f"  Can Upload: {status.get('can_upload', False)}")
        logger.info(f"  Restricted: {status['restricted']}")

        if status['error']:
            logger.warning(f"  Error: {status['error']}")

        # Only proceed if account is valid
        if status['valid'] and status.get('can_upload'):
            logger.info("\n✓ Account is ready for uploads!")

            result = await uploader.upload_video(
                video_path='path/to/video.mp4',
                caption='Account verified and ready!',
                hashtags=['verified', 'ready']
            )

            if result['success']:
                logger.info(f"✓ Video uploaded: {result['video_url']}")
        else:
            logger.warning("\n✗ Account not ready for uploads")

    finally:
        await uploader.close()


async def example_captcha_solving():
    """Example: Test captcha solving separately."""

    logger.info("Testing captcha solver...")

    solver = SadCaptchaSolver(api_key='your-sadcaptcha-api-key')

    try:
        # Test with a sample captcha image
        with open('captcha_sample.png', 'rb') as f:
            image_data = f.read()

        # Solve puzzle captcha
        solution = solver.solve_puzzle(image_data)

        if solution and solution['success']:
            logger.info(f"✓ Captcha solved successfully!")
            logger.info(f"  X Position: {solution['x_position']}")
            logger.info(f"  Y Position: {solution['y_position']}")
            logger.info(f"  Duration: {solution['duration']}s")

            # Report success (in real usage, after verifying it worked)
            solver.report_solution(solution['solution_id'], success=True)
        else:
            logger.error(f"✗ Captcha solving failed: {solution.get('error')}")

    except FileNotFoundError:
        logger.warning("No sample captcha image found. Skipping test.")
    except Exception as e:
        logger.exception(f"Error testing captcha solver: {e}")
    finally:
        solver.close()


async def example_scheduled_upload():
    """Example: Schedule a video for later posting."""

    logger.info("Starting scheduled upload example...")

    uploader = TikTokUploader(
        cookies='cookies.json',
        headless=True,
        captcha_api_key='your-sadcaptcha-api-key'
    )

    try:
        await uploader.setup_browser()

        # Schedule for 2 hours from now
        from datetime import datetime, timedelta
        schedule_time = (datetime.now() + timedelta(hours=2)).isoformat()

        result = await uploader.upload_video(
            video_path='path/to/video.mp4',
            caption='This video is scheduled for later!',
            hashtags=['scheduled', 'automated'],
            schedule_time=schedule_time
        )

        if result['success']:
            logger.info(f"✓ Video scheduled for {schedule_time}")
            logger.info(f"  Video URL: {result['video_url']}")
        else:
            logger.error(f"✗ Scheduling failed: {result['error']}")

    finally:
        await uploader.close()


def main():
    """Run examples."""

    print("\n" + "="*60)
    print("TikTok Uploader - Example Usage")
    print("="*60 + "\n")

    print("Available examples:")
    print("1. Basic Upload")
    print("2. Upload with Proxy")
    print("3. Upload with Custom Profile")
    print("4. Batch Upload")
    print("5. Account Status Check")
    print("6. Captcha Solving Test")
    print("7. Scheduled Upload")
    print("8. Run All Examples")

    choice = input("\nSelect an example to run (1-8): ").strip()

    examples = {
        '1': example_basic_upload,
        '2': example_with_proxy,
        '3': example_custom_profile,
        '4': example_batch_upload,
        '5': example_account_check,
        '6': example_captcha_solving,
        '7': example_scheduled_upload,
    }

    if choice in examples:
        asyncio.run(examples[choice]())
    elif choice == '8':
        print("\nRunning all examples...\n")
        for name, example in examples.items():
            print(f"\n{'='*60}")
            print(f"Running Example {name}")
            print('='*60)
            try:
                asyncio.run(example())
            except Exception as e:
                logger.error(f"Example {name} failed: {e}")
            print("\n")
    else:
        print("Invalid choice. Please run again and select 1-8.")


if __name__ == '__main__':
    main()
