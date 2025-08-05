# 🚀 Enhanced Interactive CLI Guide

## 🎯 **Key Improvements Made**

### **1. File Content Detection**
The CLI now automatically detects and extracts:
- **Source language** from JSON files (if specified)
- **Sentences** from both text and JSON formats
- **File format** and prompts accordingly

### **2. Smart Prompting System**
- **Interactive language selection** with numbered menu
- **Validation** of all inputs with helpful error messages
- **Smart defaults** for batch processing and formatting
- **Confirmation steps** before processing

### **3. Minimal Commands**
Instead of complex command lines, now it's just:
```bash
# Simple - just specify file
python interactive_cli.py sentences.txt

# Even simpler - no parameters at all
python interactive_cli.py
```

---

## 📋 **Usage Examples**

### **Example 1: File with Source Language Specified**

**Your JSON file (request.json):**
```json
{
    "source_language": "en",
    "target_languages": ["es", "fr", "de"],
    "sentences": ["Hello World", "How are you?", "Do you need help?"]
}
```

**CLI Usage:**
```bash
python interactive_cli.py request.json
```

**Interactive Flow:**
```
🌐 Welcome to Interactive Translation Platform
==================================================
✅ Found 3 sentences in file
   1. Hello World
   2. How are you?
   3. Do you need help?

Use these sentences? (y/n): y
✅ Got 3 sentences to translate
✅ Detected source language: en
Use detected source language 'en'? (Y/n): y

Select target language(s):
Common languages:
  1. English (en)  2. Spanish (es)
  3. French (fr)   4. German (de)
  5. Italian (it)  6. Portuguese (pt)

Your choice: 2,3,4

📋 Translation Summary:
   Source: en
   Targets: es, fr, de
   Sentences: 3
   Batch size: 3

Proceed with translation? (Y/n): y
```

### **Example 2: Simple Text File**

**Your text file (sentences.txt):**
```txt
Hello world
How are you today?
This is a test sentence
```

**CLI Usage:**
```bash
python interactive_cli.py sentences.txt
```

**Interactive Flow:**
```
✅ Found 3 sentences in file
Use these sentences? (y/n): y

Select source language:
  1. English (en)  2. Spanish (es)  3. French (fr)
Your choice: 1

Select target language(s):
Your choice: es,fr

📱 Display options:
Show results in terminal? (Y/n): y
Use simple format (no colors)? (y/N): n
Save results to file? (y/N): y
Output filename (default: translation_results.json): 

Proceed with translation? (Y/n): y
```

### **Example 3: No File - Manual Input**

**CLI Usage:**
```bash
python interactive_cli.py
```

**Interactive Flow:**
```
📝 Enter sentences to translate:
   - Type each sentence and press Enter
   - Type 'done' when finished

Sentence 1: Hello world
Sentence 2: How are you?
Sentence 3: done

Select source language:
Your choice: en

Select target language(s):
Your choice: es,fr,de
```

---

## 🎨 **GUI Application**

For users who prefer graphical interfaces:

### **Installation:**
```bash
# GUI uses tkinter (included with Python)
python translation_gui.py
```

### **Features:**
- **Tabbed interface**: Translate, Settings, History
- **File drag & drop** support
- **Language selection** with dropdowns
- **Progress bars** for long operations
- **Results display** with formatting options
- **Configuration management** with test connection
- **Translation history** browser

### **GUI Screenshots (Text Description):**

**Main Translation Tab:**
- File browser with preview
- Text input area
- Language selection dropdowns
- Quick language buttons (Spanish, French, German)
- Options checkboxes
- Large "🌐 Translate" button
- Results display area

**Settings Tab:**
- API endpoint configuration
- API key input (masked)
- Test connection button
- Save configuration button
- Status messages

**History Tab:**
- Table view of recent translations
- Columns: ID, Time, Languages, Sentences
- Refresh button

---

## 🔧 **Installation & Setup**

### **Enhanced CLI Requirements:**
```txt
# requirements.txt
requests>=2.28.0
boto3>=1.26.0
tqdm>=4.64.0
colorama>=0.4.6
```

