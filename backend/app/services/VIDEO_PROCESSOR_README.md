# Video Processor Service

A robust FFmpeg-based video processing service for creating unique variations of videos to avoid duplicate detection on platforms like TikTok.

## Features

- **Unique Video Variations**: Creates variations with different file hashes and subtle visual differences
- **Async Operations**: All FFmpeg operations run asynchronously for better performance
- **Batch Processing**: Process multiple variations in one call
- **Metadata Stripping**: Remove EXIF and other metadata
- **Video Analysis**: Get detailed video information (duration, resolution, codec, etc.)
- **Comprehensive Error Handling**: Detailed error messages and logging

## Installation

### Requirements

1. **FFmpeg**: Must be installed and accessible in PATH
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

2. **Python Dependencies**: (Add to requirements.txt)
   ```
   # No additional Python packages required - uses stdlib only!
   ```

## Usage

### Basic Initialization

```python
from app.services import VideoProcessor

# Default configuration
processor = VideoProcessor()

# Custom configuration
processor = VideoProcessor(
    output_format="mp4",
    video_codec="libx264",
    audio_codec="aac",
    preset="medium",  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    crf=23  # 0-51, lower is better quality (18-28 is typical range)
)
```

### Process Single Video

```python
import asyncio

async def process():
    processor = VideoProcessor()

    result = await processor.process_video(
        input_path="/path/to/input.mp4",
        output_path="/path/to/output.mp4",
        variation_seed=42  # Optional: for reproducible variations
    )

    print(f"Processed: {result['output_path']}")
    print(f"Params used: {result['variation_params']}")

asyncio.run(process())
```

### Batch Process Multiple Variations

```python
async def batch():
    processor = VideoProcessor()

    results = await processor.batch_process(
        input_path="/path/to/input.mp4",
        count=10,  # Create 10 unique variations
        output_dir="/path/to/output/dir"
    )

    successful = [r for r in results if r['success']]
    print(f"Created {len(successful)} variations")

asyncio.run(batch())
```

### Get Video Information

```python
async def get_info():
    processor = VideoProcessor()

    info = await processor.get_video_info("/path/to/video.mp4")

    print(f"Duration: {info['duration']}s")
    print(f"Resolution: {info['width']}x{info['height']}")
    print(f"Codec: {info['codec']}")
    print(f"Bitrate: {info['bitrate']} bps")
    print(f"FPS: {info['fps']}")

asyncio.run(get_info())
```

### Strip Metadata

```python
async def strip():
    processor = VideoProcessor()

    await processor.strip_metadata(
        input_path="/path/to/input.mp4",
        output_path="/path/to/output.mp4"
    )

asyncio.run(strip())
```

### Generate Unique Filename

```python
processor = VideoProcessor()

filename = processor.generate_unique_filename("mp4")
print(filename)  # e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890.mp4"
```

### Verify Unique Hashes

```python
async def verify():
    processor = VideoProcessor()

    files = [
        "/path/to/variation1.mp4",
        "/path/to/variation2.mp4",
        "/path/to/variation3.mp4"
    ]

    result = await processor.verify_unique_hashes(files)

    print(f"Total files: {result['total_files']}")
    print(f"Unique hashes: {result['unique_hashes']}")
    print(f"All unique: {result['all_unique']}")

asyncio.run(verify())
```

## Transformations Applied

Each processed video receives the following transformations to ensure uniqueness:

1. **Brightness Adjustment**: Random adjustment between -0.03 to +0.03
2. **Saturation Adjustment**: Random factor between 0.97 to 1.03
3. **Contrast Adjustment**: Random factor between 0.98 to 1.02
4. **Tiny Crop**: Random 1-3 pixel crop from each edge, then scale back
5. **Bitrate Variation**: Random ±3% bitrate adjustment
6. **Noise Addition**: Subtle imperceptible noise (strength 1-3)
7. **Speed Variation**: Random 0.99x to 1.01x speed with audio pitch correction
8. **Frame Offset**: Random starting frame offset (0-3 frames)
9. **Metadata Stripping**: All EXIF/metadata removed

All transformations are designed to be imperceptible to human viewers while ensuring different file hashes.

## API Reference

### VideoProcessor Class

#### Constructor

```python
VideoProcessor(
    output_format: str = "mp4",
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    preset: str = "medium",
    crf: int = 23
)
```

#### Methods

##### `async process_video(input_path, output_path, variation_seed=None) -> Dict`

Process a video with all transformations.

**Parameters:**
- `input_path` (str): Path to input video
- `output_path` (str): Path to output video
- `variation_seed` (int, optional): Seed for reproducible variations

**Returns:**
- Dictionary with processing information

**Raises:**
- `VideoProcessorError`: If processing fails

##### `async strip_metadata(input_path, output_path) -> None`

Remove all EXIF/metadata from video.

**Parameters:**
- `input_path` (str): Path to input video
- `output_path` (str): Path to output video

**Raises:**
- `VideoProcessorError`: If stripping fails

