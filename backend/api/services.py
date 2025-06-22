import google.generativeai as genai
import pandas as pd
import re
import json
import logging
from typing import Dict, List, Tuple, Any
from django.conf import settings
from .models import FileUpload, ProcessingJob

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', '')
        
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        
        try:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("LLM Service initialized successfully")
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini: {str(e)}")

    def analyze_description_and_generate_regex(self, user_description: str, available_columns: List[str], 
                                             sample_data: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Analyze user description to determine:
        1. Which columns to target based on the description
        2. Generate appropriate regex pattern
        """
        
        logger.info(f"Analyzing description: {user_description}")
        logger.info(f"Available columns: {available_columns}")
        
        # Prepare sample data context
        sample_context = ""
        if sample_data:
            sample_context = "\n\nSample data from each column:\n"
            for col, samples in sample_data.items():
                sample_context += f"- {col}: {samples[:3]}\n"
        
        prompt = f"""Analyze this user description and determine which columns should be processed and what regex pattern to generate.

USER DESCRIPTION: "{user_description}"

AVAILABLE COLUMNS: {available_columns}
{sample_context}

Based on the user description, determine:
1. Which specific columns should be targeted (be smart about matching)
2. Generate ONE SINGLE appropriate regex pattern that will work across all target columns

COLUMN MATCHING RULES:
- "emails" should match columns like: email, email_address, user_email, contact_email
- "names" should match columns like: name, full_name, first_name, last_name, username
- "phone numbers" should match columns like: phone, telephone, mobile, contact_phone
- "IP addresses" should match columns like: ip, ip_address, server_ip, host_ip
- "addresses" should match columns like: address, location, street, city
- If user says "find emails and names" - target BOTH email and name related columns but create ONE regex that matches BOTH
- Be precise - only target columns that clearly match what the user is asking for

IMPORTANT: 
- For regex patterns, use DOUBLE backslashes for JSON compatibility: \\\\b, \\\\w, \\\\d, \\\\s
- Return ONLY ONE regex pattern that will work for the user's request
- If multiple data types (like emails AND names), create a regex with alternation: "pattern1|pattern2"
- Make patterns SPECIFIC to avoid cross-contamination (e.g., IP patterns shouldn't match phone numbers)

Return ONLY a JSON object with this EXACT structure:
{{
    "target_columns": ["column1", "column2"],
    "regex": "single_regex_pattern_here",
    "explanation": "Explanation of what this regex matches"
}}

Examples of PROPERLY ESCAPED and SPECIFIC regex patterns:
- Email only: "\\\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{{2,7}}\\\\b"
- Names only: "\\\\b[A-Z][a-z]+(?:\\\\s+[A-Z][a-z]+)*\\\\b"
- Phone only: "\\\\b(?:\\\\+?1[-\\.\\\\s]?)?\\\\(?[0-9]{{3}}\\\\)?[-\\.\\\\s]?[0-9]{{3}}[-\\.\\\\s]?[0-9]{{4}}\\\\b"
- IP address only: "\\\\b(?:[0-9]{{1,3}}\\\\.){3}[0-9]{{1,3}}\\\\b"
- BOTH emails AND names: "\\\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{{2,7}}\\\\b|\\\\b[A-Z][a-z]+(?:\\\\s+[A-Z][a-z]+)*\\\\b"
- BOTH phone AND IP: "\\\\b(?:\\\\+?1[-\\.\\\\s]?)?\\\\(?[0-9]{{3}}\\\\)?[-\\.\\\\s]?[0-9]{{3}}[-\\.\\\\s]?[0-9]{{4}}\\\\b|\\\\b(?:[0-9]{{1,3}}\\\\.){3}[0-9]{{1,3}}\\\\b"

Your response:"""

        try:
            logger.info("Calling Gemini for intelligent analysis...")
            response = self.client.generate_content(prompt)
            content = response.text.strip()
            
            logger.info(f"Gemini analysis response: {content}")
            
            # Clean up markdown formatting
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # Parse JSON response
            result = json.loads(content)
            
            # Debug: Log the structure of the result
            logger.info(f"Parsed result structure: {type(result)}")
            logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            if 'regex' in result:
                logger.info(f"Regex type: {type(result['regex'])}, value: {result['regex']}")
            
            # Validate required fields
            if 'target_columns' not in result or 'regex' not in result:
                raise ValueError("Missing required fields in response")
            
            # ADDITIONAL SAFETY: Fix regex escaping if needed
            # Handle case where regex might be a dict or other type
            if isinstance(result['regex'], str):
                result['regex'] = self._ensure_proper_regex_escaping(result['regex'])
            elif isinstance(result['regex'], dict):
                # If regex is a dict, try to extract the pattern
                if 'pattern' in result['regex']:
                    result['regex'] = self._ensure_proper_regex_escaping(result['regex']['pattern'])
                else:
                    logger.warning("Regex returned as dict without 'pattern' key, using fallback")
                    result['regex'] = self._get_fallback_regex_for_description(user_description)['regex']
            else:
                logger.warning(f"Regex returned as unexpected type: {type(result['regex'])}, using fallback")
                result['regex'] = self._get_fallback_regex_for_description(user_description)['regex']
            
            # Validate that target columns exist in available columns
            valid_columns = []
            for col in result['target_columns']:
                if col in available_columns:
                    valid_columns.append(col)
                else:
                    logger.warning(f"Column '{col}' not found in available columns")
            
            result['target_columns'] = valid_columns
            
            # If no valid columns found, use fallback
            if not valid_columns:
                logger.warning("No valid target columns found, using fallback")
                result = self._fallback_analysis(user_description, available_columns)
            
            # Validate regex
            try:
                # Test the regex by converting JSON-escaped pattern back to Python regex
                test_pattern = result['regex'].replace('\\\\', '\\')
                re.compile(test_pattern)
            except re.error as regex_error:
                logger.warning(f"Invalid regex generated: {regex_error}, using fallback")
                result['regex'] = self._get_fallback_regex_for_description(user_description)['regex']
            
            logger.info(f"Final analysis result: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw content: {content}")
            return self._fallback_analysis(user_description, available_columns)
        except Exception as e:
            logger.error(f"Error in intelligent analysis: {e}")
            return self._fallback_analysis(user_description, available_columns)

    def _ensure_proper_regex_escaping(self, regex_pattern: str) -> str:
        """Ensure regex pattern has proper JSON escaping"""
        # If pattern doesn't have proper double escaping, fix it
        if '\\b' in regex_pattern and '\\\\b' not in regex_pattern:
            regex_pattern = regex_pattern.replace('\\b', '\\\\b')
        if '\\w' in regex_pattern and '\\\\w' not in regex_pattern:
            regex_pattern = regex_pattern.replace('\\w', '\\\\w')
        if '\\d' in regex_pattern and '\\\\d' not in regex_pattern:
            regex_pattern = regex_pattern.replace('\\d', '\\\\d')
        if '\\s' in regex_pattern and '\\\\s' not in regex_pattern:
            regex_pattern = regex_pattern.replace('\\s', '\\\\s')
        return regex_pattern

    def _fallback_analysis(self, user_description: str, available_columns: List[str]) -> Dict[str, Any]:
        """Fallback analysis using keyword matching"""
        
        logger.info("Using fallback keyword-based analysis")
        
        description_lower = user_description.lower()
        matched_columns = []
        
        # Smart keyword matching
        column_patterns = {
            'email': ['email', 'mail', 'e-mail', '@'],
            'name': ['name', 'full_name', 'first_name', 'last_name', 'username', 'user_name'],
            'phone': ['phone', 'telephone', 'mobile', 'cell', 'contact'],
            'address': ['address', 'location', 'street', 'city', 'state'],
            'date': ['date', 'time', 'created', 'updated', 'birth'],
            'url': ['url', 'link', 'website', 'site'],
            'ip': ['ip', 'server'],
            'id': ['id', 'identifier', 'uuid']
        }
        
        # Check for explicit mentions in description
        for col in available_columns:
            if col.lower() in description_lower:
                matched_columns.append(col)
        
        # Check for semantic matches
        for col in available_columns:
            col_lower = col.lower()
            for pattern_type, keywords in column_patterns.items():
                # If description mentions this type of data
                if any(keyword in description_lower for keyword in keywords):
                    # And column name suggests it contains this type
                    if any(keyword in col_lower for keyword in keywords):
                        if col not in matched_columns:
                            matched_columns.append(col)
        
        # If no specific matches, check for "all" or "everything"
        if not matched_columns and any(word in description_lower for word in ['all', 'everything', 'any']):
            matched_columns = available_columns
        
        # Generate appropriate regex based on description
        regex_result = self._get_fallback_regex_for_description(user_description)
        
        return {
            'target_columns': matched_columns,
            'regex': regex_result['regex'],
            'explanation': f"Keyword-based analysis: {regex_result['explanation']}"
        }

    def _get_fallback_regex_for_description(self, description: str) -> Dict[str, Any]:
        """Generate fallback regex based on description keywords - PROPERLY ESCAPED FOR JSON"""
        
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['email', 'mail', '@']):
            return {
                'regex': '\\\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,7}\\\\b',
                'explanation': 'Matches email addresses'
            }
        elif any(word in desc_lower for word in ['phone', 'telephone', 'mobile']):
            return {
                'regex': '\\\\b(?:\\\\+?1[-\\.\\\\s]?)?\\\\(?([0-9]{3})\\\\)?[-\\.\\\\s]?([0-9]{3})[-\\.\\\\s]?([0-9]{4})\\\\b',
                'explanation': 'Matches phone numbers'
            }
        elif any(word in desc_lower for word in ['name', 'person']):
            return {
                'regex': '\\\\b[A-Z][a-z]+(?:\\\\s+[A-Z][a-z]+)*\\\\b',
                'explanation': 'Matches names (capitalized words)'
            }
        elif any(word in desc_lower for word in ['url', 'link', 'website']):
            return {
                'regex': 'https?://[^\\\\s]+',
                'explanation': 'Matches URLs'
            }
        elif any(word in desc_lower for word in ['date', 'time']):
            return {
                'regex': '\\\\b\\\\d{1,2}[/-]\\\\d{1,2}[/-]\\\\d{2,4}\\\\b',
                'explanation': 'Matches dates'
            }
        elif any(word in desc_lower for word in ['ip', 'address']):
            return {
                'regex': '\\\\b(?:[0-9]{1,3}\\\\.){3}[0-9]{1,3}\\\\b',
                'explanation': 'Matches IP addresses'
            }
        else:
            return {
                'regex': '\\\\S+',
                'explanation': 'Generic pattern - matches non-whitespace text'
            }

class FileProcessingService:
    def __init__(self):
        logger.info("File Processing Service initialized")

    def read_file(self, file_upload: FileUpload) -> pd.DataFrame:
        """Read CSV or Excel file into DataFrame"""
        file_path = file_upload.file.path
        logger.info(f"Reading file: {file_path}")
        
        try:
            if file_upload.file_type.lower() == 'csv':
                df = pd.read_csv(file_path)
            elif file_upload.file_type.lower() in ['xlsx', 'xls', 'excel']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_upload.file_type}")
            
            logger.info(f"File read successfully. Shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise ValueError(f"Error reading file: {str(e)}")
        
    def paginate_data(self, data: List[Dict], page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Paginate data for display"""
        total_records = len(data)
        max_pages = 100

        # Calculate total pages but cap at 100
        total_pages = min((total_records + page_size - 1) // page_size, max_pages)

        # If user requests page beyond max, redirect to last page
        if page > total_pages:
            page = total_pages if total_pages > 0 else 1
        
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_records)

        # Only show data within the 100-page limit
        max_records = max_pages * page_size  # 1000 records max
        if start_idx >= max_records:
            start_idx = max_records - page_size
            end_idx = max_records
            
        page_data = data[start_idx:end_idx]
        
        return {
            'data': page_data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_records': total_records,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'start_record': start_idx + 1 if page_data else 0,
                'end_record': end_idx if page_data else 0
            }
        }
        
    def get_text_columns(self, df: pd.DataFrame) -> List[str]:
        """Identify text columns in the DataFrame"""
        text_columns = []
        
        for col in df.columns:
            if df[col].dtype == 'object':
                non_null_values = df[col].dropna()
                if len(non_null_values) > 0:
                    text_columns.append(col)
                    
        logger.info(f"Text columns identified: {text_columns}")
        return text_columns

    def get_sample_data_for_columns(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, List[str]]:
        """Get sample data for columns to help with analysis"""
        sample_data = {}
        
        for col in columns:
            if col in df.columns:
                samples = df[col].dropna().head(3).astype(str).tolist()
                sample_data[col] = samples
                
        return sample_data

    def apply_regex_replacement(self,
                                df: pd.DataFrame,
                                regex_pattern: str,
                                replacement: str,
                                target_columns: List[str]) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Apply replacement to specified columns - intelligently decide between regex and full replacement"""

        logger.info(f"Applying replacement to columns: {target_columns}")
        logger.info(f"Using pattern: {regex_pattern}")
        
        df_result = df.copy()
        replacement_stats = {}

        for col in target_columns:
            if col in df_result.columns:
                try:
                    original_values = df_result[col].astype(str)
                    
                    # Determine if this column should use regex or full replacement
                    should_use_full_replacement = self._should_use_full_replacement(col, original_values)
                    
                    if should_use_full_replacement:
                        logger.info(f"Using FULL replacement for column '{col}' (dedicated data column)")
                        # Replace entire content of non-empty cells
                        modified_values = original_values.copy()
                        mask = (original_values != '') & (original_values != 'nan') & (original_values.notna())
                        modified_values[mask] = replacement
                        changes = mask.sum()
                    else:
                        logger.info(f"Using REGEX replacement for column '{col}' (mixed content)")
                        # IMPORTANT: Convert JSON-escaped regex back to Python regex
                        python_regex = regex_pattern.replace('\\\\', '\\')
                        logger.info(f"Python regex pattern: {python_regex}")
                        
                        modified_values = original_values.str.replace(
                            python_regex, replacement, regex=True
                        )
                        changes = sum(original_values != modified_values)
                    
                    replacement_stats[col] = changes
                    df_result[col] = modified_values
                    
                    logger.info(f"Column '{col}': {changes} replacements made")
                    
                except Exception as e:
                    logger.error(f"Error processing column '{col}': {e}")
                    replacement_stats[col] = 0

        return df_result, replacement_stats

    def _should_use_full_replacement(self, column_name: str, column_data) -> bool:
        """
        Determine if we should replace entire cell content or use regex pattern matching
        
        Use FULL replacement when:
        - Column name suggests it contains a specific data type (email, phone, ip, etc.)
        - Column content appears to be homogeneous (all same data type)
        
        Use REGEX replacement when:
        - Column contains mixed content (like descriptions, comments, etc.)
        - We need to find specific patterns within larger text
        """
        
        col_lower = column_name.lower()
        
        # Dedicated data type columns - use full replacement
        dedicated_column_keywords = [
            'email', 'mail', 'e_mail',
            'phone', 'telephone', 'mobile', 'cell',
            'ip', 'ip_address', 'server_ip', 'host_ip',
            'ssn', 'social_security',
            'credit_card', 'card_number',
            'id', 'user_id', 'customer_id',
            'account', 'account_number'
        ]
        
        for keyword in dedicated_column_keywords:
            if keyword in col_lower:
                logger.info(f"Column '{column_name}' identified as dedicated {keyword} column")
                return True
        
        # Mixed content columns - use regex
        mixed_content_keywords = [
            'description', 'comment', 'note', 'text', 'content',
            'message', 'body', 'summary', 'details', 'info'
        ]
        
        for keyword in mixed_content_keywords:
            if keyword in col_lower:
                logger.info(f"Column '{column_name}' identified as mixed content column")
                return False
        
        # Analyze content homogeneity for ambiguous column names
        sample_data = column_data.dropna().head(10).astype(str)
        if len(sample_data) == 0:
            return True  # Empty column, safe to use full replacement
        
        # Check if content looks homogeneous (all similar format)
        # This is a simple heuristic - could be improved
        unique_patterns = set()
        for value in sample_data:
            if '@' in value:
                unique_patterns.add('email')
            elif value.count('.') == 3 and all(part.isdigit() for part in value.split('.')):
                unique_patterns.add('ip')
            elif any(char.isdigit() for char in value) and len(value) >= 10:
                unique_patterns.add('phone')
            else:
                unique_patterns.add('text')
        
        # If mostly one pattern type, use full replacement
        if len(unique_patterns) <= 1:
            logger.info(f"Column '{column_name}' appears homogeneous, using full replacement")
            return True
        else:
            logger.info(f"Column '{column_name}' appears to have mixed content, using regex")
            return False
    
    def process_file_with_pattern(self,
                                  file_upload: FileUpload,
                                  natural_language_query: str,
                                  replacement_value: str,
                                  target_column: str = None,  # Keep for compatibility but ignore
                                  user_api_key: str = None,
                                  page: int = 1,
                                  page_size: int = 100) -> Dict[str, Any]:
        """Process file with intelligent column detection"""
        
        logger.info("Starting intelligent file processing")
        logger.info(f"User query: {natural_language_query}")
        
        try:
            # Read file
            df = self.read_file(file_upload)
            original_data = df.to_dict('records')

            # Get available text columns
            text_columns = self.get_text_columns(df)
            
            if not text_columns:
                raise ValueError("No text columns found in the file")

            # Get sample data for analysis
            sample_data = self.get_sample_data_for_columns(df, text_columns)
            
            # Initialize LLM service
            if not user_api_key:
                raise ValueError("User API key is required")
                
            llm_service = LLMService(api_key=user_api_key)
            
            # INTELLIGENT ANALYSIS: Determine target columns and regex from description
            analysis_result = llm_service.analyze_description_and_generate_regex(
                natural_language_query, text_columns, sample_data
            )
            
            target_columns = analysis_result['target_columns']
            regex_pattern = analysis_result['regex']
            
            logger.info(f"AI determined target columns: {target_columns}")
            logger.info(f"AI generated regex: {regex_pattern}")
            
            # If no target columns found, fallback to all text columns
            if not target_columns:
                logger.warning("No target columns determined, using all text columns")
                target_columns = text_columns

            # Apply replacement
            processed_df, stats = self.apply_regex_replacement(
                df, regex_pattern, replacement_value, target_columns
            )
            
            processed_data = processed_df.to_dict('records')

            logger.info("Intelligent processing completed successfully")

            # Apply pagination
            paginated_original = self.paginate_data(original_data, page, page_size)
            paginated_processed = self.paginate_data(processed_data, page, page_size)

            return {
                'success': True,
                'original_data': original_data,
                'processed_data': processed_data,
                'regex_pattern': regex_pattern,
                'explanation': analysis_result.get('explanation', ''),
                'target_columns_detected': target_columns,  # Show which columns were detected
                'replacement_stats': stats,
                'columns': list(df.columns),
                'text_columns': text_columns,
                'total_stats': {  
                'total_original_records': len(original_data),
                'total_processed_records': len(processed_data)
                 }
            }
            
        except Exception as e:
            logger.error(f"Intelligent processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_data': [],
                'processed_data': [],
                'regex_pattern': '',
                'explanation': '',
                'target_columns_detected': [],
                'replacement_stats': {},
                'columns': [],
                'text_columns': [],
                'total_stats': {  
                'total_original_records': 0,
                'total_processed_records': 0
                 }
            }