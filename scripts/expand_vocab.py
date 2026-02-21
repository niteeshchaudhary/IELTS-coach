"""
Script to bulk-expand the IELTS vocabulary bank using the AI engine.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import config
from intelligence.llm_engine import get_llm
from intelligence.vocab_generator import VocabularyGenerator

def main():
    print("🚀 Starting Vocabulary Expansion...")
    print("ℹ️  Note: This can take several minutes per topic if using a local LLM (like Ollama).")
    
    # Initialize systems
    try:
        llm = get_llm()
    except Exception as e:
        print(f"❌ Error: Could not initialize LLM. {e}")
        return

    generator = VocabularyGenerator(llm)
    
    # Load existing bank
    vocab_path = Path(config.VOCAB_JSON_PATH)
    if vocab_path.exists():
        with open(vocab_path, "r") as f:
            word_bank = json.load(f)
    else:
        word_bank = []
    
    print(f"📊 Current word bank size: {len(word_bank)}")
    
    topics = [
        "technology", "environment", "education", "health", 
        "society", "economics", "culture", "travel", 
        "work", "science", "globalization", "urbanization"
    ]
    
    new_words_total = []
    
    for topic in topics:
        print(f"🔍 Generating words for topic: {topic}...")
        new_words = generator.expand_word_bank(word_bank + new_words_total, topic=topic, count=5)
        print(f"✅ Found {len(new_words)} new unique words.")
        new_words_total.extend(new_words)
    
    if new_words_total:
        word_bank.extend(new_words_total)
        
        # Save back
        with open(vocab_path, "w") as f:
            json.dump(word_bank, f, indent=2)
        
        print(f"🎉 Success! Added {len(new_words_total)} words.")
        print(f"📉 New word bank size: {len(word_bank)}")
    else:
        print("⚠️ No new words were added.")

if __name__ == "__main__":
    main()
