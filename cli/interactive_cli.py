#!/usr/bin/env python3
"""
Complete Interactive Translation Platform CLI Tool
Features: Setup wizard, progress bars, status tracking, history, and detailed reporting
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
import colorama
from colorama import Fore, Style, Back

# Initialize colorama for cross-platform colored output
colorama.init()

class InteractiveTranslationCLI:
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

        # Common languages for quick selection
        self.common_languages = {
            '1': ('en', 'English'),
            '2': ('es', 'Spanish'),
            '3': ('fr', 'French'),
            '4': ('de', 'German'),
            '5': ('it', 'Italian'),
            '6': ('pt', 'Portuguese'),
            '7': ('ru', 'Russian'),
            '8': ('zh', 'Chinese'),
            '9': ('ja', 'Japanese'),
            '10': ('ko', 'Korean'),
            '11': ('ar', 'Arabic'),
            '12': ('hi', 'Hindi')
        }

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
        
        # Update instance variables
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.output_bucket = output_bucket
        self.aws_region = aws_region
        
        print(f"✅ Configuration saved to {self.config_file}")

    def setup_wizard(self):
        """Interactive setup wizard for CLI configuration"""
        print(f"{Fore.CYAN}🔧 Translation Platform Setup Wizard{Style.RESET_ALL}")
        print("=" * 50)
        
        print(f"{Fore.YELLOW}Please provide your translation platform details:{Style.RESET_ALL}")
        
        # Get API endpoint
        while True:
            endpoint = input(f"\n{Fore.CYAN}API Endpoint URL: {Style.RESET_ALL}").strip()
            if endpoint:
                if not endpoint.startswith(('http://', 'https://')):
                    print(f"{Fore.RED}❌ Please include http:// or https:// in the URL{Style.RESET_ALL}")
                    continue
                break
            else:
                print(f"{Fore.RED}❌ API endpoint is required{Style.RESET_ALL}")
        
        # Get API key
        while True:
            api_key = input(f"{Fore.CYAN}API Key: {Style.RESET_ALL}").strip()
            if api_key:
                break
            else:
                print(f"{Fore.RED}❌ API key is required{Style.RESET_ALL}")
        
        # Test connection FIRST
        print(f"\n{Fore.YELLOW}🔍 Testing connection...{Style.RESET_ALL}")
        
        # Temporarily set values for testing (without modifying config)
        temp_endpoint = self.api_endpoint
        temp_key = self.api_key
        self.api_endpoint = endpoint
        self.api_key = api_key
        
        connection_success = self._test_connection()
        
        if connection_success:
            print(f"{Fore.GREEN}✅ Connection test successful!{Style.RESET_ALL}")
            
            # Optional settings
            print(f"\n{Fore.YELLOW}Optional settings (press Enter to skip):{Style.RESET_ALL}")
            bucket = input(f"{Fore.CYAN}S3 Output Bucket: {Style.RESET_ALL}").strip()
            region = input(f"{Fore.CYAN}AWS Region (default: eu-west-1): {Style.RESET_ALL}").strip()
            
            # Save configuration
            print(f"\n{Fore.YELLOW}💾 Saving configuration...{Style.RESET_ALL}")
            self.configure(endpoint, api_key, bucket or None, region or 'eu-west-1')
            
            print(f"{Fore.GREEN}✅ Setup completed successfully!{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}You can now use the translation platform:{Style.RESET_ALL}")
            print(f"  • {Fore.WHITE}python cli/interactive_cli.py{Style.RESET_ALL} - Interactive mode")
            print(f"  • {Fore.WHITE}python cli/interactive_cli.py myfile.txt{Style.RESET_ALL} - Translate a file")
            print(f"  • {Fore.WHITE}python translation_gui.py{Style.RESET_ALL} - Start GUI interface")
            return True
        else:
            # Restore original values
            self.api_endpoint = temp_endpoint
            self.api_key = temp_key
            
            print(f"{Fore.RED}❌ Connection test failed{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Configuration not saved due to connection failure{Style.RESET_ALL}")
            
            # Ask if user wants to retry
            retry = input(f"\n{Fore.CYAN}Try again with different settings? (y/N): {Style.RESET_ALL}").strip().lower()
            if retry.startswith('y'):
                return self.setup_wizard()  # Recursive retry
            else:
                print(f"{Fore.YELLOW}Setup cancelled. Run --setup again when ready.{Style.RESET_ALL}")
                return False

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
            
            # Check for success or validation error (which means API is working)
            if response.status_code == 200:
                return True
            elif response.status_code == 400:
                # Check if it's a validation error
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', '')
                    
                    # These are "good" 400 errors that indicate the API is working
                    good_errors = [
                        'Missing required field',
                        'Source language must be',
                        'Target languages must be',
                        'Sentences must be',
                        'Maximum',
                        'validation'
                    ]
                    
                    return any(good_error in error_message for good_error in good_errors)
                except:
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"{Fore.RED}Connection error: {str(e)}{Style.RESET_ALL}")
            return False

    def detect_file_content(self, filepath: str) -> tuple[List[str], Optional[str]]:
        """Detect and extract content from files, including source language if specified"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.endswith('.json'):
                    data = json.load(f)
                    
                    # Check if it's our API format with source_language
                    if isinstance(data, dict):
                        source_lang = data.get('source_language')
                        sentences = data.get('sentences', [])
                        
                        # If no sentences key, check if it's just a sentences array with metadata
                        if not sentences and 'sentences' not in data:
                            sentences = [str(data)]
                        
                        return sentences, source_lang
                    
                    # Simple array format
                    elif isinstance(data, list):
                        return data, None
                    
                    else:
                        return [str(data)], None
                else:
                    # Text file - one sentence per line, ignore comments
                    sentences = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            sentences.append(line)
                    return sentences, None
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Error reading file: {str(e)}{Style.RESET_ALL}")
            return [], None

    def prompt_for_sentences(self, file_path: str = None) -> List[str]:
        """Interactive prompt for sentences"""
        if file_path:
            sentences, _ = self.detect_file_content(file_path)
            if sentences:
                print(f"{Fore.GREEN}✅ Found {len(sentences)} sentences in file{Style.RESET_ALL}")
                
                # Show first few sentences
                preview_count = min(3, len(sentences))
                for i in range(preview_count):
                    print(f"   {i+1}. {sentences[i][:60]}{'...' if len(sentences[i]) > 60 else ''}")
                
                if len(sentences) > preview_count:
                    print(f"   ... and {len(sentences) - preview_count} more")
                
                confirm = input(f"\n{Fore.CYAN}Use these sentences? (y/n): {Style.RESET_ALL}").lower()
                if confirm.startswith('y'):
                    return sentences
        
        # Manual input
        print(f"\n{Fore.CYAN}📝 Enter sentences to translate:{Style.RESET_ALL}")
        print("   - Type each sentence and press Enter")
        print("   - Type 'done' when finished")
        print("   - Type 'quit' to exit")
        
        sentences = []
        while True:
            sentence = input(f"{Fore.YELLOW}Sentence {len(sentences) + 1}: {Style.RESET_ALL}").strip()
            
            if sentence.lower() == 'done':
                break
            elif sentence.lower() == 'quit':
                sys.exit(0)
            elif sentence:
                sentences.append(sentence)
            else:
                print(f"{Fore.RED}❌ Sentence cannot be empty. Try again or type 'done'{Style.RESET_ALL}")
        
        if not sentences:
            print(f"{Fore.RED}❌ No sentences provided. Exiting.{Style.RESET_ALL}")
            sys.exit(1)
        
        return sentences

    def prompt_for_language(self, prompt_text: str, allow_multiple: bool = False) -> str or List[str]:
        """Interactive language selection"""
        print(f"\n{Fore.CYAN}{prompt_text}:{Style.RESET_ALL}")
        print("Common languages:")
        
        # Display in columns
        for i, (key, (code, name)) in enumerate(self.common_languages.items()):
            if i % 2 == 0 and i > 0:
                print()
            print(f"  {key}. {name} ({code})", end="  " if i % 2 == 0 else "\n")
        
        print(f"\n  Or enter language code directly (e.g., 'en', 'es')")
        if allow_multiple:
            print(f"  For multiple languages, separate with commas (e.g., 'es,fr,de')")
        
        while True:
            choice = input(f"{Fore.YELLOW}Your choice: {Style.RESET_ALL}").strip()
            
            if not choice:
                print(f"{Fore.RED}❌ Please make a selection{Style.RESET_ALL}")
                continue
            
            # Check if it's a number from the menu
            if choice in self.common_languages:
                lang_code = self.common_languages[choice][0]
                return [lang_code] if allow_multiple else lang_code
            
            # Direct language code input
            if allow_multiple and ',' in choice:
                langs = [lang.strip().lower() for lang in choice.split(',')]
                if all(len(lang) == 2 for lang in langs):
                    return langs
                else:
                    print(f"{Fore.RED}❌ All language codes must be 2 characters (e.g., 'en', 'es'){Style.RESET_ALL}")
                    continue
            else:
                lang = choice.lower()
                if len(lang) == 2:
                    return [lang] if allow_multiple else lang
                else:
                    print(f"{Fore.RED}❌ Language code must be 2 characters (e.g., 'en', 'es'){Style.RESET_ALL}")
                    continue

    def prompt_for_options(self, sentence_count: int) -> Dict[str, Any]:
        """Prompt for translation options"""
        options = {}
        
        # Batch processing
        if sentence_count > 25:
            print(f"\n{Fore.CYAN}📦 You have {sentence_count} sentences.{Style.RESET_ALL}")
            batch = input(f"Enable batch processing? (Y/n): ").strip().lower()
            if not batch or batch.startswith('y'):
                try:
                    batch_size = input(f"Batch size (default 25): ").strip()
                    options['batch_size'] = int(batch_size) if batch_size else 25
                except ValueError:
                    options['batch_size'] = 25
            else:
                options['batch_size'] = sentence_count
        else:
            options['batch_size'] = sentence_count
        
        # Output format
        print(f"\n{Fore.CYAN}📱 Display options:{Style.RESET_ALL}")
        
        # Terminal display
        terminal = input(f"Show results in terminal? (Y/n): ").strip().lower()
        options['show_terminal'] = not (terminal and terminal.startswith('n'))
        
        if options['show_terminal']:
            # Simple format
            simple = input(f"Use simple format (no colors)? (y/N): ").strip().lower()
            options['simple_format'] = simple and simple.startswith('y')
        
        # File output
        save_file = input(f"Save results to file? (y/N): ").strip().lower()
        if save_file and save_file.startswith('y'):
            filename = input(f"Output filename (default: translation_results.json): ").strip()
            options['output_file'] = filename if filename else 'translation_results.json'
        
        # S3 download
        if self.s3_client and self.output_bucket:
            download = input(f"Download S3 file? (y/N): ").strip().lower()
            options['download_s3'] = download and download.startswith('y')
        
        return options

    def check_configuration(self) -> bool:
        """Check if CLI is configured"""
        if not self.api_endpoint or not self.api_key:
            print(f"{Fore.RED}❌ CLI not configured{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Please run 'python cli/interactive_cli.py --setup' to configure the CLI first{Style.RESET_ALL}")
            return False
        
        return True

    def interactive_translate(self, file_path: str = None):
        """Main interactive translation workflow"""
        print(f"{Fore.CYAN}🌐 Welcome to Interactive Translation Platform{Style.RESET_ALL}")
        print("=" * 50)
        
        # Check configuration
        if not self.check_configuration():
            sys.exit(1)
        
        # Step 1: Get sentences
        sentences = self.prompt_for_sentences(file_path)
        print(f"{Fore.GREEN}✅ Got {len(sentences)} sentences to translate{Style.RESET_ALL}")
        
        # Step 2: Detect source language from file or prompt
        source_lang = None
        if file_path:
            _, detected_source = self.detect_file_content(file_path)
            if detected_source:
                print(f"{Fore.GREEN}✅ Detected source language: {detected_source}{Style.RESET_ALL}")
                confirm = input(f"Use detected source language '{detected_source}'? (Y/n): ").strip().lower()
                if not confirm or confirm.startswith('y'):
                    source_lang = detected_source
        
        if not source_lang:
            source_lang = self.prompt_for_language("Select source language", allow_multiple=False)
        
        # Step 3: Get target languages
        target_langs = self.prompt_for_language("Select target language(s)", allow_multiple=True)
        
        # Step 4: Get options
        options = self.prompt_for_options(len(sentences))
        
        # Step 5: Confirm and translate
        print(f"\n{Fore.CYAN}📋 Translation Summary:{Style.RESET_ALL}")
        print(f"   Source: {source_lang}")
        print(f"   Targets: {', '.join(target_langs)}")
        print(f"   Sentences: {len(sentences)}")
        print(f"   Batch size: {options.get('batch_size', len(sentences))}")
        
        confirm = input(f"\n{Fore.YELLOW}Proceed with translation? (Y/n): {Style.RESET_ALL}").strip().lower()
        if confirm and confirm.startswith('n'):
            print("Translation cancelled.")
            sys.exit(0)
        
        # Execute translation
        return self.translate(
            source_lang=source_lang,
            target_langs=target_langs,
            sentences=sentences,
            output_file=options.get('output_file'),
            show_progress=True,
            show_terminal=options.get('show_terminal', True),
            simple_format=options.get('simple_format', False),
            download_s3=options.get('download_s3', False),
            batch_size=options.get('batch_size', len(sentences))
        )

    def translate(self, source_lang: str, target_langs: List[str], 
                sentences: List[str], output_file: str = None, 
                show_progress: bool = True, show_terminal: bool = True,
                simple_format: bool = False, download_s3: bool = False,
                batch_size: int = None) -> Dict[str, Any]:
        """Send translation request with progress tracking"""

        # Handle batch processing
        if batch_size and len(sentences) > batch_size:
            return self._translate_in_batches(
                source_lang, target_langs, sentences, output_file,
                show_progress, show_terminal, simple_format, batch_size
            )

        # Estimate processing time
        estimated_time = len(sentences) * len(target_langs) * 0.5

        request_data = {
            'source_language': source_lang,
            'target_languages': target_langs,
            'sentences': sentences
        }

        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-API-Key'] = self.api_key

        print(f"\n{Fore.CYAN}🔄 Starting translation job{Style.RESET_ALL}")
        print(f"📊 {len(sentences)} sentences → {len(target_langs)} languages")
        print(f"⏱️  Estimated time: {estimated_time:.1f} seconds")

        # Progress bar
        progress_bar = None
        if show_progress:
            progress_bar = tqdm(
                total=100, 
                desc="Processing", 
                bar_format="{l_bar}{bar}| {n:.1f}%",
                leave=False
            )
            progress_thread = threading.Thread(
                target=self._animate_progress, 
                args=(progress_bar, estimated_time)
            )
            progress_thread.daemon = True
            progress_thread.start()

        try:
            start_time = time.time()
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

            # Handle response
            result = response.json()
            if response.status_code != 200 or not result.get("success", False):
                print(f"{Fore.RED}❌ Translation failed: {response.status_code}{Style.RESET_ALL}")
                print(result)
                sys.exit(1)

            translation_id = result['translation_id']
            print(f"{Fore.GREEN}✅ Translation job started!{Style.RESET_ALL}")
            print(f"🆔 Translation ID: {translation_id}")
            print(f"⏱️  Actual time: {actual_time:.1f} seconds")

            # --- 🔹 Fetch translations from S3 if missing ---
            translations_data = result.get('translations', {})
            if not translations_data and self.s3_client:
                output_key = result.get('output_location', {}).get('key')
                output_bucket = result.get('output_location', {}).get('bucket', self.output_bucket)

                if output_key:
                    print(f"{Fore.YELLOW}⏳ Waiting for translations in S3...{Style.RESET_ALL}")
                    for _ in range(30):  # wait up to ~30 seconds
                        try:
                            s3_obj = self.s3_client.get_object(Bucket=output_bucket, Key=output_key)
                            content = s3_obj['Body'].read().decode('utf-8')
                            s3_data = json.loads(content)
                            translations_data = s3_data.get('translations', {})
                            if translations_data:
                                break
                        except self.s3_client.exceptions.NoSuchKey:
                            pass
                        time.sleep(1)

            # Normalize translations to dict-of-lists
            if isinstance(translations_data, str):
                try:
                    translations_data = json.loads(translations_data)
                except json.JSONDecodeError:
                    translations_data = {}

            if isinstance(translations_data, dict):
                for lang in target_langs:
                    translations_data.setdefault(lang, [])
            else:
                # Convert list-of-dicts to dict-of-lists
                normalized = {lang: [] for lang in target_langs}
                for sentence_entry in translations_data:
                    for lang in target_langs:
                        normalized[lang].append(sentence_entry.get(lang, ""))
                translations_data = normalized

            # Inject into result for consistency
            result['translations'] = translations_data

            # Display in terminal
            if show_terminal:
                detected_source = result.get('summary', {}).get('source_language', source_lang)
                detected_targets = result.get('summary', {}).get('target_languages', target_langs)
                if simple_format:
                    self._display_translations_simple(sentences, translations_data, detected_source, detected_targets)
                else:
                    self._display_translations_terminal(sentences, translations_data, detected_source, detected_targets)

            # Save to history
            self._save_to_history(result, source_lang, target_langs, len(sentences))

            # Save to file if requested
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"💾 Results saved to {output_file}")

            # Download S3 file if requested
            if download_s3 and self.s3_client and self.output_bucket:
                self._download_translation(result['output_location']['key'])

            return result

        except requests.exceptions.Timeout:
            if progress_bar:
                progress_bar.close()
            print(f"{Fore.RED}❌ Request timeout after {estimated_time * 2:.1f} seconds{Style.RESET_ALL}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            if progress_bar:
                progress_bar.close()
            print(f"{Fore.RED}❌ Network error: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            if progress_bar:
                progress_bar.close()
            print(f"{Fore.RED}❌ Invalid response format: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)


    def _translate_in_batches(self, source_lang: str, target_langs: List[str], 
                            sentences: List[str], output_file: str, 
                            show_progress: bool, show_terminal: bool,
                            simple_format: bool, batch_size: int):
        """Handle batch translation processing"""
        print(f"\n{Fore.CYAN}📦 Processing {len(sentences)} sentences in batches of {batch_size}{Style.RESET_ALL}")
        
        all_results = []
        all_translations = {lang: [] for lang in target_langs}
        
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(sentences) + batch_size - 1) // batch_size
            
            print(f"\n🔄 Processing batch {batch_num}/{total_batches}")
            
            result = self.translate(
                source_lang=source_lang,
                target_langs=target_langs,
                sentences=batch,
                show_progress=show_progress,
                show_terminal=False,  # Don't show individual batch results
                simple_format=simple_format,
                download_s3=False
            )
            
            all_results.append(result)
            
            # Accumulate translations
            if 'translations' in result:
                for lang in target_langs:
                    if lang in result['translations']:
                        all_translations[lang].extend(result['translations'][lang])
            
            # Small delay between batches
            if i + batch_size < len(sentences):
                time.sleep(1)
        
        print(f"\n{Fore.GREEN}✅ All batches completed! Processed {len(sentences)} sentences total.{Style.RESET_ALL}")
        
        # Show final results if requested
        if show_terminal:
            if simple_format:
                self._display_translations_simple(sentences, all_translations, source_lang, target_langs)
            else:
                self._display_translations_terminal(sentences, all_translations, source_lang, target_langs)
        
        # Save combined results if requested
        if output_file:
            combined_result = {
                'success': True,
                'batch_results': all_results,
                'combined_translations': all_translations,
                'summary': {
                    'total_sentences': len(sentences),
                    'total_batches': len(all_results),
                    'source_language': source_lang,
                    'target_languages': target_langs
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(combined_result, f, indent=2, ensure_ascii=False)
            print(f"💾 Combined results saved to {output_file}")
        
        return all_results

    def _display_translations_terminal(self, original_sentences: List[str], 
                                     translations: Dict[str, List[str]], 
                                     source_lang: str, target_langs: List[str]):
        """Display translations in a beautiful terminal format"""
        
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}🌐 TRANSLATION RESULTS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

        # Language flag emojis
        lang_flags = {
            'en': '🇺🇸', 'es': '🇪🇸', 'fr': '🇫🇷', 'de': '🇩🇪', 'it': '🇮🇹',
            'pt': '🇵🇹', 'ru': '🇷🇺', 'zh': '🇨🇳', 'ja': '🇯🇵', 'ko': '🇰🇷',
            'ar': '🇸🇦', 'hi': '🇮🇳', 'tr': '🇹🇷', 'pl': '🇵🇱', 'nl': '🇳🇱'
        }
        
        for i, original in enumerate(original_sentences):
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}📝 Sentence {i+1}:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{Back.BLUE} {source_lang.upper()} {Style.RESET_ALL} {lang_flags.get(source_lang, '🌍')} {original}")
            
            # Display each translation
            colors = [Fore.GREEN, Fore.MAGENTA, Fore.CYAN, Fore.YELLOW, Fore.BLUE]
            for j, lang in enumerate(target_langs):
                if lang in translations and i < len(translations[lang]):
                    translated_text = translations[lang][i]
                    flag = lang_flags.get(lang, '🌍')
                    color = colors[j % len(colors)]
                    
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
                    if isinstance(data, dict):
                        return data.get('sentences', [])
                    elif isinstance(data, list):
                        return data
                else:
                    # Text file - one sentence per line
                    sentences = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
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
    parser = argparse.ArgumentParser(description='Interactive Translation Platform CLI')
    parser.add_argument('file', nargs='?', help='Optional: File to translate')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard and exit')
    parser.add_argument('--test', action='store_true', help='Test API connection')
    parser.add_argument('--status', action='store_true', help='Show configuration status')
    parser.add_argument('--get-status', help='Get status of specific translation')
    parser.add_argument('--list', action='store_true', help='List recent translations')
    parser.add_argument('--show', help='Show translation results from S3')
    parser.add_argument('--version', action='version', version='Translation CLI v2.0')
    
    args = parser.parse_args()
    
    cli = InteractiveTranslationCLI()
    
    # Handle setup mode
    if args.setup:
        cli.setup_wizard()
        return  # Exit after setup, don't proceed to translation
    
    # Handle test connection
    if args.test:
        if cli.api_endpoint and cli.api_key:
            print(f"{Fore.YELLOW}🔍 Testing API connection...{Style.RESET_ALL}")
            if cli._test_connection():
                print(f"{Fore.GREEN}✅ API connection successful{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ API connection failed{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ CLI not configured. Run --setup first{Style.RESET_ALL}")
        return
    
    # Handle status check
    if args.status:
        cli.status()
        return
    
    # Handle get status
    if args.get_status:
        cli.get_translation_status(args.get_status)
        return
    
    # Handle list translations
    if args.list:
        cli.list_translations()
        return
    
    # Handle show translation
    if args.show:
        cli.get_s3_translation(args.show)
        return
    
    # Check configuration before proceeding to translation
    if not cli.check_configuration():
        return
    
    # Run interactive translation
    cli.interactive_translate(args.file)

if __name__ == '__main__':
    main()