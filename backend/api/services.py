import google.generativeai as genai
import pandas as pd
import re
import json
import logging
from typing import Dict, List, Tuple, Any
from django.conf import settings
from .models import FileUpload, ProcessingJob

# Set up logging
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY

        if not self.api_key:
            raise ValueError("Gemini API key not found in settings")
        try:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')  # This line is critical!
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini: {str(e)}")

        # Configure generation settings
        self.generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=200,
            temperature=0.1,
        )
        logger.info("Gemini LLM Service initialized")

    def natural_language_to_regex(self, query: str, sample_data: List[str] = None) -> Dict[str, Any]:
        """Convert natural language query to regex pattern using LLM"""

        logger.info(f"Processing natural language query with Gemini: {query}")

        # FIX: Include the actual query in the prompt
        prompt = f"""Convert this natural language description to a regex pattern.

Query: "{query}"

Rules:
1. Return ONLY a JSON object with 'regex' and 'explanation' fields
2. The regex should be production-ready and safe
3. Consider edge cases and be as accurate as possible
4. Use appropriate flags when needed

Example response:
{{"regex": "\\\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{{2,7}}\\\\b", "explanation": "Matches email addresses with proper domain validation"}}

Your response:"""

        if sample_data:
            prompt += f"\n\nSample data: {sample_data[:3]}"
        
        try:
            logger.info("Calling Gemini API...")
            response = self.client.generate_content(prompt)
            content = response.text.strip()
            
            logger.info(f"Gemini response: {content}")
            
            # Clean up markdown formatting if present
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # Parse JSON response
            result = json.loads(content)
            
            # Validate regex
            if 'regex' not in result:
                raise ValueError("No regex field in response")
            
            re.compile(result['regex'])
            
            return result
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON, attempting fallback parsing")
            return self._parse_gemini_response(content, query)
        
        except Exception as e:
            logger.error(f"Error generating regex: {str(e)}")
            return self._get_fallback_pattern(query)

    # ADD THIS MISSING METHOD:
    def _parse_gemini_response(self, content: str, query: str) -> Dict[str, Any]:
        """Parse Gemini response when JSON parsing fails"""
        
        logger.info("Attempting to parse non-JSON Gemini response")
        
        # Try to extract regex from various formats
        lines = content.split('\n')
        
        for line in lines:
            # Look for regex patterns in quotes
            if '"regex"' in line and ':' in line:
                try:
                    # Extract the regex value
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        regex_part = parts[1].strip().strip(',').strip('"').strip("'")
                        re.compile(regex_part)  # Validate regex
                        return {
                            "regex": regex_part,
                            "explanation": f"Generated regex pattern for: {query}"
                        }
                except Exception as e:
                    logger.warning(f"Failed to extract regex from line: {line}, error: {e}")
                    continue
            
            # Look for regex: pattern
            elif line.strip().startswith('regex:') or 'regex:' in line.lower():
                try:
                    regex_part = line.split(':', 1)[1].strip().strip('"').strip("'")
                    re.compile(regex_part)  # Validate regex
                    return {
                        "regex": regex_part,
                        "explanation": f"Generated regex pattern for: {query}"
                    }
                except Exception as e:
                    logger.warning(f"Failed to extract regex from regex: line: {line}, error: {e}")
                    continue
        
        # If all parsing fails, use fallback
        logger.warning("Could not parse Gemini response, using fallback pattern")
        return self._get_fallback_pattern(query)

    # ADD THIS MISSING METHOD TOO:
    def _get_fallback_pattern(self, query: str) -> Dict[str, Any]:
        """Provide fallback regex patterns for common queries"""
        
        query_lower = query.lower()
        
        fallback_patterns = {
            'email': {
                'regex': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b',
                'explanation': 'Matches email addresses (fallback pattern)'
            },
            'phone': {
                'regex': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                'explanation': 'Matches phone numbers (fallback pattern)'
            },
            'url': {
                'regex': r'https?://[^\s]+',
                'explanation': 'Matches URLs (fallback pattern)'
            },
            'date': {
                'regex': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',
                'explanation': 'Matches dates in MM/DD/YYYY format (fallback pattern)'
            },
            'credit card': {
                'regex': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                'explanation': 'Matches credit card numbers (fallback pattern)'
            },
            'ssn': {
                'regex': r'\b\d{3}-?\d{2}-?\d{4}\b',
                'explanation': 'Matches SSN numbers (fallback pattern)'
            },
            'ip': {
                'regex': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                'explanation': 'Matches IP addresses (fallback pattern)'
            }
        }
        
        # Check for matching patterns
        for keyword, pattern in fallback_patterns.items():
            if keyword in query_lower:
                logger.info(f"Using fallback pattern for: {keyword}")
                return pattern
        
        # Default fallback
        logger.warning("No fallback pattern found, using generic pattern")
        return {
            'regex': r'\S+',
            'explanation': 'Generic pattern - matches any non-whitespace characters (fallback)'
        }