##### `generate_unique_filename(extension="mp4") -> str`

Generate UUID-based unique filename.

**Parameters:**
- `extension` (str): File extension

**Returns:**
- Unique filename string

##### `async batch_process(input_path, count, output_dir) -> List[Dict]`

Create multiple unique variations of a video.

**Parameters:**
- `input_path` (str): Path to input video
- `count` (int): Number of variations to create
- `output_dir` (str): Directory to save variations

**Returns:**
- List of processing results

**Raises:**
- `VideoProcessorError`: If batch processing fails

##### `async get_video_info(path) -> Dict`

Get video information using ffprobe.

**Parameters:**
- `path` (str): Path to video file

**Returns:**
- Dictionary with video information:
  - `duration` (float): Video duration in seconds
  - `width` (int): Video width in pixels
  - `height` (int): Video height in pixels
  - `codec` (str): Video codec name
  - `bitrate` (int): Video bitrate in bps
  - `fps` (float): Frames per second
  - `format` (str): Container format

**Raises:**
- `VideoProcessorError`: If unable to get info

##### `async verify_unique_hashes(file_paths) -> Dict`

Verify that all processed videos have unique file hashes.

**Parameters:**
- `file_paths` (List[str]): List of video file paths to check

**Returns:**
- Dictionary with hash analysis results:
  - `total_files` (int): Total number of files checked
  - `unique_hashes` (int): Number of unique hashes
  - `duplicates` (List): List of duplicate file pairs
  - `all_unique` (bool): True if all files are unique

## Error Handling

The service uses a custom `VideoProcessorError` exception for all errors:

```python
from app.services import VideoProcessorError

try:
    result = await processor.process_video(...)
except VideoProcessorError as e:
    print(f"Processing failed: {e}")
```

## Logging

The service uses Python's standard logging module. Configure it in your application:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Log levels used:
- `INFO`: Operation start/completion, important events
- `DEBUG`: Detailed processing parameters, filter strings
- `ERROR`: Processing failures, FFmpeg errors
- `WARNING`: Non-critical issues

## Performance Considerations

### Encoding Presets

The `preset` parameter affects encoding speed vs compression:
- **ultrafast**: Fastest encoding, largest file size
- **medium**: Balanced (default)
- **slow/slower/veryslow**: Better compression, slower encoding

### CRF (Constant Rate Factor)

The `crf` parameter controls quality (0-51):
- **18**: Visually lossless
- **23**: Default, good quality
- **28**: Acceptable quality, smaller files
- Higher values = lower quality, smaller files

### Batch Processing

For large batches, consider processing in chunks to manage memory:

```python
async def process_large_batch(input_video, total_count, chunk_size=10):
    processor = VideoProcessor()
    all_results = []

    for i in range(0, total_count, chunk_size):
        chunk_count = min(chunk_size, total_count - i)
        results = await processor.batch_process(
            input_path=input_video,
            count=chunk_count,
            output_dir=f"/output/batch_{i}"
        )
        all_results.extend(results)

    return all_results
```

## Integration with TikTok Auto-Poster

```python
from app.services import VideoProcessor, TikTokUploader

async def upload_with_variations(original_video, count=5):
    processor = VideoProcessor()
    uploader = TikTokUploader()

    # Create variations
    results = await processor.batch_process(
        input_path=original_video,
        count=count,
        output_dir="/tmp/variations"
    )

    # Upload each variation
    for result in results:
        if result['success']:
            video_path = result['result']['output_path']
            await uploader.upload(video_path)
```

## Testing

The service includes hash verification to ensure variations are unique:

```python
async def test_uniqueness():
    processor = VideoProcessor()

    # Create 5 variations
    results = await processor.batch_process(
        input_path="test_video.mp4",
        count=5,
        output_dir="test_output"
    )

    # Verify all have unique hashes
    files = [r['result']['output_path'] for r in results if r['success']]
    hash_check = await processor.verify_unique_hashes(files)

    assert hash_check['all_unique'], "Not all variations are unique!"
    print("All variations are unique!")
```

## Troubleshooting

### FFmpeg Not Found

**Error**: `FFmpeg is not installed or not accessible in PATH`

**Solution**: Install FFmpeg and ensure it's in your system PATH:
```bash
which ffmpeg  # Linux/macOS
where ffmpeg  # Windows
```

### Processing Too Slow

**Solutions**:
- Use faster preset: `preset="faster"` or `preset="veryfast"`
- Increase CRF value: `crf=28` (lower quality, faster)
- Reduce output resolution (modify filter complex)

### Output File Too Large

**Solutions**:
- Increase CRF value: `crf=28`
- Use slower preset for better compression: `preset="slow"`
- Reduce bitrate manually

### Variations Not Unique

If variations still have the same hash:
- Check that transformations are being applied (check logs)
- Increase variation ranges in `_generate_variation_params`
- Verify FFmpeg is actually processing (not just copying)

## License

Part of TikTok Auto-Poster backend service.