### **Installation:**
```bash
# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x interactive_cli.py

# Run setup wizard
python interactive_cli.py --setup
```

### **First-Time Setup:**
```bash
python interactive_cli.py --setup
```

**Setup Flow:**
```
🌐 Welcome to Interactive Translation Platform
❌ CLI not configured
Let's set up your translation platform:
API Endpoint URL: https://your-api-gateway-url/translate
API Key: your-api-key-here
S3 Output Bucket (optional): your-output-bucket
AWS Region (default: eu-west-1): eu-west-1
✅ Configuration saved
✅ Connection test successful
```

---

## 📱 **File Format Support**

### **Automatically Detected Formats:**

**1. JSON with source language:**
```json
{
    "source_language": "en",
    "target_languages": ["es", "fr"],
    "sentences": ["Hello", "World"]
}
```
✅ **Auto-detects source language**  
✅ **Extracts sentences**  
✅ **Suggests target languages**

**2. JSON array:**
```json
["Hello world", "How are you?", "This is a test"]
```
✅ **Extracts sentences**  
❓ **Prompts for source language**

**3. JSON with metadata:**
```json
{
    "sentences": ["Hello", "World"],
    "metadata": {"source": "website"}
}
```
✅ **Extracts sentences from 'sentences' key**  
❓ **Prompts for source language**

**4. Text file:**
```txt
Hello world
How are you?
# This is a comment (ignored)
This is a test
```
✅ **One sentence per line**  
✅ **Ignores comments starting with #**  
✅ **Ignores empty lines**

---

## 🚀 **Command Comparison**

### **Before (Complex):**
```bash
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de \
  --file sentences.txt \
  --output results.json \
  --batch-size 25 \
  --no-progress \
  --simple-format \
  --download
```

### **After (Simple):**
```bash
# Just specify the file
python interactive_cli.py sentences.txt

# Or even simpler
python interactive_cli.py
```

**The CLI handles everything interactively!**

---

## 🎯 **Smart Features**

### **1. Automatic Detection**
- **File format** (JSON vs text)
- **Source language** (from JSON files)
- **Sentence extraction** (different JSON structures)
- **Batch processing needs** (based on sentence count)

### **2. Intelligent Prompting**
- **Only asks what's needed** (skips detected values)
- **Provides helpful examples** in prompts
- **Validates input** and gives clear error messages
- **Offers quick options** for common choices

### **3. User-Friendly Options**
- **Numbered menus** for language selection
- **Yes/No prompts** with sensible defaults
- **Progress indicators** during processing
- **Confirmation summaries** before execution

### **4. Error Prevention**
- **Validates file existence** before processing
- **Checks API configuration** before translation
- **Confirms language codes** are valid format
- **Prevents empty inputs** with helpful messages

---

## 🔍 **Interactive Examples**

### **Example: Large File Processing**

**Input file:** `large_content.txt` (150 sentences)

**CLI Flow:**
```
✅ Found 150 sentences in file
Use these sentences? (y/n): y

Select source language:
Your choice: en

Select target language(s):
Your choice: es,fr,de

📦 You have 150 sentences.
Enable batch processing? (Y/n): y
Batch size (default 25): 50

📱 Display options:
Show results in terminal? (Y/n): n
Save results to file? (y/N): y
Output filename: large_translations.json

📋 Translation Summary:
   Source: en
   Targets: es, fr, de
   Sentences: 150
   Batch size: 50

Proceed with translation? (Y/n): y

📦 Processing 150 sentences in batches of 50
🔄 Processing batch 1/3
🔄 Processing batch 2/3
🔄 Processing batch 3/3
✅ All batches completed! Processed 150 sentences total.
💾 Combined results saved to large_translations.json
```

### **Example: Error Handling**

**Scenario:** User provides invalid language code

```
Select target language(s):
Your choice: spanish,french

❌ All language codes must be 2 characters (e.g., 'en', 'es')
Your choice: es,fr

✅ Valid languages selected
```

