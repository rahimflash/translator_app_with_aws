#!/usr/bin/env python3
"""
Enhanced Translation Platform CLI Tool
Features: Progress bars, status tracking, history, detailed reporting, and terminal output
"""

import argparse
import json
import requests
import sys
import os
import boto3
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
from datetime import datetime, timezone
from tqdm import tqdm
import threading
from textwrap import fill
import colorama
from colorama import Fore, Style, Back

# Initialize colorama for cross-platform colored output
colorama.init()

class TranslationCLI:
    def __init__(self, api_endpoint: str = None, api_key: str = None):
        self.api_endpoint = api_endpoint or os.environ.get('TRANSLATION_API_ENDPOINT')
        self.api_key = api_key or os.environ.get('TRANSLATION_API_KEY')
        self.config_file = Path.home() / '.translation-cli-config.json'
        self.history_file = Path.home() / '.translation-cli-history.json'
        
        # Load config if exists
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.api_endpoint = self.api_endpoint or config.get('api_endpoint')
                self.api_key = self.api_key or config.get('api_key')
                self.output_bucket = config.get('output_bucket')
                self.aws_region = config.get('aws_region', 'eu-west-1')

        # Initialize S3 client for status checking
        try:
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
        except:
            self.s3_client = None

    def configure(self, api_endpoint: str, api_key: str, output_bucket: str = None, aws_region: str = 'eu-west-1'):
        """Configure CLI with API endpoint, key, and AWS settings"""
        config = {
            'api_endpoint': api_endpoint,
            'api_key': api_key,
            'output_bucket': output_bucket,
            'aws_region': aws_region,
            'configured_at': datetime.now(timezone.utc).isoformat()
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration saved to {self.config_file}")
        
        # Test configuration
        if self._test_connection():
            print("✅ Connection test successful")
        else:
            print("⚠️  Warning: Could not verify API connection")

    def _test_connection(self) -> bool:
        """Test API connection"""
        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['X-API-Key'] = self.api_key
            
            # Send a minimal test request
            test_payload = {
                'source_language': 'en',
                'target_languages': ['es'],
                'sentences': ['test']
            }
            
            response = requests.post(self.api_endpoint, headers=headers, json=test_payload, timeout=10)
            return response.status_code in [200, 400]  # 400 is OK for validation test
        except:
            return False

    def translate(self, source_lang: str, target_langs: List[str], 
                 sentences: List[str], output_file: str = None, 
                 show_progress: bool = True, show_terminal: bool = True,
                 download_s3: bool = False) -> Dict[str, Any]:
        """Send translation request with progress tracking"""
        
        if not self.api_endpoint:
            print("❌ Error: API endpoint not configured. Use 'configure' command first.")
            sys.exit(1)
        
        # Estimate processing time
        estimated_time = len(sentences) * len(target_langs) * 0.5  # rough estimate
        
        # Prepare request data
        request_data = {
            'source_language': source_lang,
            'target_languages': target_langs,
            'sentences': sentences
        }
        
        # Prepare headers
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        print(f"🔄 Starting translation job")
        print(f"📊 {len(sentences)} sentences → {len(target_langs)} languages")
        print(f"⏱️  Estimated time: {estimated_time:.1f} seconds")
        
        # Show progress bar during request
        progress_bar = None
        if show_progress:
            progress_bar = tqdm(
                total=100, 
                desc="Processing", 
                bar_format="{l_bar}{bar}| {n:.1f}%",
                leave=False
            )
            
            # Start progress animation
            progress_thread = threading.Thread(
                target=self._animate_progress, 
                args=(progress_bar, estimated_time)
            )
            progress_thread.daemon = True
            progress_thread.start()
        
        try:
            start_time = time.time()
            
            # Send request
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=request_data,
                timeout=max(300, estimated_time * 2)
            )
            
            end_time = time.time()
            actual_time = end_time - start_time
            
            if progress_bar:
                progress_bar.n = 100
                progress_bar.refresh()
                progress_bar.close()
            
            if response.status_code == 200:
                result = response.json()
                translation_id = result['translation_id']
                
                print(f"✅ Translation completed successfully!")
                print(f"🆔 Translation ID: {translation_id}")
                print(f"⏱️  Actual time: {actual_time:.1f} seconds")
                print(f"📦 Output location: {result['output_location']['url']}")
                
                # Display translations in terminal if requested
                if show_terminal:
                    self._display_translations_terminal(
                        sentences, 
                        result.get('translations', {}), 
                        source_lang, 
                        target_langs
                    )
                
                # Save to history
                self._save_to_history(result, source_lang, target_langs, len(sentences))
                
                # Save to file if requested
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"💾 Results saved to {output_file}")
                
                # Offer to download from S3
                if download_s3 and self.s3_client and self.output_bucket:
                    self._download_translation(result['output_location']['key'])
                elif self.s3_client and self.output_bucket:
                    download = input("📥 Download translated file? (y/n): ").lower().startswith('y')
                    if download:
                        self._download_translation(result['output_location']['key'])
                
                return result
                
            else:
                if progress_bar:
                    progress_bar.close()
                    
                error_data = response.json() if response.content else {}
                print(f"❌ Translation failed: {response.status_code}")
                print(f"Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
                sys.exit(1)
                
        except requests.exceptions.Timeout:
            if progress_bar:
                progress_bar.close()
            print(f"❌ Request timeout after {estimated_time * 2:.1f} seconds")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            if progress_bar:
                progress_bar.close()
            print(f"❌ Network error: {str(e)}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            if progress_bar:
                progress_bar.close()
            print(f"❌ Invalid response format: {str(e)}")
            sys.exit(1)

    def _display_translations_terminal(self, original_sentences: List[str], 
                                     translations: Dict[str, List[str]], 
                                     source_lang: str, target_langs: List[str]):
        """Display translations in a beautiful terminal format"""
        
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}🌐 TRANSLATION RESULTS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
        # Language flag emojis (basic mapping)
        lang_flags = {
            'en': '🇺🇸', 'es': '🇪🇸', 'fr': '🇫🇷', 'de': '🇩🇪', 'it': '🇮🇹',
            'pt': '🇵🇹', 'ru': '🇷🇺', 'zh': '🇨🇳', 'ja': '🇯🇵', 'ko': '🇰🇷',
            'ar': '🇸🇦', 'hi': '🇮🇳', 'tr': '🇹🇷', 'pl': '🇵🇱', 'nl': '🇳🇱'
        }
        
        for i, original in enumerate(original_sentences):
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}📝 Sentence {i+1}:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{Back.BLUE} {source_lang.upper()} {Style.RESET_ALL} {lang_flags.get(source_lang, '🌍')} {original}")
            
            # Display each translation
            for lang in target_langs:
                if lang in translations and i < len(translations[lang]):
                    translated_text = translations[lang][i]
                    flag = lang_flags.get(lang, '🌍')
                    
                    # Color code by language for better readability
                    colors = [Fore.GREEN, Fore.MAGENTA, Fore.CYAN, Fore.YELLOW, Fore.BLUE]
                    color = colors[target_langs.index(lang) % len(colors)]
                    
                    print(f"{color}{Back.BLACK} {lang.upper()} {Style.RESET_ALL} {flag} {translated_text}")
                else:
                    print(f"{Fore.RED}❌ {lang.upper()} - Translation not available{Style.RESET_ALL}")
            
            # Add separator between sentences if more than one
            if i < len(original_sentences) - 1:
                print(f"{Fore.BLUE}{'─' * 40}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        
        # Summary statistics
        total_translations = sum(len(translations.get(lang, [])) for lang in target_langs)
        print(f"{Fore.GREEN}📊 Summary: {len(original_sentences)} sentences → {total_translations} translations{Style.RESET_ALL}")

    def _display_translations_simple(self, original_sentences: List[str], 
                                   translations: Dict[str, List[str]], 
                                   source_lang: str, target_langs: List[str]):
        """Display translations in simple format (no colors)"""
        
        print("\n" + "=" * 80)
        print("🌐 TRANSLATION RESULTS")
        print("=" * 80)
        
        for i, original in enumerate(original_sentences):
            print(f"\n📝 Sentence {i+1}:")
            print(f"[{source_lang.upper()}] {original}")
            
            # Display each translation
            for lang in target_langs:
                if lang in translations and i < len(translations[lang]):
                    translated_text = translations[lang][i]
                    print(f"[{lang.upper()}] {translated_text}")
                else:
                    print(f"[{lang.upper()}] ❌ Translation not available")
            
            # Add separator between sentences if more than one
            if i < len(original_sentences) - 1:
                print("-" * 40)
        
        print("\n" + "=" * 80)

    def _animate_progress(self, progress_bar: tqdm, estimated_time: float):
        """Animate progress bar during translation"""
        start_time = time.time()
        while progress_bar.n < 95:  # Don't go to 100% until actually done
            elapsed = time.time() - start_time
            progress = min(95, (elapsed / estimated_time) * 100)
            progress_bar.n = progress
            progress_bar.refresh()
            time.sleep(0.1)

    def _download_translation(self, s3_key: str, local_path: str = None):
        """Download translation result from S3"""
        if not self.s3_client or not self.output_bucket:
            print("❌ S3 access not configured")
            return
        
        if not local_path:
            filename = os.path.basename(s3_key)
            local_path = f"./downloads/{filename}"
            os.makedirs("./downloads", exist_ok=True)
        
        try:
            print(f"📥 Downloading from S3...")
            self.s3_client.download_file(self.output_bucket, s3_key, local_path)
            print(f"✅ Downloaded to {local_path}")
        except Exception as e:
            print(f"❌ Download failed: {str(e)}")

    def get_translation_status(self, translation_id: str) -> Dict[str, Any]:
        """Get status of a specific translation"""
        
        # Check history first
        history = self._load_history()
        for record in history:
            if record.get('translation_id') == translation_id:
                print(f"📋 Translation Status for {translation_id}")
                print(f"🕐 Created: {record.get('timestamp')}")
                print(f"🌐 Languages: {record.get('source_lang')} → {record.get('target_langs')}")
                print(f"📝 Sentences: {record.get('sentence_count')}")
                print(f"✅ Status: Completed")
                print(f"📦 Location: {record.get('output_location')}")
                
                # Try to verify file exists in S3
                if self.s3_client and self.output_bucket:
                    s3_key = record.get('s3_key')
                    if s3_key and self._check_s3_file_exists(s3_key):
                        print(f"✅ File verified in S3")
                    else:
                        print(f"⚠️  File not found in S3")
                
                return record
        
        print(f"❌ Translation {translation_id} not found in local history")
        return {}

    def _check_s3_file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.output_bucket, Key=s3_key)
            return True
        except:
            return False

    def list_translations(self, limit: int = 10):
        """List recent translations"""
        history = self._load_history()
        
        if not history:
            print("📭 No translation history found")
            return
        
        print(f"📜 Recent Translations (showing last {min(limit, len(history))})")
        print("=" * 80)
        
        for record in history[-limit:]:
            print(f"🆔 {record.get('translation_id', 'Unknown')[:8]}...")
            print(f"   🕐 {record.get('timestamp')}")
            print(f"   🌐 {record.get('source_lang')} → {', '.join(record.get('target_langs', []))}")
            print(f"   📝 {record.get('sentence_count')} sentences")
            print()

    def _save_to_history(self, result: Dict[str, Any], source_lang: str, 
                        target_langs: List[str], sentence_count: int):
        """Save translation to history"""
        history = self._load_history()
        
        record = {
            'translation_id': result.get('translation_id'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_lang': source_lang,
            'target_langs': target_langs,
            'sentence_count': sentence_count,
            'output_location': result.get('output_location', {}).get('url'),
            's3_key': result.get('output_location', {}).get('key')
        }
        
        history.append(record)
        
        # Keep only last 100 records
        if len(history) > 100:
            history = history[-100:]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load translation history"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def translate_file(self, input_file: str, source_lang: str, 
                      target_langs: List[str], output_file: str = None,
                      batch_size: int = 25, show_terminal: bool = True):
        """Translate sentences from a file with batching support"""
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                if input_file.endswith('.json'):
                    data = json.load(f)
                    if isinstance(data, list):
                        sentences = data
                    elif isinstance(data, dict) and 'sentences' in data:
                        sentences = data['sentences']
                    else:
                        sentences = [str(data)]
                else:
                    # Text file - one sentence per line
                    sentences = [line.strip() for line in f if line.strip()]
            
            if not sentences:
                print("❌ No sentences found in input file")
                sys.exit(1)
            
            # Process in batches if file is large
            if len(sentences) > batch_size:
                print(f"📦 Processing {len(sentences)} sentences in batches of {batch_size}")
                
                all_results = []
                
                for i in range(0, len(sentences), batch_size):
                    batch = sentences[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(sentences) + batch_size - 1) // batch_size
                    
                    print(f"\n🔄 Processing batch {batch_num}/{total_batches}")
                    
                    result = self.translate(source_lang, target_langs, batch, 
                                          show_progress=True, show_terminal=show_terminal)
                    all_results.append(result)
                    
                    # Small delay between batches
                    if i + batch_size < len(sentences):
                        time.sleep(1)
                
                print(f"✅ All batches completed! Processed {len(sentences)} sentences total.")
                return all_results
            else:
                return self.translate(source_lang, target_langs, sentences, output_file, 
                                    show_terminal=show_terminal)
            
        except FileNotFoundError:
            print(f"❌ Input file not found: {input_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in input file: {str(e)}")
            sys.exit(1)

    def status(self):
        """Show CLI configuration and system status"""
        print("🔧 Translation CLI Configuration:")
        print(f"API Endpoint: {self.api_endpoint or 'Not configured'}")
        print(f"API Key: {'Configured' if self.api_key else 'Not configured'}")
        print(f"Output Bucket: {getattr(self, 'output_bucket', 'Not configured')}")
        print(f"AWS Region: {getattr(self, 'aws_region', 'Not configured')}")
        print(f"Config file: {self.config_file}")
        print(f"History file: {self.history_file}")
        print(f"S3 Access: {'Available' if self.s3_client else 'Not available'}")
        
        # Test API connection
        if self.api_endpoint:
            print(f"API Status: {'🟢 Connected' if self._test_connection() else '🔴 Connection failed'}")
        
        # Show recent activity
        history = self._load_history()
        if history:
            recent = history[-1]
            print(f"Last translation: {recent.get('timestamp')} ({recent.get('translation_id', 'Unknown')[:8]}...)")

    def get_s3_translation(self, translation_id: str, display_terminal: bool = True):
        """Fetch and display translation from S3"""
        if not self.s3_client or not self.output_bucket:
            print("❌ S3 access not configured")
            return
        
        # Try to find the translation in history first
        history = self._load_history()
        s3_key = None
        for record in history:
            if record.get('translation_id') == translation_id:
                s3_key = record.get('s3_key')
                break
        
        if not s3_key:
            print(f"❌ Translation {translation_id} not found in history")
            return
        
        try:
            # Download the translation file from S3
            response = self.s3_client.get_object(Bucket=self.output_bucket, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            translation_data = json.loads(content)
            
            if display_terminal:
                # Extract original sentences and translations
                original_sentences = []
                translations = translation_data.get('translations', {})
                
                # Try to reconstruct original sentences from translation data
                if translations:
                    # Get length from first language
                    first_lang = list(translations.keys())[0]
                    sentence_count = len(translations[first_lang])
                    original_sentences = [f"Sentence {i+1}" for i in range(sentence_count)]
                
                self._display_translations_terminal(
                    original_sentences,
                    translations,
                    translation_data.get('source_language', 'unknown'),
                    list(translations.keys())
                )
            
            return translation_data
            
        except Exception as e:
            print(f"❌ Failed to fetch translation from S3: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Translation Platform CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Configure command
    config_parser = subparsers.add_parser('configure', help='Configure API settings')
    config_parser.add_argument('--endpoint', required=True, help='API Gateway endpoint URL')
    config_parser.add_argument('--api-key', required=True, help='API key for authentication')
    config_parser.add_argument('--output-bucket', help='S3 output bucket name')
    config_parser.add_argument('--aws-region', default='eu-west-1', help='AWS region')
    
    # Translate command
    translate_parser = subparsers.add_parser('translate', help='Translate text')
    translate_parser.add_argument('--source-lang', required=True, help='Source language code (e.g., en)')
    translate_parser.add_argument('--target-langs', required=True, help='Target language codes (comma-separated)')
    translate_parser.add_argument('--text', help='Text to translate (for single sentence)')
    translate_parser.add_argument('--file', help='Input file with sentences')
    translate_parser.add_argument('--output', help='Output file for results')
    translate_parser.add_argument('--batch-size', type=int, default=25, help='Batch size for large files')
    translate_parser.add_argument('--no-progress', action='store_true', help='Disable progress bar')
    translate_parser.add_argument('--no-terminal', action='store_true', help='Disable terminal output display')
    translate_parser.add_argument('--simple-format', action='store_true', help='Use simple format (no colors)')
    translate_parser.add_argument('--download', action='store_true', help='Auto-download S3 file')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show configuration and system status')
    
    # Get translation status
    get_status_parser = subparsers.add_parser('get-status', help='Get status of specific translation')
    get_status_parser.add_argument('translation_id', help='Translation ID to check')
    
    # List translations
    list_parser = subparsers.add_parser('list', help='List recent translations')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of translations to show')
    
    # Show translation from S3
    show_parser = subparsers.add_parser('show', help='Show translation results from S3')
    show_parser.add_argument('translation_id', help='Translation ID to display')
    show_parser.add_argument('--simple-format', action='store_true', help='Use simple format (no colors)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = TranslationCLI()
    
    if args.command == 'configure':
        cli.configure(args.endpoint, args.api_key, args.output_bucket, args.aws_region)
    
    elif args.command == 'translate':
        target_langs = [lang.strip() for lang in args.target_langs.split(',')]
        show_progress = not args.no_progress
        show_terminal = not args.no_terminal
        download_s3 = args.download
        
        # Override display method if simple format requested
        if args.simple_format:
            cli._display_translations_terminal = cli._display_translations_simple
        
        if args.text:
            sentences = [args.text]
            cli.translate(args.source_lang, target_langs, sentences, args.output, 
                         show_progress, show_terminal, download_s3)
        elif args.file:
            cli.translate_file(args.file, args.source_lang, target_langs, args.output, 
                             args.batch_size, show_terminal)
        else:
            print("❌ Either --text or --file must be provided")
            sys.exit(1)
    
    elif args.command == 'status':
        cli.status()
    
    elif args.command == 'get-status':
        cli.get_translation_status(args.translation_id)
    
    elif args.command == 'list':
        cli.list_translations(args.limit)
    
    elif args.command == 'show':
        if args.simple_format:
            cli._display_translations_terminal = cli._display_translations_simple
        cli.get_s3_translation(args.translation_id)

if __name__ == '__main__':
    main()