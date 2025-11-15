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
    SongMetadata,
    GenericExtraction
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
        
        IMPORTANT INSTRUCTIONS:
        1. Return ONLY the JSON data - NO explanations, reasoning, or thought process
        2. Each field should contain ONLY its value - no extra text or reasoning
        3. Exercise names should be short and clean (e.g., "Squats" not "Squats (0:00-0:30) as shown...")
        4. If you include a 'category' field, it MUST be exactly "workout"
        5. Put extra context in "additional_context" field, NOT in other fields
        
        Return ONLY valid JSON in this format:
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
            "music_tempo_bpm": 140,
            "additional_context": {
                "trainer": "Trainer name if visible",
                "equipment": ["Dumbbells", "Mat"],
                "notes": "Any additional tips or context"
            }
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
        
        IMPORTANT: Put any additional context (chef name, cooking tips, substitutions, 
        difficulty level, dietary info, etc.) into the "additional_context" field.
        
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
        
        IMPORTANT: Put any additional context (best season to visit, travel tips, 
        local culture notes, accommodation suggestions, etc.) into the "additional_context" field.
        
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
        
        IMPORTANT: Put any additional context (product reviews, features, 
        comparisons, discount codes, affiliate info, etc.) into the "additional_context" field.
        
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
        
        IMPORTANT: Put any additional context (instructor name, skill level, 
        common mistakes, troubleshooting tips, etc.) into the "additional_context" field.
        
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
        
        IMPORTANT: Put any additional context (album name, release year, featured artists, 
        music video description, instruments used, etc.) into the "additional_context" field.
        
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
        Clean JSON schema to be compatible with Gemini API using ALLOWLIST approach.
        
        Instead of trying to block all unsupported fields (whack-a-mole),
        we only keep the fields that Gemini DOES support. This is more robust.
        
        Gemini supports these core JSON Schema fields:
        - type, properties, items, required, enum
        - Validation: minimum, maximum, minLength, maxLength, minItems, maxItems
        - pattern, exclusiveMinimum, exclusiveMaximum
        
        Args:
            schema: The schema dict to clean
        
        Returns:
            Cleaned schema compatible with Gemini (only supported fields)
        """
        if isinstance(schema, dict):
            # ALLOWLIST: Only keep fields that Gemini API explicitly supports
            # Based on testing, Gemini only supports CORE structure fields, NO validation fields
            supported_fields = {
                "type",        # Data type (string, number, object, array, boolean, null)
                "properties",  # Object properties
                "items",       # Array items
                "required",    # Required fields
                "enum",        # Enum values
            }
            # Note: Gemini does NOT support validation fields like:
            # minimum, maximum, minLength, maxLength, pattern, format, etc.
            
            cleaned = {}
            for key, value in schema.items():
                if key in supported_fields:
                    # Special handling for 'properties' - it's a dict of property definitions
                    if key == "properties" and isinstance(value, dict):
                        cleaned_props = {}
                        for prop_name, prop_schema in value.items():
                            # Recursively clean each property's schema
                            cleaned_prop = self._clean_schema_for_gemini(prop_schema)
                            # Only include if it has content
                            if cleaned_prop:
                                cleaned_props[prop_name] = cleaned_prop
                        if cleaned_props:  # Only add properties if non-empty
                            cleaned[key] = cleaned_props
                    # Special handling for 'required' - filter out properties that don't exist
                    elif key == "required" and isinstance(value, list):
                        # We'll add this after we know which properties exist
                        cleaned[key] = value
                    else:
                        # Recursively clean nested structures
                        cleaned_value = self._clean_schema_for_gemini(value)
                        if cleaned_value is not None and cleaned_value != {}:
                            cleaned[key] = cleaned_value
            
            # Post-process: Filter 'required' to only include properties that exist
            if "required" in cleaned and "properties" in cleaned:
                valid_required = [
                    req for req in cleaned["required"] 
                    if req in cleaned["properties"]
                ]
                if valid_required:
                    cleaned["required"] = valid_required
                else:
                    # Remove required if no valid fields
                    del cleaned["required"]
            
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
    
    def _format_generic_data(self, data: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Intelligently format and structure data for GenericExtraction.
        
        Attempts to map common field variations to standard names and organize data
        in a readable format even when it doesn't match our exact schema.
        
        Args:
            data: Raw data from Gemini
            model_class: The model class that failed validation
        
        Returns:
            Formatted and structured data dictionary
        """
        # Sometimes Gemini returns a top-level list instead of an object.
        # Normalize that into an { "items": [...] } structure so downstream
        # logic can treat it consistently.
        if isinstance(data, list):
            data = {"items": data}

        formatted = {}
        
        # Common field name variations to normalize
        field_mappings = {
            "title": ["title", "name", "recipe_name", "workout_name", "song_title", "topic"],
            "description": ["description", "desc", "summary", "overview", "notes"],
            "items": ["items", "list", "ingredients", "exercises", "activities", "products", "steps"],
        }
        
        # Try to extract and normalize common fields
        for standard_name, variations in field_mappings.items():
            for variation in variations:
                if variation in data and data[variation]:
                    formatted[standard_name] = data[variation]
                    break
        
        # Format lists/arrays nicely
        for key, value in data.items():
            if isinstance(value, list) and value:
                # Try to format list items
                formatted_list = []
                for item in value:
                    if isinstance(item, dict):
                        # Normalize dictionary keys (e.g., "item" -> "name")
                        formatted_item = {}
                        for k, v in item.items():
                            # Common key normalizations
                            if k in ["item", "exercise", "activity", "product"]:
                                formatted_item["name"] = v
                            else:
                                formatted_item[k] = v
                        formatted_list.append(formatted_item)
                    else:
                        formatted_list.append(item)
                formatted[key] = formatted_list
            elif key not in formatted:  # Don't overwrite already formatted fields
                formatted[key] = value
        
        # Add metadata about what category this was intended for
        formatted["_original_category"] = model_class.__name__
        formatted["_fallback_reason"] = "Field name mismatch or validation error"
        
        return formatted
    
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
            
            # Use flexible JSON generation - let Gemini return whatever it wants
            # We'll map the fields ourselves instead of enforcing strict schema
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json"
                # NOTE: No response_schema - allows Gemini to be flexible
            )
            
            response = self.model.generate_content(
                content_parts,
                generation_config=generation_config
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Sometimes Gemini wraps JSON in markdown code blocks, clean it up
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            gemini_data = json.loads(response_text)

            # Normalize top-level list responses from Gemini into an object so that
            # the rest of the logic (which expects a dict) can operate safely.
            # Example: `[ {...}, {...} ]` -> `{ "items": [ {...}, {...} ] }`
            if isinstance(gemini_data, list):
                gemini_data = {"items": gemini_data}
            
            # Flexible mapping approach:
            # 1. Extract known fields that match our model
            # 2. Put everything else into additional_context
            
            # Get the expected fields from the model
            model_fields = model_class.model_fields.keys()
            
            # Separate matched fields from extra fields
            mapped_data = {}
            extra_context = {}
            
            for key, value in gemini_data.items():
                if key in model_fields:
                    # Clean up fields that might have excessive text
                    if key == "exercises" and isinstance(value, list):
                        for exercise in value:
                            if "name" in exercise and isinstance(exercise["name"], str):
                                if len(exercise["name"]) > 100:
                                    first_line = exercise["name"].split("\n")[0].strip()
                                    exercise["name"] = first_line[:50] if len(first_line) > 50 else first_line
                    mapped_data[key] = value
                else:
                    # This field doesn't match our model, save it as extra context
                    extra_context[key] = value
            
            # Set required fields with defaults if missing
            category_map = {
                WorkoutRoutine: "workout",
                RecipeCard: "recipe",
                TravelItinerary: "travel",
                ProductCatalog: "product",
                TutorialSummary: "educational",
                SongMetadata: "music"
            }
            
            # Always set the correct category
            if model_class in category_map:
                mapped_data["category"] = category_map[model_class]
            
            # Merge or create additional_context
            if extra_context:
                if "additional_context" in mapped_data:
                    # Merge with existing additional_context
                    if isinstance(mapped_data["additional_context"], dict):
                        mapped_data["additional_context"].update(extra_context)
                    else:
                        mapped_data["additional_context"] = extra_context
                else:
                    mapped_data["additional_context"] = extra_context
            
            # Set model-specific defaults
            if model_class == WorkoutRoutine:
                if "estimated_duration_minutes" not in mapped_data or mapped_data["estimated_duration_minutes"] is None:
                    mapped_data["estimated_duration_minutes"] = 20.0
                if "difficulty_level" not in mapped_data or mapped_data["difficulty_level"] is None:
                    mapped_data["difficulty_level"] = "intermediate"
            
            # Try to create the model instance
            try:
                instance = model_class(**mapped_data)
                return instance, None
            except Exception as validation_error:
                # If validation fails, fall back to GenericExtraction
                # This ensures no data is lost even if structure doesn't match
                print(f"⚠️  Validation failed for {model_class.__name__}, falling back to GenericExtraction")
                print(f"   Reason: {str(validation_error)[:200]}...")
                
                try:
                    # Intelligently format the raw data for better readability
                    formatted_data = self._format_generic_data(gemini_data, model_class)
                    
                    # Merge additional_context if it exists in mapped_data
                    # This preserves extra information that was captured
                    if "additional_context" in mapped_data and mapped_data["additional_context"]:
                        if "additional_context" not in formatted_data:
                            formatted_data["additional_context"] = {}
                        # Merge the additional context
                        if isinstance(formatted_data["additional_context"], dict):
                            formatted_data["additional_context"].update(mapped_data["additional_context"])
                        else:
                            formatted_data["additional_context"] = mapped_data["additional_context"]
                    
                    # Also merge any extra_context that was separated out
                    if extra_context:
                        if "additional_context" not in formatted_data:
                            formatted_data["additional_context"] = {}
                        if isinstance(formatted_data["additional_context"], dict):
                            formatted_data["additional_context"].update(extra_context)
                        else:
                            formatted_data["additional_context"] = extra_context
                    
                    # Create a generic extraction with ALL data preserved
                    generic_data = {
                        "category": mapped_data.get("category", "unknown"),
                        "title": formatted_data.get("title") or mapped_data.get("title"),
                        "description": formatted_data.get("description") or mapped_data.get("description"),
                        "source_url": mapped_data.get("source_url"),
                        "confidence_score": mapped_data.get("confidence_score", 0.5),  # Lower confidence for fallback
                        "raw_data": formatted_data # Store ALL formatted data including additional_context
                    }
                    generic_instance = GenericExtraction(**generic_data)
                    print(f"✓ Successfully created GenericExtraction fallback with formatted data")
                    print(f"   Preserved {len(formatted_data)} fields in raw_data")
                    return generic_instance, None
                except Exception as generic_error:
                    # Last resort: return error
                    return None, f"Failed to create even generic extraction: {str(generic_error)}"
            
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
    ) -> Tuple[Optional[Any], Optional[str], Optional[list]]:
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
        extraction_result, error = extractor(video_path, keyframes, transcript)
        return extraction_result, error, keyframes
