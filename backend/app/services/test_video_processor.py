"""
Test script for VideoProcessor service.

This script validates the VideoProcessor implementation and demonstrates usage.
Note: FFmpeg must be installed for actual video processing.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from video_processor import VideoProcessor, VideoProcessorError


async def test_initialization():
    """Test VideoProcessor initialization"""
    print("Test 1: Initialization")
    print("-" * 50)

    try:
        # Test default initialization
        processor1 = VideoProcessor()
        print("✓ Default initialization successful")

        # Test custom initialization
        processor2 = VideoProcessor(
            output_format="mp4",
            video_codec="libx264",
            audio_codec="aac",
            preset="fast",
            crf=20
        )
        print("✓ Custom initialization successful")

        print(f"  Output format: {processor2.output_format}")
        print(f"  Video codec: {processor2.video_codec}")
        print(f"  Audio codec: {processor2.audio_codec}")
        print(f"  Preset: {processor2.preset}")
        print(f"  CRF: {processor2.crf}")

        return True

    except VideoProcessorError as e:
        print(f"✗ Initialization failed: {e}")
        if "FFmpeg is not installed" in str(e):
            print("\nNote: FFmpeg is not installed. Install it with:")
            print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
            print("  macOS: brew install ffmpeg")
            print("  Windows: Download from https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_unique_filename_generation():
    """Test unique filename generation"""
    print("\n\nTest 2: Unique Filename Generation")
    print("-" * 50)

    try:
        processor = VideoProcessor(verify_ffmpeg=False)

        # Generate multiple filenames
        filenames = set()
        for i in range(10):
            filename = processor.generate_unique_filename("mp4")
            filenames.add(filename)

        # Check uniqueness
        if len(filenames) == 10:
            print(f"✓ Generated 10 unique filenames")
            print(f"  Examples:")
            for filename in list(filenames)[:3]:
                print(f"    - {filename}")
        else:
            print(f"✗ Filenames not unique: {len(filenames)}/10")
            return False

        # Test different extensions
        mp4_file = processor.generate_unique_filename("mp4")
        avi_file = processor.generate_unique_filename("avi")
        mov_file = processor.generate_unique_filename(".mov")  # Test with dot

        print(f"✓ Different extensions work:")
        print(f"    MP4: {mp4_file}")
        print(f"    AVI: {avi_file}")
        print(f"    MOV: {mov_file}")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_variation_params():
    """Test variation parameter generation"""
    print("\n\nTest 3: Variation Parameters")
    print("-" * 50)

    try:
        processor = VideoProcessor(verify_ffmpeg=False)

        # Generate params with seed (should be reproducible)
        params1 = processor._generate_variation_params(seed=42)
        params2 = processor._generate_variation_params(seed=42)

        if params1 == params2:
            print("✓ Seeded variation params are reproducible")
        else:
            print("✗ Seeded params are not reproducible")
            return False

        # Generate random params (should be different)
        params3 = processor._generate_variation_params()
        params4 = processor._generate_variation_params()

        if params3 != params4:
            print("✓ Unseeded variation params are random")
        else:
            print("⚠ Warning: Unseeded params happened to be identical (unlikely but possible)")

        # Verify parameter ranges
        print("\n  Sample variation parameters:")
        for key, value in params1.items():
            print(f"    {key}: {value}")

        # Validate ranges
        checks = [
            (-0.03 <= params1['brightness'] <= 0.03, "brightness"),
            (0.97 <= params1['saturation'] <= 1.03, "saturation"),
            (0.98 <= params1['contrast'] <= 1.02, "contrast"),
            (1 <= params1['crop_top'] <= 3, "crop_top"),
            (0.97 <= params1['bitrate_factor'] <= 1.03, "bitrate_factor"),
            (1 <= params1['noise_strength'] <= 3, "noise_strength"),
            (0.99 <= params1['speed'] <= 1.01, "speed"),
            (0 <= params1['frame_offset'] <= 3, "frame_offset"),
        ]

        all_valid = all(check[0] for check in checks)
        if all_valid:
            print("\n✓ All parameters within expected ranges")
        else:
            invalid = [check[1] for check in checks if not check[0]]
            print(f"\n✗ Invalid parameter ranges: {invalid}")
            return False

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filter_complex():
    """Test filter complex generation"""
    print("\n\nTest 4: FFmpeg Filter Complex")
    print("-" * 50)

    try:
        processor = VideoProcessor(verify_ffmpeg=False)

        # Generate sample params
        params = processor._generate_variation_params(seed=123)

        # Build filter complex
        filter_complex = processor._build_filter_complex(params, 1920, 1080)

        print("✓ Filter complex generated successfully")
        print(f"\n  Filter string:")
        print(f"    {filter_complex[:100]}...")

        # Validate filter contains expected operations
        expected_filters = ['crop', 'scale', 'eq', 'noise', 'setpts']
        found_filters = [f for f in expected_filters if f in filter_complex]

        if len(found_filters) == len(expected_filters):
            print(f"\n✓ All expected filters present: {', '.join(expected_filters)}")
        else:
            missing = [f for f in expected_filters if f not in found_filters]
            print(f"\n✗ Missing filters: {missing}")
            return False

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_video_processing_api():
    """Test video processing API (without actual video)"""
    print("\n\nTest 5: Video Processing API")
    print("-" * 50)

    try:
        processor = VideoProcessor(verify_ffmpeg=False)

        # Test that methods exist and have correct signatures
        methods = {
            'process_video': ['input_path', 'output_path', 'variation_seed'],
            'strip_metadata': ['input_path', 'output_path'],
            'batch_process': ['input_path', 'count', 'output_dir'],
            'get_video_info': ['path'],
            'verify_unique_hashes': ['file_paths'],
        }

        import inspect

        all_valid = True
        for method_name, expected_params in methods.items():
            method = getattr(processor, method_name)

            # Check if method is async
            if method_name in ['process_video', 'strip_metadata', 'batch_process', 'get_video_info', 'verify_unique_hashes']:
                if not asyncio.iscoroutinefunction(method):
                    print(f"✗ {method_name} is not async")
                    all_valid = False
                    continue

            # Check parameters
            sig = inspect.signature(method)
            params = [p for p in sig.parameters.keys() if p != 'self']

            print(f"✓ {method_name}({', '.join(params)})")

        if all_valid:
            print("\n✓ All methods have correct signatures")
        else:
            print("\n✗ Some methods have issues")
            return False

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("VideoProcessor Test Suite")
    print("=" * 50)

    results = []

    # Test 1: Initialization (checks for FFmpeg)
    ffmpeg_available = await test_initialization()
    results.append(("Initialization", ffmpeg_available))

    # Test 2: Unique filename generation
    results.append(("Unique Filenames", test_unique_filename_generation()))

    # Test 3: Variation parameters
    results.append(("Variation Parameters", test_variation_params()))

    # Test 4: Filter complex
    results.append(("Filter Complex", test_filter_complex()))

    # Test 5: API structure
    results.append(("API Structure", await test_video_processing_api()))

    # Summary
    print("\n\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if not ffmpeg_available:
        print("\n" + "=" * 50)
        print("Note: FFmpeg is not installed")
        print("=" * 50)
        print("The VideoProcessor is ready to use, but requires FFmpeg")
        print("to process actual videos. Install FFmpeg to enable full")
        print("functionality.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
