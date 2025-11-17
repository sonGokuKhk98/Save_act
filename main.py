"""
Main orchestration script for Reel Data Extraction
"""
import sys
from pathlib import Path
from typing import Optional, Callable
from src.services.video_downloader import VideoDownloader
from src.services.video_segmenter import VideoSegmenter
from src.services.gemini_analyzer import GeminiAnalyzer
from src.services.supermemeory_client import SupermemeoryClient
from src.utils.config import Config
from src.utils.file_utils import cleanup_temp_file


class ReelExtractor:
    """
    Main orchestrator for the reel extraction pipeline.
    
    Coordinates all services to extract structured data from video reels.
    """
    
    def __init__(self):
        """Initialize all services"""
        Config.validate()
        Config.ensure_temp_storage()
        
        self.downloader = VideoDownloader()
        self.segmenter = VideoSegmenter()
        self.analyzer = GeminiAnalyzer()
        self.storage = SupermemeoryClient()
    
    def extract(
        self,
        input_source: str,
        source_type: str = "file",
        preferred_category: Optional[str] = None,
        extract_keyframes: bool = True,
        extract_audio: bool = True,
        transcribe: bool = True,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> dict:
        """
        Extract structured data from a video reel.
        
        Args:
            input_source: File path or URL
            source_type: "file" or "url"
            preferred_category: Preferred category (optional, will auto-detect)
            extract_keyframes: Whether to extract keyframes
            extract_audio: Whether to extract audio
            transcribe: Whether to transcribe audio
        
        Returns:
            Dictionary with extraction results
        """
        def notify(stage: str, progress: int) -> None:
            """Notify external callers (e.g., API) about stage/progress."""
            if progress_callback is None:
                return
            try:
                progress_callback(stage, progress)
            except Exception:
                # Never let callback errors break the core pipeline
                pass
        result = {
            "success": False,
            "extraction": None,
            "stored": False,
            "errors": [],
            "temp_files": [],
            "thumbnail_path": None,
        }
        
        try:
            # Step 1: Download/Process video
            notify("downloading", 10)
            print("📥 Step 1: Processing video...")
            video_path, error = self.downloader.process(input_source, source_type)
            if error:
                result["errors"].append(f"Download error: {error}")
                notify("error", 100)
                return result
            
            result["temp_files"].append(video_path)
            print(f"✓ Video processed: {video_path}")
            notify("downloading", 30)
            
            # Step 2: Segment video (keyframes, audio)
            notify("segmenting", 40)
            print("✂️  Step 2: Segmenting video...")
            segmentation = self.segmenter.segment_video(
                video_path,
                extract_keyframes=extract_keyframes,
                extract_audio=extract_audio,
                transcribe=transcribe
            )
            
            if segmentation["errors"]:
                result["errors"].extend(segmentation["errors"])
            
            # Add temp files to cleanup list
            if segmentation["audio_path"]:
                result["temp_files"].append(segmentation["audio_path"])
            result["temp_files"].extend(segmentation["keyframes"])

            # Keep track of the first keyframe so we can expose a thumbnail
            # URL for downstream features like Google Lens / product search.
            if segmentation["keyframes"]:
                # Store as string path; API layer will convert to a URL.
                result["thumbnail_path"] = str(segmentation["keyframes"][0])
            
            print(f"✓ Extracted {len(segmentation['keyframes'])} keyframes")
            if segmentation.get("transcript"):
                print(f"✓ Audio transcribed: {len(segmentation['transcript']['text'])} characters")
            else:
                print("ℹ️  No audio transcript available (continuing without it)")
            notify("segmenting", 60)
            
            # Step 3: Analyze with Gemini
            notify("analyzing", 70)
            print("🤖 Step 3: Analyzing with Gemini AI...")
            transcript_text = None
            if segmentation.get("transcript") and segmentation["transcript"].get("text"):
                transcript_text = segmentation["transcript"]["text"]
            
            extraction, error,keyframes = self.analyzer.analyze_video(
                video_path,
                keyframes=segmentation["keyframes"] if extract_keyframes else None,
                transcript=transcript_text,
                preferred_category=preferred_category
            )
            extraction.keyframes = keyframes
            if error:
                result["errors"].append(f"Analysis error: {error}")
                notify("error", 100)
                return result
            
            result["extraction"] = extraction
            print(f"✓ Category detected: {extraction.category}")
            print(f"✓ Title: {extraction.title}")
            notify("analyzing", 85)
            
            # Step 4: Store in supermemeory.ai
            notify("storing", 90)
            print("💾 Step 4: Storing in supermemeory.ai...")
            storage_result, storage_error = self.storage.store_extraction(
                extraction,
                source_url=input_source if source_type == "url" else None
            )
            
            if storage_error:
                result["errors"].append(f"Storage error: {storage_error}")
            else:
                result["stored"] = True
                print("✓ Data stored successfully in supermemeory.ai")
            
            result["success"] = True
            notify("done", 100)
            return result
            
        except Exception as e:
            result["errors"].append(f"Unexpected error: {str(e)}")
            notify("error", 100)
            return result
        
        finally:
            # Cleanup temp files (optional - you might want to keep them for debugging)
            # Uncomment the following lines to auto-cleanup:
            # for temp_file in result["temp_files"]:
            #     if temp_file and Path(temp_file).exists():
            #         cleanup_temp_file(Path(temp_file))
            pass


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract structured data from video reels using Gemini AI"
    )
    parser.add_argument(
        "input",
        help="Path to video file or URL"
    )
    parser.add_argument(
        "--type",
        choices=["file", "url"],
        default="file",
        help="Input type: file or url"
    )
    parser.add_argument(
        "--category",
        choices=["workout", "recipe", "travel", "product", "educational", "music"],
        default=None,
        help="Preferred category (auto-detected if not specified)"
    )
    parser.add_argument(
        "--no-keyframes",
        action="store_true",
        help="Skip keyframe extraction"
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Skip audio extraction"
    )
    parser.add_argument(
        "--no-transcribe",
        action="store_true",
        help="Skip audio transcription"
    )
    
    args = parser.parse_args()
    
    # Create extractor
    extractor = ReelExtractor()
    
    # Extract
    result = extractor.extract(
        input_source=args.input,
        source_type=args.type,
        preferred_category=args.category,
        extract_keyframes=not args.no_keyframes,
        extract_audio=not args.no_audio,
        transcribe=not args.no_transcribe
    )
    
    # Print results
    if result["success"]:
        print("\n✅ Extraction successful!")
        print(f"Category: {result['extraction'].category}")
        print(f"Title: {result['extraction'].title}")
        print(f"Stored in supermemeory.ai: {result['stored']}")
        
        if result["errors"]:
            print("\n⚠️  Warnings:")
            for error in result["errors"]:
                print(f"  - {error}")
    else:
        print("\n❌ Extraction failed!")
        for error in result["errors"]:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

