# TikTok Auto-Poster Setup Guide

Complete setup instructions for the TikTok uploader service with Playwright and stealth.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Google Chrome or Chromium browser
- Active TikTok account(s)
- (Optional) SadCaptcha API key for automated captcha solving

## Installation

### 1. Install Python Dependencies

```bash
# Navigate to backend directory
cd backend

# Install all required packages
pip install -r requirements.txt

# Install Playwright browsers (Chromium)
playwright install chromium

# Install system dependencies for Playwright (Linux/WSL)
playwright install-deps
```

### 2. Verify Installation

```bash
# Test Playwright installation
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Test playwright-stealth
python -c "from playwright_stealth import stealth_sync; print('Stealth OK')"
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the backend directory:

```bash
# .env

# SadCaptcha API Key (get from https://sadcaptcha.com)
SADCAPTCHA_API_KEY=your_api_key_here

# Database URL (if using database)
DATABASE_URL=postgresql://user:pass@localhost/tiktok_poster

# Redis URL (if using task queue)
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=development
DEBUG=True
```

### 2. Get TikTok Cookies

You need valid TikTok session cookies for authentication. Here are several methods:

#### Method 1: Browser Extension (Recommended)

1. Install a cookie export extension:
   - Chrome: [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
   - Firefox: [Cookie Quick Manager](https://addons.mozilla.org/en-US/firefox/addon/cookie-quick-manager/)

2. Log into TikTok in your browser
3. Open the cookie extension
4. Export cookies for `tiktok.com` as JSON
5. Save to `cookies/account_name_cookies.json`

#### Method 2: Using Cookie Manager Script

```python
from app.services import CookieManager

# Create manager
manager = CookieManager(storage_path='./cookies')

# Extract cookies from your Chrome browser
cookies = manager.extract_from_browser('chrome')

# Save for an account
manager.save_cookies(cookies, 'my_account')
```

#### Method 3: Manual Cookie File

Create a JSON file with this structure:

```json
[
  {
    "name": "sessionid",
    "value": "your_session_id_here",
    "domain": ".tiktok.com",
    "path": "/",
    "expires": 1735689600,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  },
  {
    "name": "sid_tt",
    "value": "your_sid_tt_here",
    "domain": ".tiktok.com",
    "path": "/",
    "expires": 1735689600,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  },
  {
    "name": "sid_guard",
    "value": "your_sid_guard_here",
    "domain": ".tiktok.com",
    "path": "/",
    "expires": 1735689600,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  }
]
```

**Required cookies:**
- `sessionid` - Main session identifier
- `sid_tt` - TikTok session ID
- `sid_guard` - Session guard token

### 3. Verify Cookies

```python
from app.services import CookieManager

manager = CookieManager()
cookies = manager.load_cookies('my_account')

# Validate cookies
validation = manager.validate_cookies(cookies)

if validation['valid']:
    print("✓ Cookies are valid!")
else:
    print("✗ Issues found:")
    print(f"  Missing: {validation['missing_cookies']}")
    print(f"  Expired: {validation['expired_cookies']}")
```

## Directory Structure

Create these directories in your backend folder:

```bash
mkdir -p cookies
mkdir -p uploads
mkdir -p logs
mkdir -p data
```

```
backend/
├── app/
│   └── services/
│       ├── __init__.py
│       ├── tiktok_uploader.py
│       ├── captcha_solver.py
│       ├── cookie_manager.py
│       ├── example_usage.py
│       └── README.md
├── cookies/                    # Cookie storage
│   └── account_name_cookies.json
├── uploads/                    # Videos to upload
│   └── video.mp4
├── logs/                       # Application logs
├── .env                        # Environment variables
└── requirements.txt
```

## Quick Start

### 1. Basic Upload Test

```python
import asyncio
from app.services import TikTokUploader

async def test_upload():
    uploader = TikTokUploader(
        cookies='cookies/my_account_cookies.json',
        headless=False,  # Watch it work!
        captcha_api_key='your_sadcaptcha_key'
    )

    try:
        await uploader.setup_browser()

        result = await uploader.upload_video(
            video_path='uploads/test_video.mp4',
            caption='Test upload from automation!',
            hashtags=['test', 'automation']
        )

        if result['success']:
            print(f"Success! URL: {result['video_url']}")
        else:
            print(f"Failed: {result['error']}")

    finally:
        await uploader.close()

asyncio.run(test_upload())
```

### 2. Run Example Scripts

```bash
# Run interactive examples
python app/services/example_usage.py
```

### 3. Account Status Check

```python
import asyncio
from app.services import TikTokUploader

