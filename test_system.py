"""
Test script to verify all components of the Reel Extraction System
"""
import sys
from pathlib import Path
from typing import Dict, Any


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def test_imports() -> bool:
    """Test if all required modules can be imported"""
    print_header("Testing Imports")
    
    success = True
    
    # Test standard library imports
    try:
        import json
        import subprocess
        print_success("Standard library imports")
    except ImportError as e:
        print_error(f"Standard library imports: {e}")
        success = False
    
    # Test third-party imports
    try:
        import pydantic
        print_success(f"Pydantic {pydantic.__version__}")
    except ImportError as e:
        print_error(f"Pydantic: {e}")
        success = False
    
    try:
        import google.generativeai as genai
        print_success("Google Generative AI")
    except ImportError as e:
        print_error(f"Google Generative AI: {e}")
        success = False
    
    try:
        import httpx
        print_success(f"httpx {httpx.__version__}")
    except ImportError as e:
        print_error(f"httpx: {e}")
        success = False
    
    try:
        import ffmpeg
        print_success("ffmpeg-python")
    except ImportError as e:
        print_error(f"ffmpeg-python: {e}")
        success = False
    
    try:
        import cv2
        print_success(f"OpenCV {cv2.__version__}")
    except ImportError as e:
        print_error(f"OpenCV: {e}")
        success = False
    
    try:
        import whisper
        print_success("OpenAI Whisper")
    except ImportError as e:
        print_warning(f"OpenAI Whisper: {e} (optional)")
    
    try:
        from dotenv import load_dotenv
        print_success("python-dotenv")
    except ImportError as e:
        print_error(f"python-dotenv: {e}")
        success = False
    
    # Test our modules
    try:
        from src.models import BaseExtraction, WorkoutRoutine
        print_success("Data models")
    except ImportError as e:
        print_error(f"Data models: {e}")
        success = False
    
    try:
        from src.utils.config import Config
        print_success("Configuration utilities")
    except ImportError as e:
        print_error(f"Configuration utilities: {e}")
        success = False
    
    try:
        from src.services.video_downloader import VideoDownloader
        print_success("Video downloader service")
    except ImportError as e:
        print_error(f"Video downloader service: {e}")
        success = False
    
    try:
        from src.services.video_segmenter import VideoSegmenter
        print_success("Video segmenter service")
    except ImportError as e:
        print_error(f"Video segmenter service: {e}")
        success = False
    
    try:
        from src.services.gemini_analyzer import GeminiAnalyzer
        print_success("Gemini analyzer service")
    except ImportError as e:
        print_error(f"Gemini analyzer service: {e}")
        success = False
    
    try:
        from src.services.supermemeory_client import SupermemeoryClient
        print_success("Supermemeory client service")
    except ImportError as e:
        print_error(f"Supermemeory client service: {e}")
        success = False
    
    return success


def test_configuration() -> bool:
    """Test configuration loading"""
    print_header("Testing Configuration")
    
    try:
        from src.utils.config import Config
        
        # Check if API keys are set
        if Config.GEMINI_API_KEY:
            print_success(f"GEMINI_API_KEY is set ({len(Config.GEMINI_API_KEY)} chars)")
        else:
            print_warning("GEMINI_API_KEY is not set in .env file")
        
        if Config.SUPERMEMEORY_API_KEY:
            print_success(f"SUPERMEMEORY_API_KEY is set ({len(Config.SUPERMEMEORY_API_KEY)} chars)")
        else:
            print_warning("SUPERMEMEORY_API_KEY is not set in .env file")
        
        print_success(f"TEMP_STORAGE_PATH: {Config.TEMP_STORAGE_PATH}")
        print_success(f"MAX_VIDEO_SIZE_MB: {Config.MAX_VIDEO_SIZE_MB}")
        print_success(f"KEYFRAME_INTERVAL_SECONDS: {Config.KEYFRAME_INTERVAL_SECONDS}")
        
        # Check if at least one API key is set
        if not Config.GEMINI_API_KEY and not Config.SUPERMEMEORY_API_KEY:
            print_error("No API keys found. Please set at least GEMINI_API_KEY in .env file")
            return False
        
        return True
            
    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        return False


