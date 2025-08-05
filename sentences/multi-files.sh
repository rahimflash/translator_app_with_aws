#!/bin/bash
# Process multiple files

files=("../sentences/french.txt" "german.txt" "chinese.txt" "translate.json")

for file in "${files[@]}"; do
    echo "Processing $file..."
    python ../cli/translation_cli.py translate \
      --source-lang en \
      --target-langs es,fr,de \
      --file "$file" \
      --output "results/${file%.txt}_translated.json" \
      --no-terminal
done

echo "All files processed!"

