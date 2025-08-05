# lambda_function.py (FIXED VERSION)
import json
import boto3
import uuid
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS services
translate_client = boto3.client('translate')
s3_client = boto3.client('s3')

# Environment variables
INPUT_BUCKET = os.environ.get('INPUT_BUCKET')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for translation requests
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Parse the request body
        if 'body' in event:
            if isinstance(event['body'], str):
                request_data = json.loads(event['body'])
            else:
                request_data = event['body']
        else:
            request_data = event
        
        # Validate required fields
        required_fields = ['source_language', 'target_languages', 'sentences']
        for field in required_fields:
            if field not in request_data:
                return create_error_response(400, f"Missing required field: {field}")
        
        # Extract data
        source_language = request_data['source_language']
        target_languages = request_data['target_languages']
        sentences = request_data['sentences']
        
        # Validate input
        validation_error = validate_input(source_language, target_languages, sentences)
        if validation_error:
            return create_error_response(400, validation_error)
        
        # Generate unique translation ID
        translation_id = str(uuid.uuid4())
        
        logger.info(f"Processing translation request {translation_id}")
        logger.info(f"Source: {source_language}, Targets: {target_languages}, Sentences: {len(sentences)}")
        
        # FIXED: Store input request in INPUT bucket
        input_key = f"requests/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{translation_id}_request.json"
        store_input_request(request_data, input_key, translation_id)
        
        # Process translations
        translations = process_translations(
            source_language, 
            target_languages, 
            sentences, 
            translation_id
        )
        
        # Create output document
        output_document = {
            "translation_id": translation_id,
            "source_language": source_language,
            "timestamp": datetime.now(timezone.utc).isoformat(),  # FIXED: Use timezone-aware datetime
            "request_info": {
                "total_sentences": len(sentences),
                "target_languages": target_languages,
                "environment": ENVIRONMENT,
                "input_location": f"s3://{INPUT_BUCKET}/{input_key}"  # Reference to input
            },
            "translations": translations,
            "metadata": {
                "processing_time_ms": context.get_remaining_time_in_millis() if context else None,
                "aws_request_id": context.aws_request_id if context else None
            }
        }
        
        # Store result in S3 OUTPUT bucket
        output_key = f"translations/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{translation_id}.json"  # FIXED: timezone-aware
        s3_url = store_result_in_s3(output_document, output_key)
        
        logger.info(f"Translation completed successfully: {translation_id}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'translation_id': translation_id,
                'input_location': {
                    'bucket': INPUT_BUCKET,
                    'key': input_key,
                    'url': f"s3://{INPUT_BUCKET}/{input_key}"
                },
                'output_location': {
                    'bucket': OUTPUT_BUCKET,
                    'key': output_key,
                    'url': s3_url
                },
                'summary': {
                    'source_language': source_language,
                    'target_languages': target_languages,
                    'sentences_processed': len(sentences),
                    'translations_generated': sum(len(translations[lang]) for lang in translations)
                },
                'timestamp': output_document['timestamp']
            })
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return create_error_response(400, "Invalid JSON in request body")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return create_error_response(500, "Internal server error")

def store_input_request(request_data: Dict[str, Any], input_key: str, translation_id: str) -> str:
    """
    Store original request in INPUT S3 bucket for audit/tracking
    """
    try:
        # Add metadata to the input request
        input_document = {
            "translation_id": translation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_data": request_data,
            "environment": ENVIRONMENT
        }
        
        # Convert to JSON string
        json_content = json.dumps(input_document, indent=2, ensure_ascii=False)
        
        # Upload to INPUT S3 bucket
        s3_client.put_object(
            Bucket=INPUT_BUCKET,
            Key=input_key,
            Body=json_content.encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'translation-id': translation_id,
                'source-language': request_data.get('source_language', 'unknown'),
                'environment': ENVIRONMENT,
                'request-type': 'translation-request'
            }
        )
        
        # Generate S3 URL
        s3_url = f"s3://{INPUT_BUCKET}/{input_key}"
        
        logger.info(f"Input request stored in S3: {s3_url}")
        return s3_url
        
    except Exception as e:
        logger.error(f"S3 input storage error: {str(e)}")
        # Don't fail the whole request if input storage fails
        return ""