def test_ffmpeg() -> bool:
    """Test FFmpeg installation"""
    print_header("Testing FFmpeg")
    
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print_success(f"FFmpeg is installed: {version_line}")
            return True
        else:
            print_error("FFmpeg command failed")
            return False
            
    except FileNotFoundError:
        print_error("FFmpeg not found. Install with: brew install ffmpeg")
        return False
    except Exception as e:
        print_error(f"FFmpeg test failed: {e}")
        return False


def test_data_models() -> bool:
    """Test data models"""
    print_header("Testing Data Models")
    
    try:
        from src.models import (
            BaseExtraction,
            WorkoutRoutine,
            Exercise,
            RecipeCard,
            Ingredient,
            RecipeStep
        )
        from datetime import datetime
        
        # Test WorkoutRoutine model
        exercise = Exercise(
            name="Squats",
            sets=3,
            reps=15,
            duration_seconds=30,
            rest_seconds=15
        )
        print_success("Exercise model created")
        
        workout = WorkoutRoutine(
            category="workout",
            title="Test Workout",
            description="A test workout routine",
            exercises=[exercise],
            estimated_duration_minutes=20.0,
            difficulty_level="intermediate"
        )
        print_success("WorkoutRoutine model created")
        
        # Test RecipeCard model
        ingredient = Ingredient(
            name="Flour",
            quantity="2 cups"
        )
        print_success("Ingredient model created")
        
        recipe_step = RecipeStep(
            step_number=1,
            instruction="Mix ingredients",
            duration_minutes=2.0
        )
        print_success("RecipeStep model created")
        
        recipe = RecipeCard(
            category="recipe",
            title="Test Recipe",
            description="A test recipe",
            ingredients=[ingredient],
            steps=[recipe_step]
        )
        print_success("RecipeCard model created")
        
        # Test model serialization
        workout_dict = workout.model_dump()
        print_success("Model serialization works")
        
        return True
        
    except Exception as e:
        print_error(f"Data models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_services() -> bool:
    """Test service initialization"""
    print_header("Testing Service Initialization")
    
    success = True
    
    try:
        from src.services.video_downloader import VideoDownloader
        downloader = VideoDownloader()
        print_success("VideoDownloader initialized")
    except Exception as e:
        print_error(f"VideoDownloader initialization failed: {e}")
        success = False
    
    try:
        from src.services.video_segmenter import VideoSegmenter
        segmenter = VideoSegmenter()
        print_success("VideoSegmenter initialized")
    except Exception as e:
        print_error(f"VideoSegmenter initialization failed: {e}")
        success = False
    
    try:
        from src.utils.config import Config
        if Config.GEMINI_API_KEY:
            from src.services.gemini_analyzer import GeminiAnalyzer
            analyzer = GeminiAnalyzer()
            print_success("GeminiAnalyzer initialized")
        else:
            print_warning("GeminiAnalyzer skipped (GEMINI_API_KEY not set)")
    except Exception as e:
        print_error(f"GeminiAnalyzer initialization failed: {e}")
        print_info("Make sure GEMINI_API_KEY is set in .env file")
        success = False
    
    try:
        from src.utils.config import Config
        if Config.SUPERMEMEORY_API_KEY:
            from src.services.supermemeory_client import SupermemeoryClient
            client = SupermemeoryClient()
            print_success("SupermemeoryClient initialized")
        else:
            print_warning("SupermemeoryClient skipped (SUPERMEMEORY_API_KEY not set)")
    except Exception as e:
        print_error(f"SupermemeoryClient initialization failed: {e}")
        print_info("Make sure SUPERMEMEORY_API_KEY is set in .env file")
        success = False
    
    return success


def test_file_utilities() -> bool:
    """Test file utilities"""
    print_header("Testing File Utilities")
    
    try:
        from src.utils.file_utils import (
            generate_unique_filename,
            get_temp_file_path,
            validate_video_file
        )
        from src.utils.config import Config
        
        # Test filename generation
        filename = generate_unique_filename("test.mp4")
        print_success(f"Generated unique filename: {filename}")
        
        # Test temp file path
        temp_path = get_temp_file_path(filename)
        print_success(f"Temp file path: {temp_path}")
        
        # Test temp storage directory
        Config.ensure_temp_storage()
        if Config.TEMP_STORAGE_PATH.exists():
            print_success(f"Temp storage directory exists: {Config.TEMP_STORAGE_PATH}")
        else:
            print_warning(f"Temp storage directory does not exist: {Config.TEMP_STORAGE_PATH}")
        
        return True
        
    except Exception as e:
        print_error(f"File utilities test failed: {e}")
        return False


def test_gemini_connection() -> bool:
    """Test Gemini API connection"""
    print_header("Testing Gemini API Connection")
    
    try:
        from src.utils.config import Config
        import google.generativeai as genai
        
        if not Config.GEMINI_API_KEY:
            print_warning("GEMINI_API_KEY not set - skipping test")
            return False
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Try different model names (use full model path format)
        model_names = [
            'models/gemini-2.5-pro',
            'models/gemini-2.5-flash',
            'models/gemini-2.0-flash-001',
            'models/gemini-2.0-flash'
        ]
        model = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                print_info(f"Trying model: {model_name}...")
                # Simple test request
                response = model.generate_content("Say 'Hello' in one word.")
                
                if response and response.text:
                    print_success(f"Gemini API connection successful with {model_name}: {response.text.strip()}")
                    return True
            except Exception as e:
                print_info(f"Model {model_name} failed: {str(e)[:100]}")
                continue
        
        if model is None:
            print_error("Could not connect to any Gemini model")
            return False
        else:
            print_error("Gemini API returned empty response")
            return False
            
    except Exception as e:
        print_error(f"Gemini API connection failed: {e}")
        print_info("Check your GEMINI_API_KEY in .env file")
        return False


def test_supermemeory_connection() -> bool:
    """Test supermemeory.ai API connection"""
    print_header("Testing Supermemeory.ai API Connection")
    
    try:
        from src.services.supermemeory_client import SupermemeoryClient
        from src.utils.config import Config
        
        if not Config.SUPERMEMEORY_API_KEY:
            print_warning("SUPERMEMEORY_API_KEY not set - skipping test")
            return False
        
        client = SupermemeoryClient()
        
        # Test search endpoint (read-only, safer for testing)
        print_info("Testing supermemeory.ai API with search...")
        result, error = client.search_memories("test", limit=1)
        
        if error:
            print_warning(f"Supermemeory.ai API test: {error}")
            print_info("This might be expected if the API endpoint is different")
            print_info("The client is initialized correctly, but API endpoint may need adjustment")
            return False
        else:
            print_success("Supermemeory.ai API connection successful")
            return True
            
    except Exception as e:
        print_error(f"Supermemeory.ai API connection failed: {e}")
        print_info("Check your SUPERMEMEORY_API_KEY and API endpoint in .env file")
        return False


def test_video_processing() -> bool:
    """Test video processing capabilities"""
    print_header("Testing Video Processing")
    
    try:
        from src.services.video_segmenter import VideoSegmenter
        import subprocess
        
        # Check FFmpeg
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True
            )
            print_success("FFmpeg is available for video processing")
        except:
            print_error("FFmpeg not available")
            return False
        
        # Test segmenter initialization
        segmenter = VideoSegmenter()
        print_success("VideoSegmenter can be initialized")
        
        print_info("Video processing ready (requires actual video file to test fully)")
        return True
        
    except Exception as e:
        print_error(f"Video processing test failed: {e}")
        return False


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Reel Extraction System - Test Suite".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print(Colors.RESET)
    
    results = {}
    
    # Run all tests
    results["Imports"] = test_imports()
    results["Configuration"] = test_configuration()
    results["FFmpeg"] = test_ffmpeg()
    results["Data Models"] = test_data_models()
    results["File Utilities"] = test_file_utilities()
    results["Services"] = test_services()
    results["Gemini API"] = test_gemini_connection()
    results["Supermemeory API"] = test_supermemeory_connection()
    results["Video Processing"] = test_video_processing()
    
    # Print summary
    print_header("Test Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if failed > 0:
        print(f"{Colors.YELLOW}⚠ {failed} test(s) failed. Check the errors above.{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}✓ All tests passed! System is ready to use.{Colors.RESET}")
    
    print(f"\n{Colors.BLUE}Next steps:{Colors.RESET}")
    print("1. Ensure your .env file has GEMINI_API_KEY and SUPERMEMEORY_API_KEY")
    print("2. Test with a video file: python main.py path/to/video.mp4")
    print("3. Check the README.md for usage examples")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

