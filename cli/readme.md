# 🚀 Enhanced CLI with Terminal Output

## 📦 Requirements

Create a `requirements.txt` file:

```txt
# requirements.txt
requests>=2.28.0
boto3>=1.26.0
tqdm>=4.64.0
colorama>=0.4.6
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## ✨ New Features Added

### **1. Beautiful Terminal Output** 🎨
- **Colored output** with language flags and formatting
- **Side-by-side comparison** of original and translated text
- **Progress indicators** and status messages
- **Fallback to simple format** for systems without color support

### **2. Enhanced Command Options** ⚙️
- `--no-terminal` - Disable terminal display (API-only mode)
- `--simple-format` - Use simple text format (no colors)
- `--download` - Auto-download S3 files
- `show` command - Display stored translations from S3

### **3. Smart Display Logic** 🧠
- **Automatic color detection** for terminal compatibility
- **Language flag emojis** for visual language identification
- **Responsive formatting** that adapts to content length
- **Error highlighting** for failed translations

---

## 📋 Usage Examples

### **Basic Translation with Terminal Output**
```bash
# Translate with beautiful terminal display
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de \
  --text "Hello world, how are you today?"
```

**Terminal Output:**
```
🔄 Starting translation job
📊 1 sentences → 3 languages
⏱️ Estimated time: 1.5 seconds
Processing |████████████████████████| 100%
✅ Translation completed successfully!
🆔 Translation ID: abc123-uuid-here
⏱️ Actual time: 1.2 seconds
📦 Output location: s3://output-bucket/translations/...

================================================================================
🌐 TRANSLATION RESULTS
================================================================================

📝 Sentence 1:
 EN  🇺🇸 Hello world, how are you today?
 ES  🇪🇸 Hola mundo, ¿cómo estás hoy?
 FR  🇫🇷 Bonjour le monde, comment allez-vous aujourd'hui?
 DE  🇩🇪 Hallo Welt, wie geht es dir heute?

================================================================================
📊 Summary: 1 sentences → 3 translations
```

### **File Translation with Batching**
```bash
# Translate from file with progress tracking
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,it,pt \
  --file sentences.txt \
  --batch-size 10 \
  --output results.json
```

### **Simple Format (No Colors)**
```bash
# For terminals without color support or scripts
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr \
  --text "Hello world" \
  --simple-format
```

**Simple Output:**
```
================================================================================
🌐 TRANSLATION RESULTS
================================================================================

📝 Sentence 1:
[EN] Hello world
[ES] Hola mundo
[FR] Bonjour le monde

================================================================================
```

### **API-Only Mode (No Terminal Display)**
```bash
# Just get the API response without terminal display
python translation_cli.py translate \
  --source-lang en \
  --target-langs es \
  --text "Hello" \
  --no-terminal \
  --output api_response.json
```

### **Auto-Download S3 Files**
```bash
# Automatically download translated files from S3
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de \
  --text "Hello world" \
  --download
```

### **View Stored Translations**
```bash
# Display a previously stored translation from S3
python translation_cli.py show abc123-uuid-here

# Use simple format for viewing
python translation_cli.py show abc123-uuid-here --simple-format
```

### **Translation History**
```bash
# List recent translations
python translation_cli.py list --limit 5

# Get status of specific translation
python translation_cli.py get-status abc123-uuid-here
```

---

## 🎨 Terminal Output Features

### **Color Coding System**
- **Blue background**: Source language
- **Green**: First target language
- **Magenta**: Second target language  
- **Cyan**: Third target language
- **Yellow**: Fourth target language
- **Red**: Error messages

### **Language Flags** 🏴
The CLI includes flag emojis for common languages:
- 🇺🇸 English (en)
- 🇪🇸 Spanish (es)  
- 🇫🇷 French (fr)
- 🇩🇪 German (de)
- 🇮🇹 Italian (it)
- 🇵🇹 Portuguese (pt)
- 🇷🇺 Russian (ru)
- 🇨🇳 Chinese (zh)
- 🇯🇵 Japanese (ja)
- 🇰🇷 Korean (ko)
- And more...

### **Smart Formatting**
- **Long sentences** are properly wrapped
- **Multiple sentences** are separated with dividers
- **Error translations** are highlighted in red
- **Progress bars** show real-time processing status

---

## 🔧 Configuration Options

### **Initial Setup**
```bash
# Configure the CLI with your API details
python translation_cli.py configure \
  --endpoint https://your-api-gateway-url/translate \
  --api-key your-api-key-here \
  --output-bucket your-s3-output-bucket \
  --aws-region eu-west-1
