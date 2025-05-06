import json
from pathlib import Path

def verify_conversion():
    print("🔍 Verifying conversion results...")
    
    # Check entities
    entity_files = list(Path("output_cx/entities").glob("*.json"))
    print(f"\n✅ Found {len(entity_files)} entity files:")
    for ef in entity_files:
        with open(ef, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  - {ef.name}: {len(data['entities'])} entries")

    # Check intents
    intent_files = list(Path("output_cx/intents").glob("*.json"))
    print(f"\n✅ Found {len(intent_files)} intent files:")
    for itf in intent_files:
        with open(itf, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  - {itf.name}: {len(data['training_phrases'])} training phrases")
        if "parameters" in data:
            print(f"    Parameters: {[p['id'] for p in data['parameters']]}")

if __name__ == "__main__":
    verify_conversion()