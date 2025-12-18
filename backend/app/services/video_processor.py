"""
Video Processing Service for TikTok Auto-Poster

Uses FFmpeg to create unique variations of videos to avoid duplicate detection.
Each processed video has different hash and slightly different appearance.
"""

import asyncio
import os
import uuid
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import subprocess

logger = logging.getLogger(__name__)


class VideoProcessorError(Exception):
    """Custom exception for video processing errors"""
    pass


class VideoProcessor:
    """
    Video processor that creates unique variations of videos using FFmpeg.

    Features:
    - Multiple transformations to ensure unique file hash
    - Metadata stripping
    - Batch processing support
    - Async operations
    """

    def __init__(
        self,
        output_format: str = "mp4",
        video_codec: str = "libx264",
        audio_codec: str = "aac",
        preset: str = "medium",
        crf: int = 23,
        verify_ffmpeg: bool = True
    ):
        """
        Initialize VideoProcessor.

        Args:
            output_format: Output video format (default: mp4)
            video_codec: Video codec to use (default: libx264/h264)
            audio_codec: Audio codec to use (default: aac)
            preset: FFmpeg encoding preset (default: medium)
            crf: Constant Rate Factor for quality (default: 23, lower=better)
            verify_ffmpeg: Whether to verify FFmpeg on init (default: True)
        """
        self.output_format = output_format
        self.video_codec = video_codec
        self.audio_codec = audio_codec
        self.preset = preset
        self.crf = crf
        self._ffmpeg_verified = False

        # Verify FFmpeg is available (if requested)
        if verify_ffmpeg:
            self._verify_ffmpeg()

    def _verify_ffmpeg(self) -> None:
        """Verify FFmpeg is installed and accessible"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("FFmpeg found: %s", result.stdout.split('\n')[0])
            self._ffmpeg_verified = True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise VideoProcessorError(
                "FFmpeg is not installed or not accessible in PATH"
            ) from e

    def _ensure_ffmpeg(self) -> None:
        """Ensure FFmpeg is available before processing"""
        if not self._ffmpeg_verified:
            self._verify_ffmpeg()

    async def _run_ffmpeg(
        self,
        args: List[str],
        operation: str = "process"
    ) -> Tuple[str, str]:
        """
        Run FFmpeg command asynchronously.

        Args:
            args: FFmpeg command arguments
            operation: Description of operation for logging

        Returns:
            Tuple of (stdout, stderr)

        Raises:
            VideoProcessorError: If FFmpeg command fails
        """
        self._ensure_ffmpeg()
        cmd = ["ffmpeg", "-y"] + args
        logger.info(f"Running FFmpeg {operation}: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                logger.error(f"FFmpeg {operation} failed: {error_msg}")
                raise VideoProcessorError(
                    f"FFmpeg {operation} failed with code {process.returncode}: {error_msg}"
                )

            logger.info(f"FFmpeg {operation} completed successfully")
            return stdout.decode('utf-8', errors='replace'), stderr.decode('utf-8', errors='replace')

        except Exception as e:
            logger.error(f"Error running FFmpeg {operation}: {str(e)}")
            raise VideoProcessorError(f"Failed to execute FFmpeg: {str(e)}") from e

    def _generate_variation_params(self, seed: Optional[int] = None) -> Dict:
        """
        Generate random variation parameters.

        Args:
            seed: Random seed for reproducible variations

        Returns:
            Dictionary of variation parameters
        """
        if seed is not None:
            random.seed(seed)

        params = {
            # Brightness: -0.03 to +0.03
            'brightness': random.uniform(-0.03, 0.03),

            # Saturation: 0.97 to 1.03
            'saturation': random.uniform(0.97, 1.03),

            # Contrast: 0.98 to 1.02
            'contrast': random.uniform(0.98, 1.02),

            # Crop: 1-3 pixels from edges
            'crop_top': random.randint(1, 3),
            'crop_bottom': random.randint(1, 3),
            'crop_left': random.randint(1, 3),
            'crop_right': random.randint(1, 3),

            # Bitrate variation: ±3%
            'bitrate_factor': random.uniform(0.97, 1.03),

            # Noise strength: very subtle
            'noise_strength': random.randint(1, 3),

            # Speed: 0.99x to 1.01x
            'speed': random.uniform(0.99, 1.01),

            # Starting frame offset: 0-3 frames
            'frame_offset': random.randint(0, 3),
        }

        logger.debug(f"Generated variation params: {params}")
        return params

    def _build_filter_complex(self, params: Dict, width: int, height: int) -> str:
        """
        Build FFmpeg filter complex string.

        Args:
            params: Variation parameters
            width: Video width
            height: Video height

        Returns:
            Filter complex string
        """
        # Calculate crop dimensions
        crop_w = width - params['crop_left'] - params['crop_right']
        crop_h = height - params['crop_top'] - params['crop_bottom']

        # Build filter chain
        filters = []

        # 1. Crop
        filters.append(
            f"crop={crop_w}:{crop_h}:{params['crop_left']}:{params['crop_top']}"
        )

        # 2. Scale back to original size (subtle quality change)
        filters.append(f"scale={width}:{height}")

        # 3. Color adjustments (eq filter)
        filters.append(
            f"eq=brightness={params['brightness']}:"
            f"saturation={params['saturation']}:"
            f"contrast={params['contrast']}"
        )

        # 4. Add noise
        filters.append(f"noise=alls={params['noise_strength']}:allf=t")

        # 5. Speed adjustment
        filters.append(f"setpts=PTS/{params['speed']}")

        filter_complex = ','.join(filters)
        logger.debug(f"Filter complex: {filter_complex}")
        return filter_complex

    async def get_video_info(self, path: str) -> Dict:
        """
        Get video information using ffprobe.

        Args:
            path: Path to video file

        Returns:
            Dictionary with video information (duration, resolution, codec, bitrate)

        Raises:
            VideoProcessorError: If unable to get video info
        """
        if not os.path.exists(path):
            raise VideoProcessorError(f"Video file not found: {path}")

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            path
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                raise VideoProcessorError(f"ffprobe failed: {error_msg}")

            data = json.loads(stdout.decode('utf-8'))

            # Extract video stream info
            video_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'video'),
                None
            )

            if not video_stream:
                raise VideoProcessorError("No video stream found in file")

            # Extract format info
            format_info = data.get('format', {})

            info = {
                'duration': float(format_info.get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'codec': video_stream.get('codec_name', 'unknown'),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'format': format_info.get('format_name', 'unknown'),
            }

            logger.info(f"Video info for {path}: {info}")
            return info

        except json.JSONDecodeError as e:
            raise VideoProcessorError(f"Failed to parse ffprobe output: {str(e)}") from e
        except Exception as e:
            raise VideoProcessorError(f"Failed to get video info: {str(e)}") from e

    async def process_video(
        self,
        input_path: str,
        output_path: str,
        variation_seed: Optional[int] = None
    ) -> Dict:
        """
        Process video with all transformations to create a unique variation.

        Args:
            input_path: Path to input video
            output_path: Path to output video
            variation_seed: Optional seed for reproducible variations

        Returns:
            Dictionary with processing info (params used, output info, etc.)

        Raises:
            VideoProcessorError: If processing fails
        """
        logger.info(f"Processing video: {input_path} -> {output_path}")

        # Ensure input exists
        if not os.path.exists(input_path):
            raise VideoProcessorError(f"Input video not found: {input_path}")

        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Get video info
        video_info = await self.get_video_info(input_path)

        # Generate variation parameters
        params = self._generate_variation_params(variation_seed)

        # Build filter complex
        filter_complex = self._build_filter_complex(
            params,
            video_info['width'],
            video_info['height']
        )

        # Calculate target bitrate with variation
        base_bitrate = video_info['bitrate']
        target_bitrate = int(base_bitrate * params['bitrate_factor'])

        # Calculate frame offset in seconds
        frame_offset_seconds = params['frame_offset'] / video_info['fps'] if video_info['fps'] > 0 else 0

        # Build FFmpeg arguments
        args = [
            "-i", input_path,
            "-ss", str(frame_offset_seconds),  # Start offset
            "-vf", filter_complex,  # Video filters
            "-af", f"atempo={params['speed']}",  # Audio speed (with pitch correction)
            "-c:v", self.video_codec,  # Video codec
            "-preset", self.preset,  # Encoding preset
            "-crf", str(self.crf),  # Quality
            "-b:v", str(target_bitrate),  # Target bitrate
            "-c:a", self.audio_codec,  # Audio codec
            "-b:a", "128k",  # Audio bitrate
            "-map_metadata", "-1",  # Strip metadata
            "-movflags", "+faststart",  # Enable streaming
            output_path
        ]

        # Run FFmpeg
        await self._run_ffmpeg(args, "video processing")

        # Get output info
        output_info = await self.get_video_info(output_path)

        result = {
            'input_path': input_path,
            'output_path': output_path,
            'variation_params': params,
            'input_info': video_info,
            'output_info': output_info,
        }

        logger.info(f"Video processing completed: {output_path}")
        return result

    async def strip_metadata(self, input_path: str, output_path: str) -> None:
        """
        Strip all EXIF/metadata from video.

        Args:
            input_path: Path to input video
            output_path: Path to output video

        Raises:
            VideoProcessorError: If stripping fails
        """
        logger.info(f"Stripping metadata: {input_path} -> {output_path}")

        if not os.path.exists(input_path):
            raise VideoProcessorError(f"Input video not found: {input_path}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        args = [
            "-i", input_path,
            "-map_metadata", "-1",  # Remove all metadata
            "-c:v", "copy",  # Copy video without re-encoding
            "-c:a", "copy",  # Copy audio without re-encoding
            output_path
        ]

        await self._run_ffmpeg(args, "metadata stripping")
        logger.info(f"Metadata stripped: {output_path}")

    @staticmethod
    def generate_unique_filename(extension: str = "mp4") -> str:
        """
        Generate UUID-based unique filename.

        Args:
            extension: File extension (default: mp4)

        Returns:
            Unique filename with extension
        """
        unique_id = uuid.uuid4()
        filename = f"{unique_id}.{extension.lstrip('.')}"
        logger.debug(f"Generated unique filename: {filename}")
        return filename

    async def batch_process(
        self,
        input_path: str,
        count: int,
        output_dir: str
    ) -> List[Dict]:
        """
        Create multiple unique variations of a video.

        Args:
            input_path: Path to input video
            count: Number of variations to create
            output_dir: Directory to save variations

        Returns:
            List of processing results for each variation

        Raises:
            VideoProcessorError: If batch processing fails
        """
        logger.info(f"Batch processing: {count} variations of {input_path}")

        if not os.path.exists(input_path):
            raise VideoProcessorError(f"Input video not found: {input_path}")

        os.makedirs(output_dir, exist_ok=True)

        results = []

        for i in range(count):
            try:
                # Generate unique filename
                output_filename = self.generate_unique_filename(self.output_format)
                output_path = os.path.join(output_dir, output_filename)

                # Process with different seed for each variation
                result = await self.process_video(
                    input_path,
                    output_path,
                    variation_seed=i
                )

                results.append({
                    'index': i,
                    'success': True,
                    'result': result
                })

                logger.info(f"Batch progress: {i+1}/{count} completed")

            except Exception as e:
                logger.error(f"Failed to process variation {i}: {str(e)}")
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })

        successful = sum(1 for r in results if r['success'])
        logger.info(f"Batch processing completed: {successful}/{count} successful")

        return results

    async def verify_unique_hashes(self, file_paths: List[str]) -> Dict:
        """
        Verify that all processed videos have unique file hashes.

        Args:
            file_paths: List of video file paths to check

        Returns:
            Dictionary with hash analysis results
        """
        import hashlib

        logger.info(f"Verifying unique hashes for {len(file_paths)} files")

        hashes = {}
        duplicates = []

        for path in file_paths:
            if not os.path.exists(path):
                logger.warning(f"File not found for hash check: {path}")
                continue

            # Calculate MD5 hash
            md5_hash = hashlib.md5()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)

            file_hash = md5_hash.hexdigest()

            if file_hash in hashes:
                duplicates.append({
                    'hash': file_hash,
                    'files': [hashes[file_hash], path]
                })
            else:
                hashes[file_hash] = path

        result = {
            'total_files': len(file_paths),
            'unique_hashes': len(hashes),
            'duplicates': duplicates,
            'all_unique': len(duplicates) == 0
        }

        logger.info(f"Hash verification: {result['unique_hashes']} unique out of {result['total_files']} files")

        return result

    # Synchronous wrapper methods for Celery tasks

    def create_unique_copy(self, input_path: str, job_id: Optional[int] = None) -> str:
        """
        Synchronous wrapper to create a unique copy of a video.

        Args:
            input_path: Path to the source video
            job_id: Optional job ID for naming

        Returns:
            Path to the created unique video file
        """
        import asyncio

        # Generate output path
        output_dir = os.path.join(os.path.dirname(input_path), "temp")
        os.makedirs(output_dir, exist_ok=True)

        if job_id:
            output_filename = f"job_{job_id}_{uuid.uuid4()}.{self.output_format}"
        else:
            output_filename = self.generate_unique_filename(self.output_format)

        output_path = os.path.join(output_dir, output_filename)

        # Run async process in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self.process_video(input_path, output_path, variation_seed=job_id)
            )
        finally:
            loop.close()

        return output_path

    def create_variation(self, video_path: str, variation_number: int = 1) -> str:
        """
        Synchronous wrapper to create a variation of a video.

        Args:
            video_path: Path to the source video
            variation_number: Variation number (used as seed)

        Returns:
            Path to the created variation file
        """
        import asyncio

        # Generate output path
        output_dir = os.path.join(os.path.dirname(video_path), "variations")
        os.makedirs(output_dir, exist_ok=True)

        output_filename = f"variation_{variation_number}_{uuid.uuid4()}.{self.output_format}"
        output_path = os.path.join(output_dir, output_filename)

        # Run async process in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self.process_video(video_path, output_path, variation_seed=variation_number)
            )
        finally:
            loop.close()

        return output_path
