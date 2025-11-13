"""
Gemini multimodal analysis service
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, Literal, Tuple
import google.generativeai as genai
from src.utils.config import Config
from src.models import (
    WorkoutRoutine,
    RecipeCard,
    TravelItinerary,
    ProductCatalog,
    TutorialSummary,
    SongMetadata
)


class GeminiAnalyzer:
    """
    Service to analyze videos using Gemini multimodal AI.
    
    Handles category detection and structured data extraction.
    """
    
    def __init__(self):
        """Initialize the Gemini analyzer"""
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required in .env file")
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Try different model names in order of preference
        # Use the full model path format: models/gemini-2.5-flash
        # Flash is faster and cheaper, good for testing and production
        model_names = [
            'models/gemini-2.5-flash',  # Stable, faster, cheaper (preferred)
            'models/gemini-2.0-flash-001',  # Stable alternative
            'models/gemini-2.0-flash',  # Alternative
            'models/gemini-2.5-pro',  # Best quality (fallback if Flash unavailable)
        ]
        self.model = None
        
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                # Test if model works with a simple request
                self.model.generate_content("test")
                break
            except Exception:
                continue
        
        if self.model is None:
            raise ValueError(f"Could not initialize any Gemini model. Tried: {model_names}")
        
        # Store the model name for reference
        self.model_name = self.model._model_name if hasattr(self.model, '_model_name') else model_names[0]
        print(f"🤖 Using Gemini model: {self.model_name}")
    
    def detect_category(
        self, 
        video_path: Optional[Path] = None,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect the category of the video content.
        
        Args:
            video_path: Path to video file (optional)
            keyframes: List of keyframe image paths (optional)
            transcript: Audio transcript text (optional)
        
        Returns:
            Tuple of (category, error_message)
        """
        categories = ["workout", "recipe", "travel", "product", "educational", "music"]
        
        prompt = f"""
        Analyze this video content and determine its category.
        
        Categories: {', '.join(categories)}
        
        Return ONLY the category name (one word) from the list above.
        """
        
        try:
            # Build content for analysis
            content_parts = [prompt]
            
            # Add video if provided
            if video_path and video_path.exists():
                video_file = genai.upload_file(path=str(video_path))
                content_parts.append(video_file)
            
            # Add keyframes if provided
            if keyframes:
                for keyframe_path in keyframes[:5]:  # Limit to first 5 keyframes
                    if Path(keyframe_path).exists():
                        content_parts.append(genai.upload_file(path=str(keyframe_path)))
            
            # Add transcript if provided
            if transcript:
                content_parts.append(f"\nAudio Transcript:\n{transcript}")
            
            # Generate response
            response = self.model.generate_content(content_parts)
            category = response.text.strip().lower()
            
            # Validate category
            if category in categories:
                return category, None
            else:
                # Try to find category in response
                for cat in categories:
                    if cat in category:
                        return cat, None
                return None, f"Could not determine category. Response: {category}"
                
        except Exception as e:
            return None, f"Error detecting category: {str(e)}"
    
    def extract_workout_routine(
        self,
        video_path: Optional[Path] = None,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None
    ) -> Tuple[Optional[WorkoutRoutine], Optional[str]]:
        """
        Extract workout routine from video.
        
        Args:
            video_path: Path to video file
            keyframes: List of keyframe image paths
            transcript: Audio transcript text
        
        Returns:
            Tuple of (WorkoutRoutine object, error_message)
        """
        prompt = """
        Analyze this workout video and extract the complete workout routine.
        
        Extract:
        - Exercise names
        - Sets and reps (if mentioned)
        - Duration in seconds (for time-based exercises)
        - Rest periods between exercises
        - Total rounds/circuits
        - Estimated total duration
        - Difficulty level (beginner/intermediate/advanced)
        - Music tempo in BPM (if detectable)
        
        Return the data in JSON format matching this structure:
        {
            "title": "Workout title",
            "description": "Brief description",
            "exercises": [
                {
                    "name": "Exercise name",
                    "sets": 3,
                    "reps": 15,
                    "duration_seconds": 30,
                    "rest_seconds": 15
                }
            ],
            "total_rounds": 3,
            "estimated_duration_minutes": 20.0,
            "difficulty_level": "intermediate",
            "music_tempo_bpm": 140
        }
        """
        
        return self._extract_structured_data(
            prompt, 
            WorkoutRoutine, 
            video_path, 
            keyframes, 
            transcript
        )
    
    def extract_recipe(
        self,
        video_path: Optional[Path] = None,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None
    ) -> Tuple[Optional[RecipeCard], Optional[str]]:
        """Extract recipe from cooking video"""
        prompt = """
        Analyze this cooking video and extract the complete recipe.
        
        Extract:
        - All ingredients with quantities (e.g., "2 cups flour", "1 tbsp butter")
        - Step-by-step cooking instructions
        - Duration for each step (if mentioned)
        - Utensils/tools needed for each step
        - Prep time, cook time, servings
        - Cuisine type
        
        Return the data in JSON format.
        """
        
        return self._extract_structured_data(
            prompt, 
            RecipeCard, 
            video_path, 
            keyframes, 
            transcript
        )
    
    def extract_travel_itinerary(
        self,
        video_path: Optional[Path] = None,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None
    ) -> Tuple[Optional[TravelItinerary], Optional[str]]:
        """Extract travel itinerary from travel video"""
        prompt = """
        Analyze this travel video and extract the complete itinerary.
        
        Extract:
        - Destination location
        - All activities and places to visit
        - Locations/addresses
        - Google Maps links (if possible to generate)
        - Booking links (if visible)
        - Estimated duration for each activity
        - Day-by-day breakdown (if applicable)
        - Estimated budget
        
        Return the data in JSON format.
        """
        
        return self._extract_structured_data(
            prompt, 
            TravelItinerary, 
            video_path, 
            keyframes, 
            transcript
        )
    
    def extract_product_catalog(
        self,
        video_path: Optional[Path] = None,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None
    ) -> Tuple[Optional[ProductCatalog], Optional[str]]:
        """Extract product catalog from product video"""
        prompt = """
        Analyze this product video and extract all products shown.
        
        Extract:
        - Product names
        - Brand names
        - Prices (as displayed)
        - Currency
        - Purchase links (if visible in video)
        - Product categories
        
        Return the data in JSON format.
        """
        
        return self._extract_structured_data(
            prompt, 
            ProductCatalog, 
            video_path, 
            keyframes, 
            transcript
        )
    
    def extract_tutorial(
        self,
        video_path: Optional[Path] = None,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None
    ) -> Tuple[Optional[TutorialSummary], Optional[str]]:
        """Extract tutorial from educational video"""
        prompt = """
        Analyze this tutorial video and extract the complete tutorial.
        
        Extract:
        - Topic/subject
        - Step-by-step instructions
        - Tools/software required for each step
        - Resource links (if visible)
        - Prerequisites
        - Estimated time to complete
        
        Return the data in JSON format.
        """
        
        return self._extract_structured_data(
            prompt, 
            TutorialSummary, 
            video_path, 
            keyframes, 
            transcript
        )
    
    def extract_song_metadata(
        self,
        video_path: Optional[Path] = None,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None
    ) -> Tuple[Optional[SongMetadata], Optional[str]]:
        """Extract song metadata from music video"""
        prompt = """
        Analyze this music video and extract song metadata.
        
        Extract:
        - Song title
        - Artist name
        - Genre
        - Lyrics snippet (if audible)
        - Spotify link (if visible)
        - YouTube link (if visible)
        - Mood/vibe of the song
        
        Return the data in JSON format.
        """
        
        return self._extract_structured_data(
            prompt, 
            SongMetadata, 
            video_path, 
            keyframes, 
            transcript
        )
    
    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean JSON schema to be compatible with Gemini API.
        
        Gemini only supports a subset of JSON Schema fields. We need to remove:
        - title, description (at root and property levels)
        - example, examples
        - default, defaultValue  
        - format
        - Other metadata fields
        
        Keep only: type, properties, items, required, enum, etc.
        
        Args:
            schema: The schema dict to clean
        
        Returns:
            Cleaned schema compatible with Gemini
        """
        if isinstance(schema, dict):
            cleaned = {}
            # Fields that Gemini API doesn't support - remove these
            unsupported_fields = {
                "title", "description", "example", "examples", 
                "default", "defaultValue", "format", 
                "additionalProperties", "$schema", "$id"
            }
            
            for key, value in schema.items():
                if key in unsupported_fields:
                    continue
                # Recursively clean nested structures
                cleaned[key] = self._clean_schema_for_gemini(value)
            return cleaned
        elif isinstance(schema, list):
            return [self._clean_schema_for_gemini(item) for item in schema]
        else:
            return schema
    
    def _resolve_schema_refs(self, schema: Dict[str, Any], defs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve $ref references in a JSON schema by inlining definitions.
        
        Args:
            schema: The schema dict to process
            defs: The $defs dictionary containing referenced schemas
        
        Returns:
            Schema with all $ref references resolved
        """
        if isinstance(schema, dict):
            if "$ref" in schema:
                # Extract the reference path (e.g., "#/$defs/Exercise")
                ref_path = schema["$ref"]
                if ref_path.startswith("#/$defs/"):
                    ref_name = ref_path.split("/")[-1]
                    if ref_name in defs:
                        # Replace the reference with the actual definition
                        resolved = defs[ref_name].copy()
                        # Recursively resolve any refs in the resolved schema
                        return self._resolve_schema_refs(resolved, defs)
                return schema
            else:
                # Recursively process all values in the dict
                return {k: self._resolve_schema_refs(v, defs) for k, v in schema.items()}
        elif isinstance(schema, list):
            # Recursively process all items in the list
            return [self._resolve_schema_refs(item, defs) for item in schema]
        else:
            return schema
    
    def _extract_structured_data(
        self,
        prompt: str,
        model_class,
        video_path: Optional[Path] = None,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Generic method to extract structured data using Gemini.
        
        Args:
            prompt: Analysis prompt
            model_class: Pydantic model class to validate against
            video_path: Path to video file
            keyframes: List of keyframe image paths
            transcript: Audio transcript text
        
        Returns:
            Tuple of (validated model instance, error_message)
        """
        try:
            # Build content for analysis
            content_parts = [prompt]
            
            # Add video if provided
            if video_path and video_path.exists():
                video_file = genai.upload_file(path=str(video_path))
                content_parts.append(video_file)
            
            # Add keyframes if provided
            if keyframes:
                for keyframe_path in keyframes[:10]:  # Limit to first 10 keyframes
                    if Path(keyframe_path).exists():
                        content_parts.append(genai.upload_file(path=str(keyframe_path)))
            
            # Add transcript if provided
            if transcript:
                content_parts.append(f"\nAudio Transcript:\n{transcript}")
            
            # Generate response with JSON format and schema enforcement
            # Convert Pydantic model to JSON Schema for structured output
            json_schema = model_class.model_json_schema()
            
            # Remove $defs key as Gemini API doesn't support it
            # This is a Pydantic v2 feature for nested schemas that needs to be cleaned
            if "$defs" in json_schema:
                defs = json_schema.pop("$defs")
                # Inline the definitions by resolving $ref references
                json_schema = self._resolve_schema_refs(json_schema, defs)
            
            # Clean schema to remove unsupported fields (example, examples, etc.)
            json_schema = self._clean_schema_for_gemini(json_schema)
            
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=json_schema  # Enforce structure at generation time
            )
            
            response = self.model.generate_content(
                content_parts,
                generation_config=generation_config
            )
            
            # Parse JSON response
            json_data = json.loads(response.text)
            
            # Clean up None values for required fields - provide defaults
            # This handles cases where Gemini doesn't return all required fields
            if model_class == WorkoutRoutine:
                if "estimated_duration_minutes" not in json_data or json_data["estimated_duration_minutes"] is None:
                    # Try to estimate from exercises or set a default
                    json_data["estimated_duration_minutes"] = 20.0  # Default 20 minutes
                if "difficulty_level" not in json_data or json_data["difficulty_level"] is None:
                    json_data["difficulty_level"] = "intermediate"  # Default difficulty
            
            # Validate and create model instance
            try:
                instance = model_class(**json_data)
                return instance, None
            except Exception as validation_error:
                # If validation fails, try to fix common issues
                error_msg = str(validation_error)
                return None, f"Validation error: {error_msg}. JSON data: {json.dumps(json_data, indent=2)}"
            
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON response: {str(e)}"
        except Exception as e:
            return None, f"Error extracting data: {str(e)}"
    
    def analyze_video(
        self,
        video_path: Path,
        keyframes: Optional[list] = None,
        transcript: Optional[str] = None,
        preferred_category: Optional[str] = None
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Analyze video and extract structured data based on category.
        
        Args:
            video_path: Path to video file
            keyframes: List of keyframe image paths
            transcript: Audio transcript text
            preferred_category: Preferred category (if known)
        
        Returns:
            Tuple of (extracted model instance, error_message)
        """
        # Detect category if not provided
        if not preferred_category:
            category, error = self.detect_category(video_path, keyframes, transcript)
            if error:
                return None, error
            preferred_category = category
        
        # Extract based on category
        category_extractors = {
            "workout": self.extract_workout_routine,
            "recipe": self.extract_recipe,
            "travel": self.extract_travel_itinerary,
            "product": self.extract_product_catalog,
            "educational": self.extract_tutorial,
            "music": self.extract_song_metadata
        }
        
        if preferred_category not in category_extractors:
            return None, f"Unknown category: {preferred_category}"
        
        extractor = category_extractors[preferred_category]
        return extractor(video_path, keyframes, transcript)

