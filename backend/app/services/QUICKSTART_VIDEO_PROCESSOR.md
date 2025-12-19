# Video Processor Quick Start Guide

## Installation

1. **Install FFmpeg** (required):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows - Download from https://ffmpeg.org/download.html
   ```

2. **Verify Installation**:
   ```bash
   ffmpeg -version
   ```

## Basic Usage

### Import the Service

```python
from app.services import VideoProcessor, VideoProcessorError
```

### Create Unique Video Variation

```python
import asyncio

async def create_unique_video():
    # Initialize processor
    processor = VideoProcessor()

    # Process video with unique transformations
    try:
        result = await processor.process_video(
            input_path="/path/to/original.mp4",
            output_path="/path/to/unique.mp4"
        )

        print(f"Success! Created: {result['output_path']}")
        print(f"Input duration: {result['input_info']['duration']}s")
        print(f"Output duration: {result['output_info']['duration']}s")

    except VideoProcessorError as e:
        print(f"Error: {e}")

# Run
asyncio.run(create_unique_video())
```

### Create Multiple Variations

```python
async def create_variations():
    processor = VideoProcessor()

    # Create 5 unique variations
    results = await processor.batch_process(
        input_path="/path/to/video.mp4",
        count=5,
        output_dir="/path/to/output"
    )

    successful = [r for r in results if r['success']]
    print(f"Created {len(successful)} variations")

    # Verify all are unique
    files = [r['result']['output_path'] for r in successful]
    hash_check = await processor.verify_unique_hashes(files)

    if hash_check['all_unique']:
        print("All variations have unique file hashes!")
    else:
        print(f"Warning: {len(hash_check['duplicates'])} duplicates found")

asyncio.run(create_variations())
```

### Get Video Information

```python
async def analyze_video():
    processor = VideoProcessor()

    info = await processor.get_video_info("/path/to/video.mp4")

    print(f"Duration: {info['duration']} seconds")
    print(f"Resolution: {info['width']}x{info['height']}")
    print(f"Codec: {info['codec']}")
    print(f"Bitrate: {info['bitrate']} bps")
    print(f"FPS: {info['fps']}")

asyncio.run(analyze_video())
```

### Strip Metadata Only

```python
async def remove_metadata():
    processor = VideoProcessor()

    await processor.strip_metadata(
        input_path="/path/to/video.mp4",
        output_path="/path/to/clean.mp4"
    )

    print("Metadata removed!")

asyncio.run(remove_metadata())
```

### Generate Unique Filename

```python
processor = VideoProcessor()

# Generate UUID-based filename
filename = processor.generate_unique_filename("mp4")
print(filename)  # e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890.mp4"
```

## Configuration Options

### Custom Settings

```python
processor = VideoProcessor(
    output_format="mp4",       # Output format
    video_codec="libx264",     # H.264 codec
    audio_codec="aac",         # AAC audio
    preset="fast",             # Encoding speed (ultrafast to veryslow)
    crf=23                     # Quality (0-51, lower=better)
)
```

### Presets Explained

- **ultrafast**: Fastest encoding, largest files
- **fast**: Good speed, decent compression
- **medium**: Balanced (default)
- **slow**: Better compression, slower
- **veryslow**: Best compression, slowest

### Quality (CRF) Guide

- **18**: Visually lossless (large files)
- **23**: Default, high quality
- **28**: Acceptable quality (smaller files)
- **32+**: Low quality (not recommended)

## Common Patterns

### TikTok Upload Integration

```python
from app.services import VideoProcessor, TikTokUploader

async def upload_unique_video(original_path):
    processor = VideoProcessor()
    uploader = TikTokUploader()

    # Create unique variation
    temp_path = f"/tmp/{processor.generate_unique_filename('mp4')}"

    await processor.process_video(original_path, temp_path)

    # Upload to TikTok
    await uploader.upload(temp_path)

    # Cleanup
    os.remove(temp_path)
```

### Reproducible Variations

```python
async def create_reproducible():
    processor = VideoProcessor()

    # Same seed = same variation
    result1 = await processor.process_video(
        input_path="video.mp4",
        output_path="output1.mp4",
        variation_seed=42
    )

    result2 = await processor.process_video(
        input_path="video.mp4",
        output_path="output2.mp4",
        variation_seed=42
    )

    # output1.mp4 and output2.mp4 will have identical transformations
    # (but different filenames, so different hashes if you include metadata)
```

### Batch Processing with Custom Names

```python
async def custom_batch():
    processor = VideoProcessor()

    video_ids = [101, 102, 103, 104, 105]

    for video_id in video_ids:
        output = f"/output/video_{video_id}.mp4"

        await processor.process_video(
            input_path="source.mp4",
            output_path=output,
            variation_seed=video_id
        )

        print(f"Created variation for ID {video_id}")
```

## Error Handling

```python
from app.services import VideoProcessorError

async def safe_processing():
    processor = VideoProcessor()

    try:
        result = await processor.process_video(
            input_path="input.mp4",
            output_path="output.mp4"
        )

    except VideoProcessorError as e:
        if "not found" in str(e):
            print("Input file missing")
        elif "FFmpeg" in str(e):
            print("FFmpeg not installed or not in PATH")
        else:
            print(f"Processing error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Logging

```python
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now VideoProcessor will log all operations
processor = VideoProcessor()
```

## Testing Without FFmpeg

```python
# For unit tests where FFmpeg is not available
processor = VideoProcessor(verify_ffmpeg=False)

# Can use these methods without FFmpeg:
filename = processor.generate_unique_filename("mp4")
params = processor._generate_variation_params(seed=42)

# These methods require FFmpeg:
# await processor.process_video(...)      # Will fail
# await processor.get_video_info(...)     # Will fail
```

## Troubleshooting

### Error: FFmpeg not found

**Solution**: Install FFmpeg and ensure it's in PATH
```bash
which ffmpeg  # Should show path to FFmpeg
```

### Processing is slow

**Solutions**:
- Use faster preset: `preset="fast"` or `preset="veryfast"`
- Increase CRF (lower quality): `crf=28`
- Check CPU usage (encoding is CPU-intensive)

### Output files too large

**Solutions**:
- Use slower preset: `preset="slow"` (better compression)
- Increase CRF: `crf=28` or `crf=32`

### Variations not unique

**Check**:
```python
# Verify transformations are being applied
result = await processor.process_video(...)
print(result['variation_params'])  # Should show random values

# Verify hashes are different
hash_check = await processor.verify_unique_hashes([file1, file2, file3])
print(hash_check['all_unique'])  # Should be True
```

## Next Steps

- Read full documentation: `VIDEO_PROCESSOR_README.md`
- See usage examples: `video_processor_example.py`
- Run tests: `python3 test_video_processor.py`
- Check implementation details: `IMPLEMENTATION_SUMMARY.md`

## Support

For issues or questions:
1. Check logs (enable with `logging.basicConfig(level=logging.DEBUG)`)
2. Verify FFmpeg installation (`ffmpeg -version`)
3. Review documentation files
4. Check error messages for specific guidance
