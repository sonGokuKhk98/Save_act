"""
Video segmentation service for keyframe and audio extraction
"""
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from src.utils.config import Config
from src.utils.file_utils import get_temp_file_path, generate_unique_filename


class VideoSegmenter:
    """
    Service to segment videos into keyframes and extract audio.
    
    Uses FFmpeg for video processing.
    """
    
    def __init__(self):
        """Initialize the video segmenter"""
        Config.ensure_temp_storage()
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is installed.
        
        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: FFmpeg not found. Video segmentation will not work.")
            print("Install FFmpeg: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
            return False
    
    def extract_keyframes(
        self, 
        video_path: Path, 
        interval_seconds: Optional[int] = None
    ) -> Tuple[List[Path], Optional[str]]:
        """
        Extract keyframes from video at specified intervals.
        
        Args:
            video_path: Path to video file
            interval_seconds: Seconds between keyframes (default from config)
        
        Returns:
            Tuple of (list of keyframe paths, error_message)
        """
        if interval_seconds is None:
            interval_seconds = Config.KEYFRAME_INTERVAL_SECONDS
        
        # Generate output pattern for keyframes
        keyframe_dir = get_temp_file_path(f"keyframes_{video_path.stem}")
        keyframe_dir.mkdir(parents=True, exist_ok=True)
        output_pattern = str(keyframe_dir / "keyframe_%04d.jpg")
        
        try:
            # Extract keyframes using FFmpeg
            # fps=1/interval means 1 frame every 'interval' seconds
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vf", f"fps=1/{interval_seconds}",
                "-q:v", "2",  # High quality
                output_pattern,
                "-y"  # Overwrite output files
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get all extracted keyframe files
            keyframe_files = sorted(keyframe_dir.glob("keyframe_*.jpg"))
            return keyframe_files, None
            
        except subprocess.CalledProcessError as e:
            return [], f"FFmpeg error: {e.stderr}"
        except Exception as e:
            return [], f"Error extracting keyframes: {str(e)}"
    
    def extract_audio(self, video_path: Path) -> Tuple[Optional[Path], Optional[str]]:
        """
        Extract audio track from video.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Tuple of (audio file path, error_message)
        """
        audio_filename = generate_unique_filename(video_path.name, ".aac")
        audio_path = get_temp_file_path(audio_filename)
        
        try:
            # Extract audio using FFmpeg
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",  # No video
                "-acodec", "copy",  # Copy audio codec
                str(audio_path),
                "-y"  # Overwrite output file
            ]
            
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return audio_path, None
            
        except subprocess.CalledProcessError as e:
            return None, f"FFmpeg error: {e.stderr}"
        except Exception as e:
            return None, f"Error extracting audio: {str(e)}"
    
    def transcribe_audio(
        self, 
        audio_path: Path
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Transcribe audio to text using Whisper.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Tuple of (transcript dict, error_message)
        """
        try:
            import whisper
            
            # Load Whisper model (base model for speed)
            # This might take a moment on first run
            print("🎤 Loading Whisper model for transcription...")
            model = whisper.load_model("base")
            
            # Transcribe audio
            print("🎤 Transcribing audio...")
            result = model.transcribe(str(audio_path))
            
            return {
                "text": result["text"],
                "segments": result.get("segments", []),
                "language": result.get("language", "unknown")
            }, None
            
        except ImportError:
            return None, "Whisper not installed. Install with: pip install openai-whisper"
        except Exception as e:
            error_msg = str(e)
            # Check if it's a NumPy compatibility issue
            if "numpy" in error_msg.lower() or "_ARRAY_API" in error_msg:
                return None, "Whisper transcription failed due to NumPy compatibility. Continuing without transcript. (This is optional)"
            return None, f"Error transcribing audio: {error_msg}"
    
    def segment_video(
        self, 
        video_path: Path,
        extract_keyframes: bool = True,
        extract_audio: bool = True,
        transcribe: bool = True
    ) -> Dict[str, Any]:
        """
        Segment video into keyframes and audio.
        
        Args:
            video_path: Path to video file
            extract_keyframes: Whether to extract keyframes
            extract_audio: Whether to extract audio
            transcribe: Whether to transcribe audio
        
        Returns:
            Dictionary with keyframes, audio, and transcript
        """
        result = {
            "keyframes": [],
            "audio_path": None,
            "transcript": None,
            "errors": []
        }
        
        # Extract keyframes
        if extract_keyframes:
            keyframes, error = self.extract_keyframes(video_path)
            if error:
                result["errors"].append(f"Keyframe extraction: {error}")
            else:
                result["keyframes"] = keyframes
        
        # Extract audio
        if extract_audio:
            audio_path, error = self.extract_audio(video_path)
            if error:
                result["errors"].append(f"Audio extraction: {error}")
            else:
                result["audio_path"] = audio_path
                
                # Transcribe audio (only if requested and if whisper is available)
                if transcribe and audio_path:
                    try:
                        # Try to import whisper - if it fails, skip transcription
                        import whisper
                        transcript, transcribe_error = self.transcribe_audio(audio_path)
                        if transcribe_error:
                            # Transcription is optional, so we log it but don't fail
                            result["errors"].append(f"Transcription: {transcribe_error}")
                            print(f"⚠️  {transcribe_error}")
                            print("ℹ️  Continuing without audio transcript...")
                        else:
                            result["transcript"] = transcript
                            print("✓ Audio transcribed successfully")
                    except (ImportError, Exception) as e:
                        # Whisper not available or NumPy issue - skip transcription
                        result["errors"].append(f"Transcription skipped: {str(e)[:100]}")
                        print(f"⚠️  Audio transcription skipped (Whisper/NumPy issue)")
                        print("ℹ️  Continuing without audio transcript...")
        
        return result

