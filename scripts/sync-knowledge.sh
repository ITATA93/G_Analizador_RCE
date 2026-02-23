#!/bin/bash
# sync-knowledge.sh - Promote deep research to global Knowledge Items

set -e

RESEARCH_DIR="docs/research"
KNOWLEDGE_DIR="$HOME/.gemini/antigravity/knowledge"

echo "🔍 Antigravity Knowledge Sync"
echo "=============================="
echo ""

# Check if research directory exists
if [ ! -d "$RESEARCH_DIR" ]; then
    echo "❌ Error: $RESEARCH_DIR not found"
    exit 1
fi

# List recent research files
echo "📚 Recent research files:"
find "$RESEARCH_DIR" -name "*.md" -not -path "*/_templates/*" -type f -mtime -30 | sort -r | head -10

echo ""
echo "Enter the path to the research file to promote (or 'q' to quit):"
read -r research_file

if [ "$research_file" = "q" ]; then
    echo "Cancelled."
    exit 0
fi

if [ ! -f "$research_file" ]; then
    echo "❌ File not found: $research_file"
    exit 1
fi

# Extract title and tags
title=$(grep -m 1 "^# " "$research_file" | sed 's/^# //')
tags=$(grep -m 1 -E '^\\*\\*Tags:\\*\\*' "$research_file" | sed 's/^\\*\\*Tags:\\*\\* //' || true)

echo ""
echo "📄 Research: $title"
echo "🏷️  Tags: $tags"
echo ""
echo "Enter Knowledge Item name (snake_case, e.g., 'nocobase_api_patterns'):"
read -r ki_name

if [ -z "$ki_name" ]; then
    echo "❌ Name cannot be empty"
    exit 1
fi

ki_path="$KNOWLEDGE_DIR/$ki_name"

# Check if KI already exists
if [ -d "$ki_path" ]; then
    echo "⚠️  Knowledge Item '$ki_name' already exists"
    echo "Do you want to add to it? (y/n)"
    read -r add_to_existing

    if [ "$add_to_existing" != "y" ]; then
        echo "Cancelled."
        exit 0
    fi
else
    # Create new KI structure
    mkdir -p "$ki_path/artifacts"

    # Create metadata.json
    cat > "$ki_path/metadata.json" <<EOF
{
  "title": "$title",
  "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "tags": "$tags",
  "source": "$research_file"
}
EOF

    echo "✅ Created new Knowledge Item: $ki_name"
fi

# Copy research to artifacts
artifact_name=$(basename "$research_file")
cp "$research_file" "$ki_path/artifacts/$artifact_name"

echo "✅ Copied research to KI artifacts"
echo ""
echo "Knowledge Item location: $ki_path"
echo ""
echo "Next steps:"
echo "1. Review and organize artifacts in $ki_path/artifacts/"
echo "2. Create overview.md if needed"
echo "3. Update metadata.json with additional info"

echo ""
echo "✨ Done!"