```

### **Check Configuration**
```bash
# View current configuration and test connectivity
python translation_cli.py status
```

**Status Output:**
```
🔧 Translation CLI Configuration:
API Endpoint: https://abc123.execute-api.eu-west-1.amazonaws.com/dev/translate
API Key: Configured
Output Bucket: translation-output-bucket-abc123
AWS Region: eu-west-1
Config file: /home/user/.translation-cli-config.json
History file: /home/user/.translation-cli-history.json
S3 Access: Available
API Status: 🟢 Connected
Last translation: 2025-01-20T15:30:45Z (abc123...)
```

---

## 📁 File Format Support

### **JSON Files**
```json
// sentences.json
[
  "Hello world",
  "How are you?",
  "This is a test"
]

// OR with metadata
{
  "sentences": [
    "Hello world",
    "How are you?"
  ],
  "metadata": {
    "source": "example"
  }
}
```

### **Text Files**
```txt
# sentences.txt (one sentence per line)
Hello world
How are you today?
This is a test sentence
Welcome to our platform
```

---

## 🚀 Advanced Usage

### **Batch Processing Large Files**
```bash
# Process 1000+ sentences in batches
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de,it,pt \
  --file large_dataset.txt \
  --batch-size 50 \
  --output results/
```

### **Integration with Scripts**
```bash
#!/bin/bash
# Automated translation script

# Set API endpoint as environment variable
export TRANSLATION_API_ENDPOINT="https://your-api.com/translate"
export TRANSLATION_API_KEY="your-key"

# Translate multiple files
for file in inputs/*.txt; do
    echo "Translating $file..."
    python translation_cli.py translate \
      --source-lang en \
      --target-langs es,fr \
      --file "$file" \
      --output "outputs/$(basename $file .txt)_translated.json" \
      --no-terminal
done
```

### **Programmatic Usage**
```python
# Use the CLI class in your Python scripts
from translation_cli import TranslationCLI

cli = TranslationCLI(
    api_endpoint="https://your-api.com/translate",
    api_key="your-key"
)

result = cli.translate(
    source_lang="en",
    target_langs=["es", "fr"],
    sentences=["Hello world"],
    show_terminal=True
)

print(f"Translation ID: {result['translation_id']}")
```

---

## 🎯 Use Cases

### **1. Interactive Translation**
Perfect for quick translations with immediate visual feedback:
```bash
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de \
  --text "What's the weather like today?"
```

### **2. Batch Document Processing**
Ideal for processing large document sets:
```bash
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de,it,pt \
  --file documents/content.txt \
  --batch-size 25 \
  --output results/translated_content.json
```

### **3. API Testing & Development**
Great for testing the translation API:
```bash
# Quick API test
python translation_cli.py translate \
  --source-lang en \
  --target-langs es \
  --text "test" \
  --no-terminal

# View API response only
python translation_cli.py translate \
  --source-lang en \
  --target-langs es \
  --text "test" \
  --output response.json \
  --no-terminal
```

### **4. Content Localization Workflow**
Perfect for content management workflows:
```bash
# Step 1: Translate content
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de,it,pt,ru,zh \
  --file website_content.json \
  --output localized_content.json

# Step 2: Review specific translation
python translation_cli.py show abc123-translation-id

# Step 3: Download for further processing
python translation_cli.py translate \
  --source-lang en \
  --target-langs es \
  --text "Final check" \
  --download
```

---

## 🛠️ Troubleshooting

### **No Colors Showing**
If colors aren't displaying properly:
```bash
# Use simple format
python translation_cli.py translate ... --simple-format

# Check if colorama is installed
pip install colorama
```

### **S3 Access Issues**
If S3 download fails:
```bash
# Check AWS credentials
aws configure list

# Verify bucket access
aws s3 ls s3://your-output-bucket/

# Reconfigure with correct bucket
python translation_cli.py configure --output-bucket correct-bucket-name
```

### **API Connection Problems**
If API calls fail:
```bash
# Test configuration
python translation_cli.py status

# Reconfigure endpoint
python translation_cli.py configure --endpoint https://correct-endpoint
```
