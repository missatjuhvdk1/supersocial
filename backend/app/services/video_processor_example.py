"""
Example usage of VideoProcessor service.

This script demonstrates how to use the VideoProcessor class
for creating unique video variations.
"""

import asyncio
import logging
from pathlib import Path
from video_processor import VideoProcessor, VideoProcessorError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def example_single_process():
    """Example: Process a single video with variations"""
    processor = VideoProcessor(
        output_format="mp4",
        video_codec="libx264",
        preset="medium",
        crf=23
    )

    input_video = "/path/to/input/video.mp4"
    output_video = "/path/to/output/processed_video.mp4"

    try:
        result = await processor.process_video(
            input_path=input_video,
            output_path=output_video,
            variation_seed=42  # Use seed for reproducible result
        )

        logger.info(f"Processing completed!")
        logger.info(f"Input duration: {result['input_info']['duration']}s")
        logger.info(f"Output duration: {result['output_info']['duration']}s")
        logger.info(f"Variation params: {result['variation_params']}")

    except VideoProcessorError as e:
        logger.error(f"Processing failed: {e}")


async def example_batch_process():
    """Example: Create multiple unique variations"""
    processor = VideoProcessor()

    input_video = "/path/to/input/video.mp4"
    output_dir = "/path/to/output/variations"

    try:
        results = await processor.batch_process(
            input_path=input_video,
            count=5,  # Create 5 variations
            output_dir=output_dir
        )

        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]

        logger.info(f"Batch processing completed!")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")

        # Verify all variations have unique hashes
        output_files = [
            r['result']['output_path']
            for r in results if r['success']
        ]

        hash_check = await processor.verify_unique_hashes(output_files)
        logger.info(f"Hash verification: {hash_check}")

    except VideoProcessorError as e:
        logger.error(f"Batch processing failed: {e}")


async def example_get_info():
    """Example: Get video information"""
    processor = VideoProcessor()

    video_path = "/path/to/video.mp4"

    try:
        info = await processor.get_video_info(video_path)

        logger.info(f"Video Information:")
        logger.info(f"  Duration: {info['duration']}s")
        logger.info(f"  Resolution: {info['width']}x{info['height']}")
        logger.info(f"  Codec: {info['codec']}")
        logger.info(f"  Bitrate: {info['bitrate']} bps")
        logger.info(f"  FPS: {info['fps']}")
        logger.info(f"  Format: {info['format']}")

    except VideoProcessorError as e:
        logger.error(f"Failed to get video info: {e}")


async def example_strip_metadata():
    """Example: Strip metadata from video"""
    processor = VideoProcessor()

    input_video = "/path/to/input/video.mp4"
    output_video = "/path/to/output/no_metadata.mp4"

    try:
        await processor.strip_metadata(
            input_path=input_video,
            output_path=output_video
        )

        logger.info("Metadata stripped successfully!")

    except VideoProcessorError as e:
        logger.error(f"Failed to strip metadata: {e}")


async def example_unique_filenames():
    """Example: Generate unique filenames"""
    processor = VideoProcessor()

    # Generate 10 unique filenames
    filenames = [
        processor.generate_unique_filename("mp4")
        for _ in range(10)
    ]

    logger.info("Generated unique filenames:")
    for filename in filenames:
        logger.info(f"  {filename}")


async def main():
    """Run all examples"""
    logger.info("=== VideoProcessor Examples ===\n")

    logger.info("Example 1: Generate unique filenames")
    await example_unique_filenames()

    # Uncomment to run other examples (requires actual video files)
    # logger.info("\nExample 2: Get video information")
    # await example_get_info()

    # logger.info("\nExample 3: Process single video")
    # await example_single_process()

    # logger.info("\nExample 4: Strip metadata")
    # await example_strip_metadata()

    # logger.info("\nExample 5: Batch process videos")
    # await example_batch_process()


if __name__ == "__main__":
    asyncio.run(main())