def validate_input(source_language: str, target_languages: List[str], sentences: List[str]) -> str:
    """
    Validate input parameters
    """
    # Check source language format
    if not isinstance(source_language, str) or len(source_language) != 2:
        return "Source language must be a 2-character language code"
    
    # Check target languages
    if not isinstance(target_languages, list) or len(target_languages) == 0:
        return "Target languages must be a non-empty list"
    
    if len(target_languages) > 10:
        return "Maximum 10 target languages allowed"
    
    for lang in target_languages:
        if not isinstance(lang, str) or len(lang) != 2:
            return "All target languages must be 2-character language codes"
    
    # Check sentences
    if not isinstance(sentences, list) or len(sentences) == 0:
        return "Sentences must be a non-empty list"
    
    if len(sentences) > 100:
        return "Maximum 100 sentences allowed per request"
    
    for sentence in sentences:
        if not isinstance(sentence, str) or len(sentence.strip()) == 0:
            return "All sentences must be non-empty strings"
        if len(sentence) > 5000:
            return "Each sentence must be less than 5000 characters"
    
    return None

def process_translations(source_language: str, target_languages: List[str], 
                        sentences: List[str], translation_id: str) -> Dict[str, List[str]]:
    """
    Process all translation requests
    """
    translations = {}
    
    for target_lang in target_languages:
        logger.info(f"Translating to {target_lang}")
        translations[target_lang] = []
        
        for i, sentence in enumerate(sentences):
            try:
                # Call AWS Translate
                response = translate_client.translate_text(
                    Text=sentence.strip(),
                    SourceLanguageCode=source_language,
                    TargetLanguageCode=target_lang
                )
                
                translated_text = response['TranslatedText']
                translations[target_lang].append(translated_text)
                
                logger.debug(f"Translated sentence {i+1}/{len(sentences)} to {target_lang}")
                
            except Exception as e:
                logger.error(f"Translation error for sentence {i+1} to {target_lang}: {str(e)}")
                # Add error placeholder but continue processing
                translations[target_lang].append(f"[Translation Error: {str(e)}]")
    
    return translations

def store_result_in_s3(output_document: Dict[str, Any], output_key: str) -> str:
    """
    Store translation result in OUTPUT S3 bucket
    """
    try:
        # Convert to JSON string
        json_content = json.dumps(output_document, indent=2, ensure_ascii=False)
        
        # Upload to OUTPUT S3 bucket
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=json_content.encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'translation-id': output_document['translation_id'],
                'source-language': output_document['source_language'],
                'environment': ENVIRONMENT,
                'result-type': 'translation-result'
            }
        )
        
        # Generate S3 URL
        s3_url = f"s3://{OUTPUT_BUCKET}/{output_key}"
        
        logger.info(f"Result stored in S3: {s3_url}")
        return s3_url
        
    except Exception as e:
        logger.error(f"S3 output storage error: {str(e)}")
        raise

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create standardized error response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Api-Key',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps({
            'success': False,
            'error': {
                'code': status_code,
                'message': message,
                'timestamp': datetime.now(timezone.utc).isoformat()  # FIXED: timezone-aware
            }
        })
    }

# Additional utility functions for enhanced functionality

def get_supported_languages() -> List[str]:
    """
    Get list of supported languages from AWS Translate
    """
    try:
        response = translate_client.list_languages()
        return [lang['LanguageCode'] for lang in response['Languages']]
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        return []

def estimate_translation_cost(sentences: List[str], target_languages: List[str]) -> float:
    """
    Estimate translation cost based on character count
    """
    total_chars = sum(len(sentence) for sentence in sentences)
    total_translations = total_chars * len(target_languages)
    
    # AWS Translate pricing: $15 per 1M characters (as of 2025)
    cost_per_char = 15.0 / 1_000_000
    estimated_cost = total_translations * cost_per_char
    
    return round(estimated_cost, 6)

def batch_translate(sentences: List[str], source_language: str, 
                   target_language: str, batch_size: int = 25) -> List[str]:
    """
    Translate sentences in batches for better performance
    """
    translations = []
    
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i + batch_size]
        
        for sentence in batch:
            try:
                response = translate_client.translate_text(
                    Text=sentence,
                    SourceLanguageCode=source_language,
                    TargetLanguageCode=target_language
                )
                translations.append(response['TranslatedText'])
            except Exception as e:
                logger.error(f"Batch translation error: {str(e)}")
                translations.append(f"[Error: {str(e)}]")
    
    return translations

# Test function for local testing
def test_lambda_locally():
    """
    Test function for local development
    """
    test_event = {
        "body": json.dumps({
            "source_language": "en",
            "target_languages": ["es", "fr"],
            "sentences": ["Hello world", "This is a test"]
        })
    }
    
    class MockContext:
        aws_request_id = "test-request-id"
        def get_remaining_time_in_millis(self):
            return 30000
    
    # Set environment variables for local testing
    os.environ['INPUT_BUCKET'] = 'test-input-bucket'
    os.environ['OUTPUT_BUCKET'] = 'test-output-bucket'
    os.environ['ENVIRONMENT'] = 'local'
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_lambda_locally()