class FileProcessingService:
    def __init__(self):
        self.llm_service = LLMService()

    def read_file(self, file_upload: FileUpload) -> pd.DataFrame:
        """Read CSV or Excel file into DataFrame"""
        file_path = file_upload.file.path
        
        try:
            if file_upload.file_type.lower() == 'csv':
                df = pd.read_csv(file_path)
            elif file_upload.file_type.lower() in ['xlsx','xls','excel']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_upload.file_type}")
            
            return df
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
        
    def get_text_columns(self, df: pd.DataFrame) -> List[str]:
        """Identify text columns in the DataFrame"""
        text_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column contains mostly text
                sample = df[col].dropna().head(10).astype(str)
                if len(sample) > 0:
                    text_columns.append(col)
        return text_columns
    
    def apply_regex_replacement(self,
                                df:pd.DataFrame,
                                regex_pattern:str,
                                replacement:str,
                                target_column:str = None) -> Tuple[pd.DataFrame,Dict[str,int]]:
        """Apply regex replacement to DataFrame"""

        df_copy = df.copy()
        replacement_stats = {}

        # Determine target columns
        if target_column and target_column in df.columns:
            target_columns = [target_column]
        else:
            target_columns = self.get_text_columns(df)

        # Apply regex replacement
        for col in target_columns:
            if col in df_copy.columns:
                original_values = df_copy[col].astype(str)
                modified_values = original_values.str.replace(
                    regex_pattern, replacement, regex=True
                )

                # Count replacements
                changes = sum(original_values != modified_values)
                replacement_stats[col] = changes

                df_copy[col] = modified_values

        return df_copy, replacement_stats
    
    def process_file_with_pattern(self,
                                  file_upload: FileUpload,
                                  natural_language_query:str,
                                  replacement_value:str,
                                  target_column:str=None) -> Dict[str,Any]:
        """Complete file processing workflow"""
        try:
            # Read file
            df = self.read_file(file_upload)
            original_data = df.to_dict('records')

            # Get sample data for LLM context
            text_columns = self.get_text_columns(df)
            sample_data=[]

            if target_column and target_column in df.columns:
                sample_data = df[target_column].dropna().head(5).astype(str).tolist()
            elif text_columns:
                sample_data = df[text_columns[0]].dropna().head(5).astype(str).tolist()
            
            # Generate regex using LLM
            llm_result = self.llm_service.natural_language_to_regex(
                natural_language_query, sample_data
            )
            
            # FIX: Extract regex from the result dictionary
            regex_pattern = llm_result['regex']  # Changed from llm_result to llm_result['regex']

            # Apply replacement
            processed_df, stats = self.apply_regex_replacement(
                df, regex_pattern, replacement_value, target_column)
            
            processed_data = processed_df.to_dict('records')

            return{
                'success':True,
                'original_data':original_data,
                'processed_data':processed_data,
                'regex_pattern':regex_pattern,
                'explanation':llm_result.get('explanation',''),
                'replacement_stats':stats,
                'columns':list(df.columns),
                'text_columns':text_columns
            }
        except Exception as e:
            return{
                'success': False,
                'error': str(e),
                'original_data': [],
                'processed_data': [],
                'regex_pattern': '',
                'explanation': '',
                'replacement_stats': {},
                'columns': [],
                'text_columns': []
            }