async def check_account():
    uploader = TikTokUploader(
        cookies='cookies/my_account_cookies.json',
        headless=True
    )

    try:
        status = await uploader.check_account_status()
        print(f"Account valid: {status['valid']}")
        print(f"Logged in: {status['logged_in']}")
        print(f"Can upload: {status.get('can_upload', False)}")

    finally:
        await uploader.close()

asyncio.run(check_account())
```

## Proxy Setup (Optional)

For better anonymity and avoiding rate limits, use proxies:

### Proxy Configuration

```python
proxy_config = {
    'server': 'http://proxy.example.com:8080',
    'username': 'proxy_user',  # Optional
    'password': 'proxy_pass'   # Optional
}

uploader = TikTokUploader(
    proxy=proxy_config,
    cookies='cookies/account_cookies.json'
)
```

### Rotating Proxies

```python
proxies = [
    {'server': 'http://proxy1.example.com:8080'},
    {'server': 'http://proxy2.example.com:8080'},
    {'server': 'http://proxy3.example.com:8080'},
]

# Use different proxy for each account
for i, account in enumerate(accounts):
    proxy = proxies[i % len(proxies)]
    uploader = TikTokUploader(proxy=proxy, cookies=account['cookies'])
    # ... upload videos
```

## Troubleshooting

### Issue: "playwright command not found"

```bash
# Install Playwright CLI globally
pip install playwright
playwright install
```

### Issue: "Browser not found"

```bash
# Reinstall browsers
playwright install chromium --force
```

### Issue: "Cookies invalid or expired"

1. Clear browser cookies for TikTok
2. Log in again
3. Export fresh cookies
4. Verify cookies are less than 30 days old

### Issue: "Captcha not solving"

1. Check SadCaptcha API key is set
2. Verify you have API credits
3. Check captcha type is supported
4. Try manual solving first time

### Issue: "Upload timeout"

1. Increase timeout values in code
2. Check video file size (max ~500MB)
3. Verify network connection
4. Try with smaller video

### Issue: "Account restricted"

1. TikTok may have flagged the account
2. Wait 24-48 hours
3. Use different proxy/IP
4. Reduce upload frequency
5. Vary upload times

## Best Practices

### 1. Rate Limiting

```python
# Wait between uploads
import random

for video in videos:
    await uploader.upload_video(...)

    # Random delay 5-10 minutes
    delay = random.randint(300, 600)
    await asyncio.sleep(delay)
```

### 2. Cookie Rotation

```python
# Refresh cookies every 2 weeks
from datetime import datetime, timedelta

manager = CookieManager()

for account_id in manager.list_accounts():
    info = manager.get_account_info(account_id)

    if info['age_days'] > 14:
        print(f"Cookies for {account_id} need refresh")
        # Re-export cookies from browser
```

### 3. Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def upload_with_retry(uploader, video_path, caption):
    result = await uploader.upload_video(video_path, caption)

    if not result['success']:
        raise Exception(result['error'])

    return result
```

### 4. Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/uploader.log'),
        logging.StreamHandler()
    ]
)
```

## Security Considerations

1. Never commit cookies to version control
2. Add to .gitignore:
   ```
   cookies/
   *.json
   .env
   ```

3. Encrypt cookie files at rest:
   ```python
   from cryptography.fernet import Fernet

   # Generate key once
   key = Fernet.generate_key()

   # Encrypt cookies
   cipher = Fernet(key)
   encrypted = cipher.encrypt(cookie_json.encode())
   ```

4. Use environment variables for sensitive data
5. Rotate proxies regularly
6. Monitor for suspicious activity
7. Keep API keys secure

## Production Deployment

### Using with Celery

```python
from celery import Celery
from app.services import TikTokUploader

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
async def upload_video_task(account_id, video_path, caption, hashtags):
    uploader = TikTokUploader(
        cookies=f'cookies/{account_id}_cookies.json',
        headless=True
    )

    try:
        await uploader.setup_browser()
        result = await uploader.upload_video(video_path, caption, hashtags)
        return result
    finally:
        await uploader.close()
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps

COPY . .

CMD ["python", "main.py"]
```

## Support

For issues and questions:
- Check logs in `logs/` directory
- Review README.md for common solutions
- Update selectors if TikTok UI changes
- Test with headless=False to debug visually

## Next Steps

1. Test with a single video upload
2. Set up cookie rotation schedule
3. Implement error monitoring
4. Add video queue management
5. Scale with multiple accounts
6. Monitor upload success rates
