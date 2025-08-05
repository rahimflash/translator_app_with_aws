# 📁 File Usage Guide & Examples

## 🚀 Quick Start Examples

### **1. Create a Simple Text File**
```bash
# Create sentences.txt
cat > sentences.txt << 'EOF'
Hello world
How are you today?
This is a test sentence
Welcome to our platform
Thank you for using our service
EOF

# Translate the file
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de \
  --file sentences.txt
```

### **2. Create a JSON File**
```bash
# Create sentences.json
cat > sentences.json << 'EOF'
[
  "Hello world",
  "How are you today?", 
  "This is a test sentence"
]
EOF

# Translate the JSON file
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr \
  --file sentences.json \
  --output results.json
```

---

## 📋 File Format Examples

### **Text File Format** (sentences.txt)
- **One sentence per line**
- **Empty lines are ignored**
- **Comments starting with # are ignored**

```txt
# Customer service phrases
Hello, how can I help you today?
Thank you for contacting support
We appreciate your patience
Your request has been received

# Product descriptions  
Premium quality materials used
Fast and free shipping available
30-day money-back guarantee
```

### **JSON Array Format** (simple.json)
```json
[
  "First sentence to translate",
  "Second sentence to translate", 
  "Third sentence to translate"
]
```

### **JSON Object Format** (structured.json)
```json
{
  "sentences": [
    "Welcome to our platform",
    "Experience fast translations",
    "Join thousands of users"
  ],
  "metadata": {
    "source": "website",
    "category": "marketing"
  }
}
```

---

## 🎯 Real-World Usage Examples

### **Website Localization**
```bash
# Create website content file
cat > website_content.txt << 'EOF'
Welcome to our company
About our services
Contact us today
Privacy policy
Terms of service
Follow us on social media
Subscribe to our newsletter
EOF

# Translate for multiple markets
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de,it,pt,ru,zh \
  --file website_content.txt \
  --output localized_website.json \
  --batch-size 5
```

### **Customer Support Scripts**
```bash
# Create support phrases
cat > support_phrases.txt << 'EOF'
Hello, how can I help you today?
Thank you for contacting customer support
We appreciate your patience while we resolve this
Your request has been received and is being processed
Is there anything else I can assist you with?
Have a wonderful day and thank you for choosing us
EOF

# Translate for international support
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de,pt,it \
  --file support_phrases.txt
```

### **E-commerce Product Descriptions**
```json
// products.json
{
  "sentences": [
    "Premium quality materials ensure durability",
    "Fast and free shipping to your doorstep",
    "30-day money-back satisfaction guarantee",
    "Perfect for both casual and professional use",
    "Easy installation with step-by-step guide included"
  ],
  "product_info": {
    "category": "electronics",
    "target_markets": ["EU", "LATAM", "APAC"]
  }
}
```

```bash
# Translate product descriptions
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de,it,pt,ja,zh \
  --file products.json \
  --output translated_products.json
```

### **Mobile App Interface**
```bash
# Create app interface strings
cat > app_strings.txt << 'EOF'
Login
Sign up
Forgot password?
Loading, please wait
Profile updated successfully
Settings saved
Logout
Delete account
Contact support
Rate this app
EOF

# Translate for app localization
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de,it,pt,ru,zh,ja,ko \
  --file app_strings.txt \
  --simple-format \
  --output app_translations.json
```

---

## 📊 Batch Processing Examples

### **Large Dataset Processing**
```bash
# Create a large dataset
python -c "
with open('large_dataset.txt', 'w') as f:
    for i in range(1, 101):
        f.write(f'This is sentence number {i} for batch processing\\n')
"

# Process in batches with progress tracking
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de \
  --file large_dataset.txt \
  --batch-size 25 \
  --output batch_results.json
```

### **Multiple File Processing**
```bash
#!/bin/bash
# Process multiple files

files=("marketing.txt" "support.txt" "legal.txt" "technical.txt")

for file in "${files[@]}"; do
    echo "Processing $file..."
    python translation_cli.py translate \
      --source-lang en \
      --target-langs es,fr,de \
      --file "$file" \
      --output "results/${file%.txt}_translated.json" \
      --no-terminal
done

echo "All files processed!"
```

---

## 🔧 Advanced File Formats

### **CSV-like Structure** (using text file)
```txt
# Structured content with categories
# Format: Category | Text
Marketing | Welcome to our innovative platform
Marketing | Experience the future of communication
Support | How can we help you today?
Support | Your satisfaction is our priority
Legal | Terms and conditions apply
Legal | Privacy policy updated
```

### **Multilingual Source** (mixed.json)
```json
{
  "sentences": [
    "Hello world",
    "Bonjour le monde", 
    "Hola mundo"
  ],
  "source_languages": ["en", "fr", "es"],
  "note": "Mixed language input - specify source language per sentence"
}
```

### **Contextual Translation** (context.json)
```json
{
  "sentences": [
    "Bank account balance",
    "River bank erosion", 
    "Memory bank storage"
  ],
  "contexts": ["finance", "geography", "technology"],
  "note": "Same word 'bank' but different contexts"
}
```

---

## 📱 Command Variations

### **Quick Text File Translation**
```bash
# One-liner to create and translate
echo -e "Hello\nWorld\nTest" > quick.txt && \
python translation_cli.py translate \
  --source-lang en \
  --target-langs es \
  --file quick.txt
```

### **Silent Processing** (for scripts)
```bash
# No terminal output, just save to file
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr \
  --file input.txt \
  --output results.json \
  --no-terminal \
  --no-progress
```

### **Terminal Display Only**
```bash
# Show in terminal but don't save to file
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr,de \
  --file sentences.txt
```

### **Download S3 Results Automatically**
```bash
# Auto-download translated files
python translation_cli.py translate \
  --source-lang en \
  --target-langs es,fr \
  --file content.txt \
  --download
```

---

## 🎨 Output Examples

### **Terminal Output** (with colors)
```
================================================================================
🌐 TRANSLATION RESULTS  
================================================================================

📝 Sentence 1:
 EN  🇺🇸 Hello world
 ES  🇪🇸 Hola mundo
 FR  🇫🇷 Bonjour le monde

📝 Sentence 2:
 EN  🇺🇸 How are you today?
 ES  🇪🇸 ¿Cómo estás hoy?
 FR  🇫🇷 Comment allez-vous aujourd'hui?

================================================================================
📊 Summary: 2 sentences → 4 translations
```

### **JSON Output File**
```json
{
  "success": true,
  "translation_id": "abc123-uuid-here",
  "input_location": {
    "bucket": "input-bucket",
    "key": "requests/2025/01/20/abc123_request.json"
  },
  "output_location": {
    "bucket": "output-bucket", 
    "key": "translations/2025/01/20/abc123.json"
  },
  "summary": {
    "source_language": "en",
    "target_languages": ["es", "fr"],
    "sentences_processed": 2,
    "translations_generated": 4
  }
}
```

---

## 💡 Tips & Best Practices

### **File Preparation**
- Keep sentences **under 5000 characters** each
- Use **UTF-8 encoding** for special characters
- **One sentence per line** in text files
- **Avoid very long files** - use batching for 100+ sentences

### **Performance Optimization**
- Use **batch processing** for large files (`--batch-size 25`)
- **Save to files** for large datasets instead of terminal display
- Use **simple format** (`--simple-format`) for faster processing

### **Error Handling**
- Check files exist before translation
- Use **appropriate batch sizes** (10-50 sentences)
- Monitor **progress** for long-running jobs
- Keep **backups** of original files