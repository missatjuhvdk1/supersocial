#!/usr/bin/env python3
"""
TikTok Uploader CLI Tool

Command-line interface for managing TikTok uploads, cookies, and accounts.

Usage:
    python cli.py upload --video video.mp4 --caption "My video" --account my_account
    python cli.py cookies --list
    python cli.py cookies --validate my_account
    python cli.py account --check my_account
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from cookie_manager import CookieManager
from tiktok_uploader import TikTokUploader
from captcha_solver import SadCaptchaSolver

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TikTokCLI:
    """CLI interface for TikTok uploader."""

    def __init__(self):
        self.cookie_manager = CookieManager(storage_path='./cookies')

    async def upload_video(
        self,
        video_path: str,
        account: str,
        caption: str,
        hashtags: Optional[str] = None,
        privacy: str = 'public',
        headless: bool = True,
        proxy: Optional[str] = None
    ):
        """
        Upload a video to TikTok.

        Args:
            video_path: Path to video file
            account: Account ID
            caption: Video caption
            hashtags: Comma-separated hashtags
            privacy: Video privacy setting
            headless: Run in headless mode
            proxy: Proxy URL
        """
        print(f"\n{'='*60}")
        print("TikTok Video Upload")
        print('='*60)

        # Load cookies
        cookies_file = f'cookies/{account}_cookies.json'
        if not Path(cookies_file).exists():
            print(f"✗ Cookies not found for account: {account}")
            print(f"  Expected: {cookies_file}")
            return False

        # Parse hashtags
        tag_list = [tag.strip() for tag in hashtags.split(',')] if hashtags else []

        # Parse proxy
        proxy_config = None
        if proxy:
            proxy_config = {'server': proxy}

        # Create uploader
        uploader = TikTokUploader(
            cookies=cookies_file,
            headless=headless,
            proxy=proxy_config
        )

        try:
            print(f"\n📹 Video: {video_path}")
            print(f"👤 Account: {account}")
            print(f"📝 Caption: {caption}")
            print(f"🏷️  Hashtags: {', '.join(tag_list) if tag_list else 'None'}")
            print(f"🔒 Privacy: {privacy}")
            print()

            print("Setting up browser...")
            await uploader.setup_browser()

            print("Uploading video...")
            result = await uploader.upload_video(
                video_path=video_path,
                caption=caption,
                hashtags=tag_list,
                privacy=privacy
            )

            if result['success']:
                print(f"\n✓ Upload successful!")
                print(f"  URL: {result['video_url']}")
                print(f"  Video ID: {result['video_id']}")
                return True
            else:
                print(f"\n✗ Upload failed: {result['error']}")
                return False

        except Exception as e:
            print(f"\n✗ Error: {e}")
            logger.exception(e)
            return False

        finally:
            await uploader.close()

    async def check_account(self, account: str):
        """
        Check account status and cookie validity.

        Args:
            account: Account ID
        """
        print(f"\n{'='*60}")
        print(f"Account Status: {account}")
        print('='*60)

        cookies_file = f'cookies/{account}_cookies.json'
        if not Path(cookies_file).exists():
            print(f"\n✗ Cookies not found for account: {account}")
            return False

        # Cookie info
        info = self.cookie_manager.get_account_info(account)

        if info:
            print(f"\n📁 Cookie Information:")
            print(f"  Saved: {info['saved_at']}")
            print(f"  Age: {info['age_days']} days")
            print(f"  Count: {info['cookie_count']} cookies")
            print(f"  Valid: {'✓' if info['valid'] else '✗'}")

            if info['missing_cookies']:
                print(f"  Missing: {', '.join(info['missing_cookies'])}")

            if info['expired_cookies']:
                print(f"  Expired: {', '.join(info['expired_cookies'])}")

            if info['expires_soon']:
                print(f"  Expiring soon:")
                for cookie in info['expires_soon']:
                    print(f"    - {cookie['name']}: {cookie['expires_in_days']:.1f} days")

        # Check TikTok account status
        print(f"\n🔍 Checking TikTok account...")

        uploader = TikTokUploader(cookies=cookies_file, headless=True)

        try:
            await uploader.setup_browser()
            status = await uploader.check_account_status()

            print(f"\n📊 Account Status:")
            print(f"  Valid: {'✓' if status['valid'] else '✗'}")
            print(f"  Logged In: {'✓' if status['logged_in'] else '✗'}")
            print(f"  Can Upload: {'✓' if status.get('can_upload', False) else '✗'}")
            print(f"  Restricted: {'⚠️ Yes' if status['restricted'] else '✓ No'}")

            if status['error']:
                print(f"  Error: {status['error']}")

            return status['valid']

        except Exception as e:
            print(f"\n✗ Error checking account: {e}")
            return False

        finally:
            await uploader.close()

    def list_cookies(self):
        """List all saved cookie accounts."""
        print(f"\n{'='*60}")
        print("Saved Cookie Accounts")
        print('='*60)

        accounts = self.cookie_manager.list_accounts()

        if not accounts:
            print("\nNo saved accounts found.")
            print("Add cookies with: python cli.py cookies --add <account_id>")
            return

        print(f"\nFound {len(accounts)} account(s):\n")

        for account in accounts:
            info = self.cookie_manager.get_account_info(account)

            if info:
                status = '✓' if info['valid'] else '✗'
                age = info['age_days']
                print(f"{status} {account}")
                print(f"   Age: {age} days, Cookies: {info['cookie_count']}")

                if not info['valid']:
                    if info['missing_cookies']:
                        print(f"   Missing: {', '.join(info['missing_cookies'])}")
                    if info['expired_cookies']:
                        print(f"   Expired: {', '.join(info['expired_cookies'])}")

                print()

    def validate_cookies(self, account: str):
        """
        Validate cookies for an account.

        Args:
            account: Account ID
        """
        print(f"\n{'='*60}")
        print(f"Cookie Validation: {account}")
        print('='*60)

        cookies = self.cookie_manager.load_cookies(account)

        if not cookies:
            print(f"\n✗ No cookies found for account: {account}")
            return False

        validation = self.cookie_manager.validate_cookies(cookies)

        print(f"\n📋 Validation Results:")
        print(f"  Valid: {'✓ Yes' if validation['valid'] else '✗ No'}")
        print(f"  Total Cookies: {len(cookies)}")

        if validation['missing_cookies']:
            print(f"\n⚠️  Missing Required Cookies:")
            for cookie in validation['missing_cookies']:
                print(f"    - {cookie}")

        if validation['expired_cookies']:
            print(f"\n⚠️  Expired Cookies:")
            for cookie in validation['expired_cookies']:
                print(f"    - {cookie}")

        if validation['expires_soon']:
            print(f"\n⏰ Cookies Expiring Soon:")
            for cookie in validation['expires_soon']:
                print(f"    - {cookie['name']}: {cookie['expires_in_days']:.1f} days")

        if validation['valid']:
            print(f"\n✓ Cookies are valid and ready to use!")
        else:
            print(f"\n✗ Cookies need attention. Please refresh them.")

        return validation['valid']

    def extract_cookies(self, account: str, browser: str = 'chrome'):
        """
        Extract cookies from browser.

        Args:
            account: Account ID to save under
            browser: Browser to extract from
        """
        print(f"\n{'='*60}")
        print(f"Extract Cookies: {browser} → {account}")
        print('='*60)

        try:
            print(f"\n🔍 Extracting cookies from {browser}...")
            print("   Make sure you're logged into TikTok in this browser!")

            cookies = self.cookie_manager.extract_from_browser(browser)

            if not cookies:
                print(f"\n✗ No cookies found. Make sure:")
                print(f"  1. You're logged into TikTok in {browser}")
                print(f"  2. {browser} browser is installed")
                print(f"  3. You have browser-cookie3 package installed")
                return False

            # Filter TikTok cookies
            tiktok_cookies = self.cookie_manager.filter_tiktok_cookies(cookies)

            if not tiktok_cookies:
                print(f"\n✗ No TikTok cookies found in {browser}")
                return False

            # Save cookies
            filepath = self.cookie_manager.save_cookies(tiktok_cookies, account)

            print(f"\n✓ Extracted {len(tiktok_cookies)} cookies")
            print(f"  Saved to: {filepath}")

            # Validate
            validation = self.cookie_manager.validate_cookies(tiktok_cookies)

            if validation['valid']:
                print(f"\n✓ Cookies are valid and ready to use!")
            else:
                print(f"\n⚠️  Cookie validation warnings:")
                if validation['missing_cookies']:
                    print(f"  Missing: {', '.join(validation['missing_cookies'])}")

            return True

        except Exception as e:
            print(f"\n✗ Failed to extract cookies: {e}")
            logger.exception(e)
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='TikTok Uploader CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Upload a video:
    python cli.py upload --video video.mp4 --account my_account \\
                        --caption "Amazing video!" --hashtags "fyp,viral"

  Check account status:
    python cli.py account --check my_account

  List all saved accounts:
    python cli.py cookies --list

  Validate cookies:
    python cli.py cookies --validate my_account

  Extract cookies from browser:
    python cli.py cookies --extract my_account --browser chrome
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a video')
    upload_parser.add_argument('--video', required=True, help='Video file path')
    upload_parser.add_argument('--account', required=True, help='Account ID')
    upload_parser.add_argument('--caption', required=True, help='Video caption')
    upload_parser.add_argument('--hashtags', help='Comma-separated hashtags')
    upload_parser.add_argument('--privacy', default='public', choices=['public', 'friends', 'private'])
    upload_parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    upload_parser.add_argument('--proxy', help='Proxy URL')

    # Account command
    account_parser = subparsers.add_parser('account', help='Account management')
    account_parser.add_argument('--check', metavar='ACCOUNT', help='Check account status')

    # Cookies command
    cookies_parser = subparsers.add_parser('cookies', help='Cookie management')
    cookies_parser.add_argument('--list', action='store_true', help='List all saved accounts')
    cookies_parser.add_argument('--validate', metavar='ACCOUNT', help='Validate cookies')
    cookies_parser.add_argument('--extract', metavar='ACCOUNT', help='Extract cookies from browser')
    cookies_parser.add_argument('--browser', default='chrome', help='Browser to extract from')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = TikTokCLI()

    # Execute command
    try:
        if args.command == 'upload':
            asyncio.run(cli.upload_video(
                video_path=args.video,
                account=args.account,
                caption=args.caption,
                hashtags=args.hashtags,
                privacy=args.privacy,
                headless=args.headless,
                proxy=args.proxy
            ))

        elif args.command == 'account':
            if args.check:
                asyncio.run(cli.check_account(args.check))
            else:
                account_parser.print_help()

        elif args.command == 'cookies':
            if args.list:
                cli.list_cookies()
            elif args.validate:
                cli.validate_cookies(args.validate)
            elif args.extract:
                cli.extract_cookies(args.extract, args.browser)
            else:
                cookies_parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
