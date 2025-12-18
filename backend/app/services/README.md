# TikTok Auto-Poster Services

This directory contains the core services for automated TikTok video uploading with anti-detection measures.

## Components

### 1. TikTokUploader (`tiktok_uploader.py`)
Main service for uploading videos to TikTok using Playwright with stealth capabilities.

**Features:**
- Browser automation with stealth plugin
- Proxy support
- Cookie-based authentication
- Human-like behaviors (random delays, mouse movements, typing patterns)
- Captcha solving integration
- Video upload with caption and hashtags
- Privacy settings configuration
- Scheduling support

**Usage Example:**
```python
import asyncio
from app.services import TikTokUploader

async def upload_example():
    # Initialize uploader
    uploader = TikTokUploader(
        proxy={'server': 'http://proxy.example.com:8080'},
        cookies='path/to/cookies.json',
        captcha_api_key='your-sadcaptcha-api-key',
        headless=True
    )

    try:
        # Setup browser
        await uploader.setup_browser()

        # Upload video
        result = await uploader.upload_video(
            video_path='/path/to/video.mp4',
            caption='Check out this amazing video!',
            hashtags=['fyp', 'viral', 'trending'],
            privacy='public',
            allow_comments=True,
            allow_duet=True,
            allow_stitch=True
        )

        if result['success']:
            print(f"Video uploaded: {result['video_url']}")
        else:
            print(f"Upload failed: {result['error']}")

    finally:
        await uploader.close()

# Run
asyncio.run(upload_example())
```

### 2. SadCaptchaSolver (`captcha_solver.py`)
Captcha solving service for TikTok's various captcha types.

**Supported Captcha Types:**
- Slider/Puzzle captchas
- Rotation captchas
- 3D shape captchas

**Usage Example:**
```python
from app.services import SadCaptchaSolver

# Initialize solver
solver = SadCaptchaSolver(api_key='your-api-key')

# Solve puzzle captcha
with open('captcha_image.png', 'rb') as f:
    image_data = f.read()

solution = solver.solve_puzzle(image_data)

if solution['success']:
    print(f"Slide to position: {solution['x_position']}")

    # Report if solution worked
    solver.report_solution(solution['solution_id'], success=True)
```

## Configuration

### Environment Variables
```bash
# Required for captcha solving
SADCAPTCHA_API_KEY=your_api_key_here
```

### Cookies Format
Cookies should be in JSON format (Netscape/Chrome format):
```json
[
  {
    "name": "sessionid",
    "value": "your_session_id",
    "domain": ".tiktok.com",
    "path": "/",
    "expires": 1735689600,
    "httpOnly": true,
    "secure": true
  }
]
```

### Browser Profile Example
```python
profile = {
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'viewport': {'width': 1920, 'height': 1080},
    'timezone': 'America/New_York',
    'locale': 'en-US',
    'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},
    'permissions': ['geolocation']
}
```

## Anti-Detection Features

### Stealth Measures
1. **Playwright Stealth Plugin**: Removes automation indicators
2. **WebDriver Property Hiding**: Overrides `navigator.webdriver`
3. **Chrome Runtime Simulation**: Adds realistic Chrome properties
4. **Plugin Spoofing**: Simulates real browser plugins
5. **Permission API Override**: Realistic permission handling

### Human-like Behaviors
1. **Random Delays**: 1-4 seconds between actions
2. **Mouse Movements**: Realistic cursor movements before clicks
3. **Typing Simulation**: Random delays between keystrokes (50-150ms)
4. **Random Scrolling**: Occasional scrolling behavior
5. **Click Randomization**: Clicks on random points within elements

## Error Handling

The services include comprehensive error handling:

```python
try:
    result = await uploader.upload_video(...)
except TikTokUploadError as e:
    # Handle upload-specific errors
    logger.error(f"Upload error: {e}")
except Exception as e:
    # Handle unexpected errors
    logger.exception(f"Unexpected error: {e}")
```

## Account Status Checking

```python
status = await uploader.check_account_status()

if status['valid'] and status['can_upload']:
    print("Account is ready for uploads")
elif not status['logged_in']:
    print("Need to re-authenticate")
elif status['restricted']:
    print(f"Account restricted: {status['error']}")
```

## Important Notes

### TikTok Selector Updates
TikTok frequently updates their UI. If uploads fail, check and update these selectors in `TikTokUploader.SELECTORS`:
- `file_input`: File upload input
- `caption_input`: Caption text area
- `post_button`: Post/submit button
- `upload_progress`: Upload progress indicator
- `video_preview`: Video preview element

### Rate Limiting
To avoid detection and bans:
- Wait 5-10 minutes between uploads
- Use different proxies for different accounts
- Randomize upload times
- Don't upload more than 3-5 videos per day per account

### Cookie Expiration
Cookies expire periodically. Implement:
- Regular cookie refresh
- Login flow for expired sessions
- Cookie storage with expiration tracking

## Dependencies

Required packages (see requirements.txt):
```
playwright==1.40.0
playwright-stealth==1.0.9
requests==2.31.0
```

Install with:
```bash
pip install -r requirements.txt
playwright install chromium
```

## Troubleshooting

### Common Issues

1. **Captcha Not Solving**
   - Verify SadCaptcha API key is set
   - Check API credits
   - Review captcha type detection

2. **Login Fails**
   - Verify cookies are fresh (< 30 days old)
   - Check cookie format
   - Ensure all required cookies are present

3. **Upload Timeout**
   - Increase timeout values
   - Check network connection
   - Verify video file is valid

4. **Selectors Not Found**
   - TikTok UI may have changed
   - Update selectors in code
   - Use browser inspection to find new selectors

## Security Considerations

- Store API keys in environment variables
- Keep cookies encrypted at rest
- Use secure proxy connections (HTTPS)
- Rotate proxies and user agents regularly
- Never commit credentials to version control