**Scenario:** Empty sentences

```
📝 Enter sentences to translate:
Sentence 1: 
❌ Sentence cannot be empty. Try again or type 'done'
Sentence 1: Hello world
Sentence 2: done
```

**Scenario:** API not configured

```
❌ CLI not configured
Let's set up your translation platform:
API Endpoint URL: 
❌ Both endpoint and API key are required
```

---

## 🎨 **GUI Application Features**

### **Main Interface:**
```
┌─────────────────── Translation Platform ──────────────────┐
│ [Translate] [Settings] [History]                          │
│                                                           │
│ ┌─ Input ─────────────────────────────────────────────┐   │
│ │ File: [Browse] [Clear]                              │   │
│ │ Or enter text directly:                             │   │
│ │ ┌─────────────────────────────────────────────────┐ │   │
│ │ │ Hello world                                     │ │   │
│ │ │ How are you?                                    │ │   │
│ │ └─────────────────────────────────────────────────┘ │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                           │
│ ┌─ Languages ─────────────────────────────────────────┐   │
│ │ From: [English (en) ▼]                             │   │
│ │ To:   [es,fr,de____________________]               │   │
│ │ Quick: [Spanish] [French] [German]                 │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                           │
│ ┌─ Options ───────────────────────────────────────────┐   │
│ │ ☑ Save results to file                             │   │
│ │ ☐ Simple format (no colors)                       │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                           │
│                   [🌐 Translate]                          │
│                                                           │
│ ┌─ Results ───────────────────────────────────────────┐   │
│ │ 🌐 TRANSLATION RESULTS                             │   │
│ │ ════════════════════════                           │   │
│ │ 📝 Sentence 1:                                     │   │
│ │    Original: Hello world                           │   │
│ │    ES: Hola mundo                                  │   │
│ │    FR: Bonjour le monde                           │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                           │
│ Ready                              [████████████] 100%    │
└───────────────────────────────────────────────────────────┘
```

### **Settings Tab:**
```
┌─ API Configuration ─────────────────────────────────────┐
│ API Endpoint: [https://api.example.com/translate_____] │
│ API Key:      [********************************_____] │
│                                                        │
│ [Test Connection] [Save Configuration]                 │
│                                                        │
│ ✅ Connection successful                               │
└────────────────────────────────────────────────────────┘
```

### **History Tab:**
```
┌─ Recent Translations ───────────────────────────────────┐
│ ID       │ Time                │ Languages   │ Sentences │
│ abc12345 │ 2025-01-20 15:30:45 │ en → es,fr  │ 3        │
│ def67890 │ 2025-01-20 14:15:22 │ en → es,de  │ 5        │
│ ghi11111 │ 2025-01-20 13:45:10 │ en → fr     │ 1        │
└─────────────────────────────────────────────────────────┘
                    [Refresh History]
```

---

## 🚀 **Quick Start Commands**

### **1. First Time Setup:**
```bash
python interactive_cli.py --setup
```

### **2. Translate a File:**
```bash
python interactive_cli.py myfile.txt
```

### **3. Manual Translation:**
```bash
python interactive_cli.py
```

### **4. Start GUI:**
```bash
python translation_gui.py
```

---

## 💡 **Best Practices**

### **File Preparation:**
1. **Use UTF-8 encoding** for special characters
2. **One sentence per line** in text files
3. **Include source_language** in JSON for auto-detection
4. **Keep sentences under 5000 characters**

### **Language Codes:**
- Use **2-character ISO codes** (en, es, fr, de)
- **Common codes**: en=English, es=Spanish, fr=French, de=German, it=Italian, pt=Portuguese, ru=Russian, zh=Chinese, ja=Japanese, ko=Korean

### **Batch Processing:**
- **Use batches** for 25+ sentences
- **Recommended batch size**: 25-50 sentences
- **Monitor progress** for large files

### **Error Handling:**
- **Check API configuration** if connection fails
- **Verify file format** if detection fails
- **Use simple format** if colors don't display properly

---
