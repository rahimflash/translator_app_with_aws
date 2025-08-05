#!/usr/bin/env python3
"""
Translation Platform GUI
A comprehensive GUI application for the translation platform
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import requests
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
import os
import boto3
import boto3.session
from typing import Dict, List, Any, Optional
import queue

class TranslationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Translation Platform")
        self.root.geometry("1200x800")
        
        # Configuration
        self.config_file = Path.home() / '.translation-cli-config.json'
        self.history_file = Path.home() / '.translation-cli-history.json'
        
        # Variables
        self.api_endpoint = tk.StringVar()
        self.api_key = tk.StringVar()
        self.output_bucket = tk.StringVar()
        self.aws_region = tk.StringVar(value="eu-west-1")
        self.source_lang = tk.StringVar(value="en")
        self.batch_size = tk.IntVar(value=25)
        self.show_terminal = tk.BooleanVar(value=True)
        self.save_to_file = tk.BooleanVar(value=False)
        self.download_s3 = tk.BooleanVar(value=False)
        self.output_filename = tk.StringVar(value="translation_results.json")
        
        # Debug mode
        self.debug_mode = os.environ.get('TRANSLATION_DEBUG', '').lower() in ('1', 'true', 'yes')
        
        # Target languages
        self.target_languages = {}
        
        # S3 client
        self.s3_client = None
        
        # Queue for thread communication
        self.queue = queue.Queue()
        
        # Common languages
        self.common_languages = {
            'en': 'English 🇺🇸',
            'es': 'Spanish 🇪🇸',
            'fr': 'French 🇫🇷',
            'de': 'German 🇩🇪',
            'it': 'Italian 🇮🇹',
            'pt': 'Portuguese 🇵🇹',
            'ru': 'Russian 🇷🇺',
            'zh': 'Chinese 🇨🇳',
            'ja': 'Japanese 🇯🇵',
            'ko': 'Korean 🇰🇷',
            'ar': 'Arabic 🇸🇦',
            'hi': 'Hindi 🇮🇳',
            'tr': 'Turkish 🇹🇷',
            'pl': 'Polish 🇵🇱',
            'nl': 'Dutch 🇳🇱'
        }
        
        # Load configuration
        self.load_config()
        
        # Setup UI
        self.setup_styles()
        self.create_widgets()
        
        # Check configuration on startup
        self.root.after(100, self.check_initial_config)
        
        # Start queue processor
        self.process_queue()

    def setup_styles(self):
        """Configure ttk styles for modern look"""
        self.style = ttk.Style()
        
        # Configure colors
        self.colors = {
            'primary': '#2196F3',
            'secondary': '#FFC107',
            'success': '#4CAF50',
            'danger': '#F44336',
            'dark': '#212121',
            'light': '#F5F5F5',
            'white': '#FFFFFF'
        }
        
        # Configure styles
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Success.TLabel', foreground=self.colors['success'])
        self.style.configure('Error.TLabel', foreground=self.colors['danger'])
        self.style.configure('Primary.TButton', font=('Arial', 10, 'bold'))

    def create_widgets(self):
        """Create all GUI widgets"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.translate_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.history_tab = ttk.Frame(self.notebook)
        self.status_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.translate_tab, text='Translate')
        self.notebook.add(self.settings_tab, text='Settings')
        self.notebook.add(self.history_tab, text='History')
        self.notebook.add(self.status_tab, text='Status')
        
        # Setup each tab
        self.setup_translate_tab()
        self.setup_settings_tab()
        self.setup_history_tab()
        self.setup_status_tab()

    def setup_translate_tab(self):
        """Setup the translation interface"""
        # Main container
        main_frame = ttk.Frame(self.translate_tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Translation Service", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create two columns
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Left column - Input
        self.setup_input_section(left_frame)
        
        # Right column - Output and options
        self.setup_output_section(right_frame)

    def setup_input_section(self, parent):
        """Setup input section"""
        # Input section
        input_label = ttk.Label(parent, text="Input Text", style='Heading.TLabel')
        input_label.pack(anchor='w', pady=(0, 5))
        
        # File selection frame
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill='x', pady=(0, 10))
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state='readonly')
        file_entry.pack(side='left', fill='x', expand=True)
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side='left', padx=(5, 0))
        
        clear_file_btn = ttk.Button(file_frame, text="Clear", command=self.clear_file)
        clear_file_btn.pack(side='left', padx=(5, 0))
        
        # Text input
        self.input_text = scrolledtext.ScrolledText(parent, height=15, width=50)
        self.input_text.pack(fill='both', expand=True, pady=(0, 10))
        self.input_text.insert('1.0', "Enter sentences to translate, one per line...")
        self.input_text.bind('<FocusIn>', self.on_input_focus)
        self.input_text.bind('<FocusOut>', self.on_input_blur)
        
        # Language selection
        lang_frame = ttk.Frame(parent)
        lang_frame.pack(fill='x', pady=(10, 0))
        
        # Source language
        source_label = ttk.Label(lang_frame, text="Source Language:")
        source_label.pack(anchor='w')
        
        source_combo = ttk.Combobox(lang_frame, textvariable=self.source_lang, 
                                    values=list(self.common_languages.values()),
                                    width=30)
        source_combo['state'] = 'normal'  # Make it editable
        source_combo.pack(fill='x', pady=(5, 10))
        source_combo.bind('<<ComboboxSelected>>', self.on_source_lang_select)
        
        # Target languages
        target_label = ttk.Label(lang_frame, text="Target Languages:")
        target_label.pack(anchor='w')
        
        # Target language checkboxes in a scrollable frame
        target_container = ttk.Frame(lang_frame)
        target_container.pack(fill='both', expand=True)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(target_container, height=150)
        scrollbar = ttk.Scrollbar(target_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add checkboxes for target languages
        for i, (code, name) in enumerate(self.common_languages.items()):
            # if code != 'en':  # Skip source language initially
            var = tk.BooleanVar()
            self.target_languages[code] = var
            cb = ttk.Checkbutton(scrollable_frame, text=name, variable=var)
            cb.grid(row=i//2, column=i%2, sticky='w', padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Additional target languages entry
        self.additional_langs_var = tk.StringVar()
        ttk.Label(lang_frame, text="Additional Target Languages:").pack(anchor='w')
        additional_lang_entry = ttk.Entry(lang_frame, textvariable=self.additional_langs_var, 
                                         width=30)
        additional_lang_entry.pack(fill='x', pady=(5, 10))
        additional_lang_entry.insert(0, "e.g., it,pt,fr")
        additional_lang_entry.bind('<FocusIn>', lambda e: additional_lang_entry.delete(0, 'end') if additional_lang_entry.get() == "e.g., it,pt,fr" else None)
        additional_lang_entry.bind('<FocusOut>', lambda e: additional_lang_entry.insert(0, "e.g., it,pt,fr") if not additional_lang_entry.get() else None)
        
        # Translate button
        self.translate_btn = ttk.Button(parent, text="Translate", 
                                       command=self.start_translation,
                                       style='Primary.TButton')
        self.translate_btn.pack(pady=(10, 0))

    def setup_output_section(self, parent):
        """Setup output section"""
        # Options section
        options_label = ttk.Label(parent, text="Options", style='Heading.TLabel')
        options_label.pack(anchor='w', pady=(0, 5))
        
        options_frame = ttk.LabelFrame(parent, text="Translation Options", padding="10")
        options_frame.pack(fill='x', pady=(0, 10))
        
        # Batch size
        batch_frame = ttk.Frame(options_frame)
        batch_frame.pack(fill='x', pady=5)
        ttk.Label(batch_frame, text="Batch Size:").pack(side='left')
        ttk.Spinbox(batch_frame, from_=1, to=100, textvariable=self.batch_size, 
                    width=10).pack(side='left', padx=(10, 0))
        
        # Display options
        ttk.Checkbutton(options_frame, text="Show results in output", 
                       variable=self.show_terminal).pack(anchor='w', pady=2)
        
        # File save option
        file_save_frame = ttk.Frame(options_frame)
        file_save_frame.pack(fill='x', pady=5)
        ttk.Checkbutton(file_save_frame, text="Save to file:", 
                       variable=self.save_to_file).pack(side='left')
        ttk.Entry(file_save_frame, textvariable=self.output_filename, 
                 width=30).pack(side='left', padx=(10, 0))
        
        # S3 download option
        # ttk.Checkbutton(options_frame, text="Download from S3", 
        #                variable=self.download_s3).pack(anchor='w', pady=2)
        
        # Progress section
        progress_label = ttk.Label(parent, text="Progress", style='Heading.TLabel')
        progress_label.pack(anchor='w', pady=(10, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(parent, variable=self.progress_var, 
                                           maximum=100, length=300)
        self.progress_bar.pack(fill='x', pady=(0, 5))
        
        self.status_label = ttk.Label(parent, text="Ready")
        self.status_label.pack(anchor='w')
        
        # Output section
        output_label = ttk.Label(parent, text="Translation Results", style='Heading.TLabel')
        output_label.pack(anchor='w', pady=(20, 5))
        
        # Output text with scrollbar
        self.output_text = scrolledtext.ScrolledText(parent, height=15, width=50)
        self.output_text.pack(fill='both', expand=True)
        self.output_text.config(state='disabled')

    def setup_settings_tab(self):
        """Setup settings tab"""
        settings_frame = ttk.Frame(self.settings_tab, padding="20")
        settings_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(settings_frame, text="Configuration Settings", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # API Configuration
        api_frame = ttk.LabelFrame(settings_frame, text="API Configuration", padding="15")
        api_frame.pack(fill='x', pady=(0, 20))
        
        # API Endpoint
        ttk.Label(api_frame, text="API Endpoint:").grid(row=0, column=0, sticky='w', pady=5)
        endpoint_entry = ttk.Entry(api_frame, textvariable=self.api_endpoint, width=50)
        endpoint_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # API Key
        ttk.Label(api_frame, text="API Key:").grid(row=1, column=0, sticky='w', pady=5)
        key_entry = ttk.Entry(api_frame, textvariable=self.api_key, show="*", width=50)
        key_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Show/Hide API Key button
        self.show_key_btn = ttk.Button(api_frame, text="Show", width=10,
                                      command=self.toggle_api_key_visibility)
        self.show_key_btn.grid(row=1, column=2, padx=5)
        
        # AWS Configuration
        aws_frame = ttk.LabelFrame(settings_frame, text="AWS Configuration (Optional)", 
                                  padding="15")
        aws_frame.pack(fill='x', pady=(0, 20))
        
        # S3 Bucket
        ttk.Label(aws_frame, text="S3 Output Bucket:").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(aws_frame, textvariable=self.output_bucket, width=50).grid(
            row=0, column=1, pady=5, padx=(10, 0))
        
        # AWS Region
        ttk.Label(aws_frame, text="AWS Region:").grid(row=1, column=0, sticky='w', pady=5)
        region_combo = ttk.Combobox(aws_frame, textvariable=self.aws_region, width=47,
                                   values=['us-east-1', 'us-west-2', 'eu-west-1', 
                                          'eu-central-1', 'ap-southeast-1'])
        region_combo.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Test Connection", 
                  command=self.test_connection).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Test S3 Access", 
                  command=self.test_s3_access).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Save Configuration", 
                  command=self.save_config).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Configuration", 
                  command=self.load_config).pack(side='left', padx=5)
        
        # Status
        self.config_status_label = ttk.Label(settings_frame, text="")
        self.config_status_label.pack()
        
        # AWS Credentials Help
        help_frame = ttk.LabelFrame(settings_frame, text="AWS Credentials Help", padding="15")
        help_frame.pack(fill='x', pady=(20, 0))
        
        help_text = """To use S3 features, AWS credentials must be configured on your system:

Option 1: AWS CLI Configuration
   Run: aws configure

Option 2: Environment Variables
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   
Required S3 Permissions:
   - s3:GetObject on the output bucket
   - s3:ListBucket on the output bucket"""
        
        help_label = ttk.Label(help_frame, text=help_text, justify='left')
        help_label.pack(anchor='w')

    def setup_history_tab(self):
        """Setup history tab"""
        history_frame = ttk.Frame(self.history_tab, padding="20")
        history_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(history_frame, text="Translation History", 
                               style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Controls
        control_frame = ttk.Frame(history_frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Button(control_frame, text="Refresh", 
                  command=self.refresh_history).pack(side='left')
        ttk.Button(control_frame, text="Clear History", 
                  command=self.clear_history).pack(side='left', padx=(10, 0))
        
        # History treeview
        columns = ('ID', 'Date', 'Languages', 'Sentences', 'Status')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings')
        
        # Configure columns
        self.history_tree.heading('ID', text='Translation ID')
        self.history_tree.heading('Date', text='Date/Time')
        self.history_tree.heading('Languages', text='Languages')
        self.history_tree.heading('Sentences', text='Sentences')
        self.history_tree.heading('Status', text='Status')
        
        self.history_tree.column('ID', width=150)
        self.history_tree.column('Date', width=200)
        self.history_tree.column('Languages', width=200)
        self.history_tree.column('Sentences', width=100)
        self.history_tree.column('Status', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', 
                                 command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind double-click
        self.history_tree.bind('<Double-Button-1>', self.on_history_double_click)
        
        # Load history
        self.refresh_history()

    def setup_status_tab(self):
        """Setup status tab"""
        status_frame = ttk.Frame(self.status_tab, padding="20")
        status_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(status_frame, text="System Status", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Status info frame
        info_frame = ttk.LabelFrame(status_frame, text="Configuration Status", padding="15")
        info_frame.pack(fill='x', pady=(0, 20))
        
        self.status_info = tk.Text(info_frame, height=10, width=60)
        self.status_info.pack()
        
        # Translation lookup
        lookup_frame = ttk.LabelFrame(status_frame, text="Translation Lookup", padding="15")
        lookup_frame.pack(fill='x')
        
        ttk.Label(lookup_frame, text="Translation ID:").pack(anchor='w')
        
        id_frame = ttk.Frame(lookup_frame)
        id_frame.pack(fill='x', pady=(5, 10))
        
        self.lookup_id_var = tk.StringVar()
        ttk.Entry(id_frame, textvariable=self.lookup_id_var, width=40).pack(side='left')
        ttk.Button(id_frame, text="Lookup", 
                  command=self.lookup_translation).pack(side='left', padx=(10, 0))
        
        # Lookup results
        self.lookup_results = scrolledtext.ScrolledText(lookup_frame, height=10)
        self.lookup_results.pack(fill='both', expand=True)
        
        # Update status
        self.update_status_info()

    def browse_file(self):
        """Browse for input file"""
        filename = filedialog.askopenfilename(
            title="Select input file",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), 
                      ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            self.load_file_content(filename)

    def clear_file(self):
        """Clear file selection"""
        self.file_path_var.set("")
        self.input_text.delete('1.0', tk.END)
        self.input_text.insert('1.0', "Enter sentences to translate, one per line...")

    def load_file_content(self, filepath):
        """Load content from file"""
        try:
            sentences, source_lang = self.detect_file_content(filepath)
            if sentences:
                self.input_text.delete('1.0', tk.END)
                self.input_text.insert('1.0', '\n'.join(sentences))
                
                if source_lang:
                    # Update source language combo
                    for code, name in self.common_languages.items():
                        if code == source_lang:
                            self.source_lang.set(name)
                            break
                
                self.update_status(f"Loaded {len(sentences)} sentences from file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def detect_file_content(self, filepath):
        """Detect and extract content from files"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.endswith('.json'):
                    data = json.load(f)
                    
                    if isinstance(data, dict):
                        source_lang = data.get('source_language')
                        sentences = data.get('sentences', [])
                        
                        if not sentences and 'sentences' not in data:
                            sentences = [str(data)]
                        
                        return sentences, source_lang
                    
                    elif isinstance(data, list):
                        return data, None
                    
                    else:
                        return [str(data)], None
                else:
                    sentences = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            sentences.append(line)
                    return sentences, None
                    
        except Exception as e:
            raise e

    def on_input_focus(self, event):
        """Handle input text focus"""
        if self.input_text.get('1.0', 'end-1c') == "Enter sentences to translate, one per line...":
            self.input_text.delete('1.0', tk.END)

    def on_input_blur(self, event):
        """Handle input text blur"""
        if not self.input_text.get('1.0', 'end-1c').strip():
            self.input_text.insert('1.0', "Enter sentences to translate, one per line...")

    def on_source_lang_select(self, event):
        """Handle source language selection"""
        # Update target language checkboxes to exclude source language
        selected = self.source_lang.get()
        selected_code = None
        
        for code, name in self.common_languages.items():
            if name == selected:
                selected_code = code
                break

    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        key_entry = None
        for child in self.settings_tab.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.LabelFrame) and "API" in subchild['text']:
                        for widget in subchild.winfo_children():
                            if isinstance(widget, ttk.Entry) and widget['textvariable'] == str(self.api_key):
                                key_entry = widget
                                break
        
        if key_entry:
            if key_entry['show'] == "*":
                key_entry['show'] = ""
                self.show_key_btn['text'] = "Hide"
            else:
                key_entry['show'] = "*"
                self.show_key_btn['text'] = "Show"

    def start_translation(self):
        """Start the translation process"""
        # Validate inputs
        sentences = self.get_input_sentences()
        if not sentences:
            messagebox.showwarning("Warning", "Please enter sentences to translate")
            return
        
        target_langs = self.get_selected_target_languages()
        if not target_langs:
            messagebox.showwarning("Warning", "Please select at least one target language")
            return
        
        # Get source language code - either from dropdown or typed value
        source_lang = self.source_lang.get()
        source_code = None

        # First check if it matches a common language name
        for code, name in self.common_languages.items():
            if name == source_lang:
                source_code = code
                break

        # If not found, use the value directly (assuming it's a language code)
        if not source_code and source_lang:
            source_code = source_lang.lower().strip()
        
        if not source_code:
            messagebox.showwarning("Warning", "Please select or enter a source language")
            return
        
        # Disable translate button
        self.translate_btn.config(state='disabled')
        
        # Clear output
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', tk.END)
        self.output_text.config(state='disabled')
        
        # Start translation in thread
        thread = threading.Thread(
            target=self.run_translation,
            args=(source_code, target_langs, sentences)
        )
        thread.daemon = True
        thread.start()

    def get_input_sentences(self):
        """Get sentences from input text"""
        text = self.input_text.get('1.0', 'end-1c')
        if text == "Enter sentences to translate, one per line...":
            return []
        
        sentences = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                sentences.append(line)
        
        return sentences

    def get_selected_target_languages(self):
        """Get selected target languages"""
        selected = []
        # Get from checkboxes
        for code, var in self.target_languages.items():
            if var.get():
                selected.append(code)
        
        # Get from additional languages entry
        additional = self.additional_langs_var.get().strip()
        if additional and additional != "e.g., it,pt,fr":
            # Split by commas and clean up
            for lang in additional.split(','):
                lang = lang.strip().lower()
                if lang and lang not in selected:
                    selected.append(lang)
        
        return selected

    def run_translation(self, source_lang, target_langs, sentences):
        """Run translation in thread"""
        try:
            # Update status
            self.queue.put(('status', 'Starting translation...'))
            self.queue.put(('progress', 0))
            
            # Prepare request
            request_data = {
                'source_language': source_lang,
                'target_languages': target_langs,
                'sentences': sentences
            }
            
            headers = {'Content-Type': 'application/json'}
            if self.api_key.get():
                headers['X-API-Key'] = self.api_key.get()
            
            # Estimate time
            estimated_time = len(sentences) * len(target_langs) * 0.5
            self.queue.put(('status', f'Processing {len(sentences)} sentences... Estimated time: {estimated_time:.1f}s'))
            
            # Make request
            start_time = time.time()
            
            # Simulate progress
            progress_thread = threading.Thread(
                target=self.simulate_progress,
                args=(estimated_time,)
            )
            progress_thread.daemon = True
            progress_thread.start()
            
            response = requests.post(
                self.api_endpoint.get(),
                headers=headers,
                json=request_data,
                timeout=max(300, estimated_time * 2)
            )
            
            elapsed_time = time.time() - start_time
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                
                # Check if translations are in the response
                translations_data = result.get('translations', {})
                
                # If no translations and S3 is configured, poll S3
                if not translations_data and self.s3_client:
                    output_key = result.get('output_location', {}).get('key')
                    # Extract bucket from URL if not directly provided
                    output_url = result.get('output_location', {}).get('url', '')
                    output_bucket = result.get('output_location', {}).get('bucket')
                    
                    # Try to extract bucket from S3 URL format
                    if not output_bucket and output_url.startswith('s3://'):
                        # URL format: s3://bucket-name/path/to/file
                        parts = output_url.replace('s3://', '').split('/', 1)
                        if parts:
                            output_bucket = parts[0]
                    
                    # If still no bucket, use configured bucket
                    if not output_bucket:
                        output_bucket = self.output_bucket.get()
                    
                    if output_key and output_bucket:
                        self.queue.put(('status', f'⏳ Waiting for translations in S3 (bucket: {output_bucket})...'))
                        
                        # Show polling info in output
                        self.queue.put(('polling_info', {
                            'bucket': output_bucket,
                            'key': output_key,
                            'message': 'Polling S3 for translations. This may take up to 60 seconds...'
                        }))
                        
                        # Poll S3 for up to 60 seconds
                        max_attempts = 60
                        found = False
                        
                        for attempt in range(max_attempts):
                            try:
                                # Update progress and status
                                progress = 50 + (attempt / max_attempts * 45)  # 50-95%
                                self.queue.put(('progress', progress))
                                
                                if attempt % 10 == 0:  # Update status every 10 attempts
                                    self.queue.put(('status', f'⏳ Polling S3... (attempt {attempt + 1}/{max_attempts})'))
                                
                                # Try to get the file from S3
                                s3_obj = self.s3_client.get_object(Bucket=output_bucket, Key=output_key)
                                content = s3_obj['Body'].read().decode('utf-8')
                                s3_data = json.loads(content)
                                translations_data = s3_data.get('translations', {})
                                
                                if translations_data:
                                    # Found translations!
                                    result['translations'] = translations_data
                                    self.queue.put(('status', f'✅ Translations retrieved from S3 (attempt {attempt + 1})'))
                                    found = True
                                    break
                                else:
                                    # File exists but no translations yet
                                    if attempt == 0:
                                        self.queue.put(('status', '📄 File found but translations not ready yet...'))
                                    
                            except self.s3_client.exceptions.NoSuchKey:
                                # File doesn't exist yet, wait and retry
                                if attempt % 10 == 0:
                                    self.queue.put(('status', f'⏳ File not yet in S3, waiting... (attempt {attempt + 1}/{max_attempts})'))
                            except Exception as e:
                                if attempt == 0 or self.debug_mode:  # Log error once or always in debug
                                    self.queue.put(('status', f'S3 polling error: {str(e)}'))
                                    # Log more details for debugging
                                    print(f"S3 Polling Error Details:")
                                    print(f"  Bucket: {output_bucket}")
                                    print(f"  Key: {output_key}")
                                    print(f"  Error: {str(e)}")
                                    print(f"  Error Type: {type(e).__name__}")
                                    if self.debug_mode:
                                        import traceback
                                        print(f"  Traceback:\n{traceback.format_exc()}")
                            
                            # Wait before next attempt
                            time.sleep(1)
                        
                        if not found:
                            # Timeout after all attempts
                            self.queue.put(('status', '⚠️ Timeout waiting for S3 translations (60s elapsed)'))
                            
                            # Suggest bucket update if there's a mismatch
                            configured_bucket = self.output_bucket.get()
                            if configured_bucket and configured_bucket != output_bucket:
                                self.queue.put(('bucket_mismatch', {
                                    'configured': configured_bucket,
                                    'actual': output_bucket
                                }))
                
                self.queue.put(('progress', 100))
                self.queue.put(('status', f'Translation completed in {elapsed_time:.1f}s'))
                self.queue.put(('result', result))
                
                # Save to history
                self.save_to_history(result, source_lang, target_langs, len(sentences))
                
                # Save to file if requested
                if self.save_to_file.get():
                    self.save_results_to_file(result)
                
            else:
                error_msg = f"Translation failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f"\n{error_data.get('error', {}).get('message', '')}"
                except:
                    pass
                self.queue.put(('error', error_msg))
                
        except Exception as e:
            self.queue.put(('error', f"Translation error: {str(e)}"))
        finally:
            self.queue.put(('complete', None))

    def simulate_progress(self, estimated_time):
        """Simulate progress bar movement"""
        steps = 100  # Only go to 50% during initial request
        sleep_time = estimated_time / steps
        
        for i in range(steps):
            time.sleep(sleep_time)
            self.queue.put(('progress', i))

    def display_results(self, result):
        """Display translation results"""
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', tk.END)
        
        # Header
        self.output_text.insert(tk.END, "="*60 + "\n", 'header')
        self.output_text.insert(tk.END, "🌐 TRANSLATION RESULTS\n", 'title')
        self.output_text.insert(tk.END, "="*60 + "\n\n", 'header')
        
        # Get translations
        translations = result.get('translations', {})
        sentences = self.get_input_sentences()
        
        # If translations are still empty, show a message
        if not translations:
            self.output_text.insert(tk.END, "⚠️ No translations found in response\n", 'error')
            self.output_text.insert(tk.END, f"Translation ID: {result.get('translation_id', 'N/A')}\n", 'info')
            
            # Show S3 location if available
            output_location = result.get('output_location', {})
            if output_location:
                self.output_text.insert(tk.END, f"\nOutput Location:\n", 'info')
                self.output_text.insert(tk.END, f"  Bucket: {output_location.get('bucket', 'N/A')}\n", 'info')
                self.output_text.insert(tk.END, f"  Key: {output_location.get('key', 'N/A')}\n", 'info')
                self.output_text.insert(tk.END, f"  URL: {output_location.get('url', 'N/A')}\n", 'info')
                
                self.output_text.insert(tk.END, "\n💡 Translations may still be processing. Check S3 or History tab later.\n", 'info')
                
                # Add a retry button if S3 is configured
                if self.s3_client and output_location.get('key'):
                    self.output_text.insert(tk.END, "\n")
                    retry_btn = ttk.Button(self.output_text, text="🔄 Retry Fetching from S3",
                                         command=lambda: self.retry_fetch_translations(result))
                    self.output_text.window_create(tk.END, window=retry_btn)
                    
                    self.output_text.insert(tk.END, "  ")
                    
                    # Add copy S3 command button
                    copy_btn = ttk.Button(self.output_text, text="📋 Copy S3 Command",
                                        command=lambda: self.copy_s3_command(output_location))
                    self.output_text.window_create(tk.END, window=copy_btn)
                    self.output_text.insert(tk.END, "\n")
            
            self.output_text.config(state='disabled')
            return
        
        # Display each sentence and translations
        for i, sentence in enumerate(sentences):
            self.output_text.insert(tk.END, f"📝 Sentence {i+1}:\n", 'sentence_header')
            self.output_text.insert(tk.END, f"[{result.get('summary', {}).get('source_language', 'SOURCE')}] {sentence}\n", 'source')
            
            for lang in result.get('summary', {}).get('target_languages', []):
                if lang in translations and i < len(translations[lang]):
                    translated = translations[lang][i]
                    flag = self.get_language_flag(lang)
                    self.output_text.insert(tk.END, f"[{lang.upper()}] {flag} {translated}\n", 'translation')
                else:
                    self.output_text.insert(tk.END, f"[{lang.upper()}] ❌ Translation not available\n", 'error')
            
            if i < len(sentences) - 1:
                self.output_text.insert(tk.END, "-"*40 + "\n", 'separator')
        
        # Summary
        self.output_text.insert(tk.END, "\n" + "="*60 + "\n", 'header')
        self.output_text.insert(tk.END, f"📊 Summary: {len(sentences)} sentences translated\n", 'summary')
        self.output_text.insert(tk.END, f"🆔 Translation ID: {result.get('translation_id', 'N/A')}\n", 'summary')
        
        # Configure tags for styling
        self.output_text.tag_config('header', foreground='blue', font=('Courier', 10))
        self.output_text.tag_config('title', foreground='blue', font=('Arial', 14, 'bold'))
        self.output_text.tag_config('sentence_header', foreground='orange', font=('Arial', 11, 'bold'))
        self.output_text.tag_config('source', foreground='black', font=('Arial', 10))
        self.output_text.tag_config('translation', foreground='green', font=('Arial', 10))
        self.output_text.tag_config('error', foreground='red', font=('Arial', 10))
        self.output_text.tag_config('info', foreground='gray', font=('Arial', 10, 'italic'))
        self.output_text.tag_config('separator', foreground='gray')
        self.output_text.tag_config('summary', foreground='blue', font=('Arial', 10, 'italic'))
        
        self.output_text.config(state='disabled')

    def get_language_flag(self, code):
        """Get flag emoji for language code"""
        flags = {
            'en': '🇺🇸', 'es': '🇪🇸', 'fr': '🇫🇷', 'de': '🇩🇪', 'it': '🇮🇹',
            'pt': '🇵🇹', 'ru': '🇷🇺', 'zh': '🇨🇳', 'ja': '🇯🇵', 'ko': '🇰🇷',
            'ar': '🇸🇦', 'hi': '🇮🇳', 'tr': '🇹🇷', 'pl': '🇵🇱', 'nl': '🇳🇱'
        }
        return flags.get(code, '🌍')

    def save_results_to_file(self, result):
        """Save results to file"""
        try:
            filename = self.output_filename.get()
            if not filename:
                filename = "translation_results.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.queue.put(('status', f'Results saved to {filename}'))
        except Exception as e:
            self.queue.put(('error', f'Failed to save file: {str(e)}'))

    def fetch_from_s3(self, key):
        """Fetch translation from S3"""
        if not self.s3_client or not self.output_bucket.get():
            return None
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.output_bucket.get(),
                Key=key
            )
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except Exception as e:
            print(f"S3 fetch error: {str(e)}")
            return None

    def save_to_history(self, result, source_lang, target_langs, sentence_count):
        """Save translation to history"""
        try:
            history = self.load_history()
            
            # Extract bucket name from output location
            output_bucket = None
            output_location = result.get('output_location', {})
            if output_location:
                output_bucket = output_location.get('bucket')
                if not output_bucket:
                    # Try to extract from URL
                    url = output_location.get('url', '')
                    if url.startswith('s3://'):
                        parts = url.replace('s3://', '').split('/', 1)
                        if parts:
                            output_bucket = parts[0]
            
            record = {
                'translation_id': result.get('translation_id'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source_lang': source_lang,
                'target_langs': target_langs,
                'sentence_count': sentence_count,
                'output_location': output_location.get('url'),
                's3_key': output_location.get('key'),
                'output_bucket': output_bucket  # Store bucket for future use
            }
            
            history.append(record)
            
            # Keep only last 100 records
            if len(history) > 100:
                history = history[-100:]
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save to history: {str(e)}")

    def load_history(self):
        """Load translation history"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def refresh_history(self):
        """Refresh history display"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Load history
        history = self.load_history()
        
        # Add items (most recent first)
        for record in reversed(history[-50:]):  # Show last 50
            self.history_tree.insert('', 'end', values=(
                record.get('translation_id', 'Unknown')[:8] + '...',
                record.get('timestamp', 'Unknown'),
                f"{record.get('source_lang', '?')} → {', '.join(record.get('target_langs', []))}",
                record.get('sentence_count', 0),
                'Completed'
            ))

    def clear_history(self):
        """Clear translation history"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all history?"):
            try:
                with open(self.history_file, 'w') as f:
                    json.dump([], f)
                self.refresh_history()
                messagebox.showinfo("Success", "History cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {str(e)}")

    def on_history_double_click(self, event):
        """Handle double-click on history item"""
        selection = self.history_tree.selection()
        if selection:
            item = self.history_tree.item(selection[0])
            translation_id = item['values'][0].replace('...', '')
            
            # Find full ID in history
            history = self.load_history()
            for record in history:
                if record.get('translation_id', '').startswith(translation_id):
                    self.show_translation_details(record)
                    break

    def show_translation_details(self, record):
        """Show details of a translation"""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Translation Details - {record.get('translation_id', 'Unknown')[:8]}")
        details_window.geometry("700x500")
        
        # Create text widget
        text_widget = scrolledtext.ScrolledText(details_window, wrap=tk.WORD)
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Display details
        text_widget.insert(tk.END, "Translation Details\n", 'title')
        text_widget.insert(tk.END, "="*50 + "\n\n")
        
        text_widget.insert(tk.END, f"Translation ID: {record.get('translation_id', 'Unknown')}\n")
        text_widget.insert(tk.END, f"Timestamp: {record.get('timestamp', 'Unknown')}\n")
        text_widget.insert(tk.END, f"Source Language: {record.get('source_lang', 'Unknown')}\n")
        text_widget.insert(tk.END, f"Target Languages: {', '.join(record.get('target_langs', []))}\n")
        text_widget.insert(tk.END, f"Sentence Count: {record.get('sentence_count', 0)}\n")
        text_widget.insert(tk.END, f"Output Location: {record.get('output_location', 'N/A')}\n")
        text_widget.insert(tk.END, f"S3 Key: {record.get('s3_key', 'N/A')}\n")
        
        # Style tags
        text_widget.tag_config('title', font=('Arial', 12, 'bold'))
        
        # Buttons
        button_frame = ttk.Frame(details_window)
        button_frame.pack(pady=10)
        
        if record.get('s3_key') and self.s3_client:
            ttk.Button(button_frame, text="Download from S3",
                      command=lambda: self.download_from_s3(record)).pack(side='left', padx=5)
            
            ttk.Button(button_frame, text="View Translations",
                      command=lambda: self.view_translations_from_s3(record, details_window)).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Close",
                  command=details_window.destroy).pack(side='left', padx=5)

    def view_translations_from_s3(self, record, parent_window):
        """Fetch and display translations from S3"""
        if not self.s3_client:
            messagebox.showerror("Error", "S3 not configured")
            return
        
        # Get bucket name - try multiple sources
        bucket = self.output_bucket.get()
        
        # Check if bucket is stored in the record
        if 'output_bucket' in record:
            bucket = record['output_bucket']
        elif 'output_location' in record:
            # Try to extract from URL
            url = record.get('output_location', '')
            if url.startswith('s3://'):
                parts = url.replace('s3://', '').split('/', 1)
                if parts:
                    bucket = parts[0]
        
        if not bucket:
            messagebox.showerror("Error", "No S3 bucket configured or found in record")
            return
        
        try:
            key = record.get('s3_key')
            if not key:
                messagebox.showerror("Error", "No S3 key found")
                return
            
            # Show loading message
            loading_window = tk.Toplevel(parent_window)
            loading_window.title("Loading...")
            loading_window.geometry("300x100")
            loading_label = ttk.Label(loading_window, text="Fetching translations from S3...")
            loading_label.pack(expand=True)
            loading_window.update()
            
            # Fetch from S3
            response = self.s3_client.get_object(
                Bucket=bucket,
                Key=key
            )
            content = response['Body'].read().decode('utf-8')
            translation_data = json.loads(content)
            
            loading_window.destroy()
            
            # Create new window to show translations
            trans_window = tk.Toplevel(parent_window)
            trans_window.title(f"Translations - {record.get('translation_id', 'Unknown')[:8]}")
            trans_window.geometry("800x600")
            
            # Text widget for translations
            trans_text = scrolledtext.ScrolledText(trans_window, wrap=tk.WORD)
            trans_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Display translations
            trans_text.insert(tk.END, "🌐 TRANSLATION RESULTS\n", 'title')
            trans_text.insert(tk.END, "="*60 + "\n\n", 'header')
            
            translations = translation_data.get('translations', {})
            if translations:
                # Try to determine sentence count
                first_lang = list(translations.keys())[0] if translations else None
                sentence_count = len(translations.get(first_lang, [])) if first_lang else 0
                
                for i in range(sentence_count):
                    trans_text.insert(tk.END, f"📝 Sentence {i+1}:\n", 'sentence_header')
                    
                    for lang, trans_list in translations.items():
                        if i < len(trans_list):
                            flag = self.get_language_flag(lang)
                            trans_text.insert(tk.END, f"[{lang.upper()}] {flag} {trans_list[i]}\n", 'translation')
                    
                    if i < sentence_count - 1:
                        trans_text.insert(tk.END, "-"*40 + "\n", 'separator')
                
                trans_text.insert(tk.END, f"\n📊 Total: {sentence_count} sentences\n", 'summary')
            else:
                trans_text.insert(tk.END, "No translations found in the file.\n", 'error')
            
            # Style tags
            trans_text.tag_config('title', font=('Arial', 14, 'bold'), foreground='blue')
            trans_text.tag_config('header', foreground='blue')
            trans_text.tag_config('sentence_header', font=('Arial', 11, 'bold'), foreground='orange')
            trans_text.tag_config('translation', foreground='green')
            trans_text.tag_config('separator', foreground='gray')
            trans_text.tag_config('summary', font=('Arial', 10, 'italic'), foreground='blue')
            trans_text.tag_config('error', foreground='red')
            
            # Close button
            ttk.Button(trans_window, text="Close", 
                      command=trans_window.destroy).pack(pady=10)
            
        except Exception as e:
            if 'loading_window' in locals():
                loading_window.destroy()
            messagebox.showerror("Error", f"Failed to fetch translations: {str(e)}")

    def download_from_s3(self, record):
        """Download translation from S3"""
        if not self.s3_client:
            messagebox.showerror("Error", "S3 not configured")
            return
        
        # Get bucket name - try multiple sources
        bucket = self.output_bucket.get()
        
        # Check if bucket is stored in the record
        if 'output_bucket' in record:
            bucket = record['output_bucket']
        elif 'output_location' in record:
            # Try to extract from URL
            url = record.get('output_location', '')
            if url.startswith('s3://'):
                parts = url.replace('s3://', '').split('/', 1)
                if parts:
                    bucket = parts[0]
        
        if not bucket:
            messagebox.showerror("Error", "No S3 bucket configured or found in record")
            return
        
        try:
            key = record.get('s3_key')
            if not key:
                messagebox.showerror("Error", "No S3 key found")
                return
            
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                self.s3_client.download_file(
                    bucket,
                    key,
                    filename
                )
                messagebox.showinfo("Success", f"Downloaded to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {str(e)}")

    def test_connection(self):
        """Test API connection"""
        self.config_status_label.config(text="Testing connection...", style='')
        self.root.update()
        
        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key.get():
                headers['X-API-Key'] = self.api_key.get()
            
            test_payload = {
                'source_language': 'en',
                'target_languages': ['es'],
                'sentences': ['test']
            }
            
            response = requests.post(
                self.api_endpoint.get(),
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.config_status_label.config(
                    text="✅ Connection successful!",
                    style='Success.TLabel'
                )
            elif response.status_code == 400:
                # Check if it's a validation error (which means API is working)
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', '')
                    
                    good_errors = [
                        'Missing required field',
                        'Source language must be',
                        'Target languages must be',
                        'Sentences must be',
                        'Maximum',
                        'validation'
                    ]
                    
                    if any(good_error in error_message for good_error in good_errors):
                        self.config_status_label.config(
                            text="✅ Connection successful! (API validation working)",
                            style='Success.TLabel'
                        )
                    else:
                        self.config_status_label.config(
                            text=f"❌ Connection failed: {error_message}",
                            style='Error.TLabel'
                        )
                except:
                    self.config_status_label.config(
                        text=f"❌ Connection failed: {response.status_code}",
                        style='Error.TLabel'
                    )
            else:
                self.config_status_label.config(
                    text=f"❌ Connection failed: {response.status_code}",
                    style='Error.TLabel'
                )
                
        except Exception as e:
            self.config_status_label.config(
                text=f"❌ Connection error: {str(e)}",
                style='Error.TLabel'
            )

    def test_s3_access(self):
        """Test S3 access"""
        if not self.output_bucket.get():
            self.config_status_label.config(
                text="❌ Please enter an S3 bucket name first",
                style='Error.TLabel'
            )
            return
        
        if not self.aws_region.get():
            self.config_status_label.config(
                text="❌ Please select an AWS region first",
                style='Error.TLabel'
            )
            return
        
        self.config_status_label.config(text="Testing S3 access...", style='')
        self.root.update()
        
        # Initialize S3 client if not already done
        if not self.s3_client:
            self.init_s3_client()
        
        if not self.s3_client:
            self.config_status_label.config(
                text="❌ Failed to initialize S3 client. Check AWS credentials.",
                style='Error.TLabel'
            )
            return
        
        try:
            # Try to list objects in the bucket
            response = self.s3_client.list_objects_v2(
                Bucket=self.output_bucket.get(),
                MaxKeys=1
            )
            
            # Try to check if we can read a test object
            test_key = "translations/test-access.json"
            can_read = False
            
            try:
                self.s3_client.head_object(
                    Bucket=self.output_bucket.get(),
                    Key=test_key
                )
                can_read = True
            except self.s3_client.exceptions.NoSuchKey:
                # This is fine, the test file doesn't exist
                can_read = True  # We can still read, just no file
            except Exception:
                can_read = False
            
            if can_read:
                self.config_status_label.config(
                    text=f"✅ S3 access successful! Bucket '{self.output_bucket.get()}' is accessible.",
                    style='Success.TLabel'
                )
            else:
                self.config_status_label.config(
                    text=f"⚠️ Can list bucket '{self.output_bucket.get()}' but may have limited read permissions",
                    style='Error.TLabel'
                )
                
        except self.s3_client.exceptions.NoSuchBucket:
            self.config_status_label.config(
                text=f"❌ Bucket '{self.output_bucket.get()}' does not exist",
                style='Error.TLabel'
            )
        except Exception as e:
            error_msg = str(e)
            if 'AccessDenied' in error_msg:
                self.config_status_label.config(
                    text=f"❌ Access denied to bucket '{self.output_bucket.get()}'. Check permissions.",
                    style='Error.TLabel'
                )
            elif 'InvalidAccessKeyId' in error_msg:
                self.config_status_label.config(
                    text="❌ Invalid AWS access key. Check AWS credentials.",
                    style='Error.TLabel'
                )
            elif 'SignatureDoesNotMatch' in error_msg:
                self.config_status_label.config(
                    text="❌ Invalid AWS secret key. Check AWS credentials.",
                    style='Error.TLabel'
                )
            else:
                self.config_status_label.config(
                    text=f"❌ S3 access error: {error_msg}",
                    style='Error.TLabel'
                )

    def save_config(self):
        """Save configuration"""
        try:
            config = {
                'api_endpoint': self.api_endpoint.get(),
                'api_key': self.api_key.get(),
                'output_bucket': self.output_bucket.get(),
                'aws_region': self.aws_region.get(),
                'configured_at': datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Reinitialize S3 client
            self.init_s3_client()
            
            # Test S3 access if configured
            s3_status = ""
            if self.s3_client and self.output_bucket.get():
                try:
                    # Try to list objects to test access
                    self.s3_client.list_objects_v2(
                        Bucket=self.output_bucket.get(),
                        MaxKeys=1
                    )
                    s3_status = " S3 access verified!"
                except Exception as e:
                    s3_status = f" (S3 access error: {str(e)})"
                    print(f"S3 Access Test Failed: {str(e)}")
            
            self.config_status_label.config(
                text=f"✅ Configuration saved successfully!{s3_status}",
                style='Success.TLabel'
            )
            
            # Update status info
            self.update_status_info()
            
        except Exception as e:
            self.config_status_label.config(
                text=f"❌ Failed to save: {str(e)}",
                style='Error.TLabel'
            )

    def load_config(self):
        """Load configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_endpoint.set(config.get('api_endpoint', ''))
                    self.api_key.set(config.get('api_key', ''))
                    self.output_bucket.set(config.get('output_bucket', ''))
                    self.aws_region.set(config.get('aws_region', 'eu-west-1'))
                
                # Initialize S3 client
                self.init_s3_client()
                
                if hasattr(self, 'config_status_label'):
                    self.config_status_label.config(
                        text="✅ Configuration loaded",
                        style='Success.TLabel'
                    )
                    
            except Exception as e:
                print(f"Failed to load config: {str(e)}")

    def init_s3_client(self):
        """Initialize S3 client"""
        if self.output_bucket.get() and self.aws_region.get():
            try:
                # Configure with increased timeout for larger files
                config = boto3.session.Config(
                    read_timeout=300,
                    retries={'max_attempts': 3}
                )
                self.s3_client = boto3.client('s3', 
                                            region_name=self.aws_region.get(),
                                            config=config)
            except:
                self.s3_client = None

    def update_status_info(self):
        """Update status information"""
        self.status_info.delete('1.0', tk.END)
        
        self.status_info.insert(tk.END, "Configuration Status:\n", 'bold')
        self.status_info.insert(tk.END, "-" * 50 + "\n\n")
        
        self.status_info.insert(tk.END, f"API Endpoint: {self.api_endpoint.get() or 'Not configured'}\n")
        self.status_info.insert(tk.END, f"API Key: {'Configured' if self.api_key.get() else 'Not configured'}\n")
        self.status_info.insert(tk.END, f"Output Bucket: {self.output_bucket.get() or 'Not configured'}\n")
        self.status_info.insert(tk.END, f"AWS Region: {self.aws_region.get() or 'Not configured'}\n")
        self.status_info.insert(tk.END, f"Config File: {self.config_file}\n")
        self.status_info.insert(tk.END, f"History File: {self.history_file}\n")
        self.status_info.insert(tk.END, f"S3 Access: {'Available' if self.s3_client else 'Not available'}\n")
        
        # Test connection status
        if self.api_endpoint.get():
            self.status_info.insert(tk.END, "\nTesting API connection...\n")
            self.root.after(100, self.test_status_connection)
        
        self.status_info.tag_config('bold', font=('Arial', 10, 'bold'))

    def test_status_connection(self):
        """Test connection for status display"""
        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key.get():
                headers['X-API-Key'] = self.api_key.get()
            
            test_payload = {
                'source_language': 'en',
                'target_languages': ['es'],
                'sentences': ['test']
            }
            
            response = requests.post(
                self.api_endpoint.get(),
                headers=headers,
                json=test_payload,
                timeout=5
            )
            
            if response.status_code in [200, 400]:
                self.status_info.insert(tk.END, "API Status: 🟢 Connected\n", 'success')
            else:
                self.status_info.insert(tk.END, "API Status: 🔴 Connection failed\n", 'error')
                
        except:
            self.status_info.insert(tk.END, "API Status: 🔴 Connection failed\n", 'error')
        
        self.status_info.tag_config('success', foreground='green')
        self.status_info.tag_config('error', foreground='red')

    def lookup_translation(self):
        """Lookup translation by ID"""
        translation_id = self.lookup_id_var.get().strip()
        if not translation_id:
            messagebox.showwarning("Warning", "Please enter a translation ID")
            return
        
        # Clear previous results
        self.lookup_results.delete('1.0', tk.END)
        
        # Search in history
        history = self.load_history()
        found = False
        
        for record in history:
            if record.get('translation_id', '').startswith(translation_id):
                found = True
                self.lookup_results.insert(tk.END, "Translation Found!\n", 'title')
                self.lookup_results.insert(tk.END, "="*50 + "\n\n")
                
                self.lookup_results.insert(tk.END, f"Translation ID: {record.get('translation_id', 'Unknown')}\n")
                self.lookup_results.insert(tk.END, f"Timestamp: {record.get('timestamp', 'Unknown')}\n")
                self.lookup_results.insert(tk.END, f"Source Language: {record.get('source_lang', 'Unknown')}\n")
                self.lookup_results.insert(tk.END, f"Target Languages: {', '.join(record.get('target_langs', []))}\n")
                self.lookup_results.insert(tk.END, f"Sentence Count: {record.get('sentence_count', 0)}\n")
                self.lookup_results.insert(tk.END, f"Status: Completed\n")
                
                # Check S3 file existence
                if self.s3_client and record.get('s3_key'):
                    s3_status = self.check_s3_file_exists(record.get('s3_key'))
                    self.lookup_results.insert(tk.END, f"S3 File: {'✅ Available' if s3_status else '❌ Not found'}\n")
                
                break
        
        if not found:
            self.lookup_results.insert(tk.END, f"❌ Translation ID '{translation_id}' not found in history\n", 'error')
        
        # Configure tags
        self.lookup_results.tag_config('title', font=('Arial', 12, 'bold'))
        self.lookup_results.tag_config('error', foreground='red')

    def check_s3_file_exists(self, s3_key):
        """Check if S3 file exists"""
        if not self.s3_client or not self.output_bucket.get():
            return False
        
        try:
            self.s3_client.head_object(Bucket=self.output_bucket.get(), Key=s3_key)
            return True
        except:
            return False

    def check_initial_config(self):
        """Check if configuration exists on startup"""
        # Show debug mode status
        if self.debug_mode:
            print("🐛 Debug mode enabled - verbose logging active")
            print(f"Config file: {self.config_file}")
            print(f"History file: {self.history_file}")
        
        if not self.api_endpoint.get() or not self.api_key.get():
            response = messagebox.askyesno(
                "Configuration Required",
                "No configuration found. Would you like to set up the API connection now?"
            )
            if response:
                self.notebook.select(self.settings_tab)

    def retry_fetch_translations(self, result):
        """Retry fetching translations from S3"""
        if not self.s3_client:
            messagebox.showerror("Error", "S3 not configured")
            return
        
        output_key = result.get('output_location', {}).get('key')
        output_url = result.get('output_location', {}).get('url', '')
        output_bucket = result.get('output_location', {}).get('bucket')
        
        # Try to extract bucket from S3 URL format
        if not output_bucket and output_url.startswith('s3://'):
            parts = output_url.replace('s3://', '').split('/', 1)
            if parts:
                output_bucket = parts[0]
        
        # If still no bucket, use configured bucket
        if not output_bucket:
            output_bucket = self.output_bucket.get()
        
        if not output_key or not output_bucket:
            messagebox.showerror("Error", "No S3 location found")
            return
        
        # Ask user how long to poll
        poll_time = messagebox.askquestion(
            "Retry Options",
            "Would you like to poll for an extended time?\n\n" +
            "Yes = Poll for up to 2 minutes\n" +
            "No = Single attempt only",
            icon='question'
        )
        
        max_attempts = 120 if poll_time == 'yes' else 1
        
        try:
            # Show progress dialog
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Fetching Translations")
            progress_window.geometry("400x150")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            ttk.Label(progress_window, text="Polling S3 for translations...", 
                     font=('Arial', 10)).pack(pady=10)
            
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_window, variable=progress_var, 
                                          maximum=100, length=350)
            progress_bar.pack(pady=10)
            
            status_label = ttk.Label(progress_window, text="Starting...")
            status_label.pack(pady=5)
            
            cancel_flag = {'cancelled': False}
            
            def cancel_polling():
                cancel_flag['cancelled'] = True
                progress_window.destroy()
            
            ttk.Button(progress_window, text="Cancel", 
                      command=cancel_polling).pack(pady=5)
            
            progress_window.update()
            
            # Poll S3
            found = False
            for attempt in range(max_attempts):
                if cancel_flag['cancelled']:
                    break
                
                try:
                    # Update progress
                    progress = (attempt / max_attempts) * 100
                    progress_var.set(progress)
                    status_label.config(text=f"Attempt {attempt + 1}/{max_attempts}")
                    progress_window.update()
                    
                    # Try to fetch from S3
                    s3_obj = self.s3_client.get_object(Bucket=output_bucket, Key=output_key)
                    content = s3_obj['Body'].read().decode('utf-8')
                    s3_data = json.loads(content)
                    translations_data = s3_data.get('translations', {})
                    
                    if translations_data:
                        # Update the result and redisplay
                        result['translations'] = translations_data
                        found = True
                        break
                    else:
                        if attempt == 0:
                            status_label.config(text="File found but translations not ready...")
                        
                except self.s3_client.exceptions.NoSuchKey:
                    status_label.config(text=f"File not yet available (attempt {attempt + 1})")
                except Exception as e:
                    if attempt == 0:
                        print(f"S3 Retry Error: {str(e)}")
                        print(f"  Bucket: {output_bucket}")
                        print(f"  Key: {output_key}")
                
                if max_attempts > 1:
                    time.sleep(1)
            
            progress_window.destroy()
            
            if found:
                self.display_results(result)
                self.update_status("✅ Translations retrieved from S3!")
                messagebox.showinfo("Success", "Translations successfully retrieved!")
            else:
                if cancel_flag['cancelled']:
                    self.update_status("Polling cancelled")
                else:
                    messagebox.showinfo("Info", 
                        "Translations not yet available in S3.\n\n" +
                        "The translation may still be processing. " +
                        "Please try again later or check the History tab.")
                    self.update_status("Translations not ready yet")
                
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            messagebox.showerror("Error", f"Failed to fetch from S3: {str(e)}")
            self.update_status("S3 fetch failed")

    def copy_s3_command(self, output_location):
        """Copy AWS CLI command to clipboard for manual checking"""
        bucket = output_location.get('bucket', self.output_bucket.get())
        key = output_location.get('key', '')
        
        # Extract bucket from URL if needed
        url = output_location.get('url', '')
        if not bucket and url.startswith('s3://'):
            parts = url.replace('s3://', '').split('/', 1)
            if parts:
                bucket = parts[0]
        
        if bucket and key:
            # Create AWS CLI command
            command = f'aws s3 cp s3://{bucket}/{key} translation_result.json'
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(command)
            
            messagebox.showinfo(
                "Command Copied",
                f"AWS CLI command copied to clipboard:\n\n{command}\n\n" +
                "You can run this command in your terminal to manually download the translation file."
            )
        else:
            messagebox.showerror("Error", "Could not determine S3 location")

    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)

    def process_queue(self):
        """Process messages from thread queue"""
        try:
            while True:
                msg_type, msg_data = self.queue.get_nowait()
                
                if msg_type == 'status':
                    self.update_status(msg_data)
                elif msg_type == 'progress':
                    self.progress_var.set(msg_data)
                elif msg_type == 'result':
                    self.display_results(msg_data)
                elif msg_type == 'error':
                    messagebox.showerror("Error", msg_data)
                    self.update_status("Translation failed")
                elif msg_type == 'complete':
                    self.translate_btn.config(state='normal')
                    self.progress_var.set(0)
                elif msg_type == 'polling_info':
                    # Show polling information in output
                    self.show_polling_info(msg_data)
                elif msg_type == 'bucket_mismatch':
                    # Suggest fixing bucket configuration
                    self.suggest_bucket_fix(msg_data)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_queue)

    def show_polling_info(self, info):
        """Show S3 polling information in output"""
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', tk.END)
        
        self.output_text.insert(tk.END, "⏳ WAITING FOR TRANSLATIONS\n", 'title')
        self.output_text.insert(tk.END, "="*60 + "\n\n", 'header')
        
        self.output_text.insert(tk.END, "The translation job has been submitted successfully.\n", 'info')
        self.output_text.insert(tk.END, "Now polling S3 for the results...\n\n", 'info')
        
        self.output_text.insert(tk.END, "📍 S3 Location:\n", 'heading')
        self.output_text.insert(tk.END, f"   Bucket: {info['bucket']}\n", 'detail')
        self.output_text.insert(tk.END, f"   Key: {info['key']}\n", 'detail')
        
        # Show configured bucket if different
        configured_bucket = self.output_bucket.get()
        if configured_bucket and configured_bucket != info['bucket']:
            self.output_text.insert(tk.END, f"\n⚠️ Note: Your configured bucket is '{configured_bucket}'\n", 'warning')
            self.output_text.insert(tk.END, f"   but the API is using '{info['bucket']}'\n", 'warning')
            self.output_text.insert(tk.END, "   You may need to update your Settings.\n", 'warning')
        
        self.output_text.insert(tk.END, f"\n💡 {info['message']}\n", 'info')
        self.output_text.insert(tk.END, "\nThis is normal for asynchronous translation jobs.\n", 'info')
        
        # Configure tags
        self.output_text.tag_config('title', foreground='orange', font=('Arial', 14, 'bold'))
        self.output_text.tag_config('header', foreground='orange')
        self.output_text.tag_config('info', foreground='gray', font=('Arial', 10))
        self.output_text.tag_config('heading', foreground='blue', font=('Arial', 11, 'bold'))
        self.output_text.tag_config('detail', foreground='black', font=('Courier', 10))
        self.output_text.tag_config('warning', foreground='red', font=('Arial', 10, 'bold'))
        
        self.output_text.config(state='disabled')


def main():
    """Main entry point"""
    # Check for debug mode
    if os.environ.get('TRANSLATION_DEBUG', '').lower() in ('1', 'true', 'yes'):
        print("=" * 60)
        print("Translation Platform GUI - Debug Mode")
        print("=" * 60)
        print("To disable debug mode, unset TRANSLATION_DEBUG environment variable")
        print()
    
    root = tk.Tk()
    
    # Set icon if available
    try:
        icon_path = Path(__file__).parent / 'icon.ico'
        if icon_path.exists():
            root.iconbitmap(str(icon_path))
    except:
        pass
    
    app = TranslationGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()