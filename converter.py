import json
import os
from pathlib import Path
from typing import Dict, List

class ES2CXConverter:
    def __init__(self):
        self.input_dir = Path("extracted")
        self.output_dir = Path("output_cx")
        self.output_dir.mkdir(exist_ok=True)

    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON file with UTF-8 encoding"""
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)

    def _save_json(self, data: Dict, file_path: Path):
        """Save JSON file with proper formatting"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def convert_entity(self, entity_file: Path) -> Dict:
        """Convert ES entity to CX format"""
        try:
            base_name = entity_file.stem.replace('_entries_id', '')
            entries_file = entity_file.parent / f"{base_name}_entries_id.json"
            
            if not entries_file.exists():
                print(f"⚠️ No entries file for {base_name}")
                return None

            entries = self._load_json(entries_file)
            return {
                "display_name": base_name.lower(),
                "kind": "KIND_MAP",
                "entities": [
                    {
                        "value": entry["value"],
                        "synonyms": entry.get("synonyms", [])
                    }
                    for entry in entries
                    if isinstance(entry, dict) and "value" in entry
                ]
            }
        except Exception as e:
            print(f"❌ Error converting {entity_file.name}: {str(e)}")
            return None

    def convert_intent(self, intent_file: Path) -> Dict:
        """Convert ES intent to CX format"""
        try:
            intent_data = self._load_json(intent_file)
            base_name = intent_file.stem
            user_says_file = intent_file.parent / f"{base_name}_usersays_id.json"

            if not user_says_file.exists():
                print(f"⚠️ No training phrases for {base_name}")
                return None

            # Process training phrases
            user_says = self._load_json(user_says_file)
            training_phrases = []
            parameters = set()

            for phrase in user_says:
                parts = []
                for part in phrase.get("data", []):
                    text = part.get("text", "").strip()
                    if not text:
                        continue

                    if part.get("alias"):
                        param_id = part["alias"].lower().replace(" ", "_")
                        parts.append({
                            "text": text,
                            "parameter_id": param_id
                        })
                        parameters.add(param_id)
                    else:
                        parts.append({"text": text})

                if parts:
                    training_phrases.append({
                        "parts": parts,
                        "repeat_count": 1
                    })

            # Build CX intent
            cx_intent = {
                "display_name": base_name,
                "training_phrases": training_phrases
            }

            # Add parameters if found
            if parameters:
                cx_intent["parameters"] = [
                    {
                        "id": param,
                        "entity_type": f"@sys.any",  # Will be replaced later
                        "is_list": False
                    }
                    for param in parameters
                ]

            return cx_intent

        except Exception as e:
            print(f"❌ Error converting {intent_file.name}: {str(e)}")
            return None

    def process_all(self):
        """Process all entities and intents"""
        print("🔄 Starting conversion from ES to CX format...")
        
        # Convert entities
        entities_dir = self.output_dir / "entities"
        entities_dir.mkdir(exist_ok=True)

        print("\n🔍 Processing entities...")
        entity_files = list(self.input_dir.glob("entities/*.json"))
        for entity_file in entity_files:
            if "_entries_id" not in entity_file.name:
                continue
                
            cx_entity = self.convert_entity(entity_file)
            if cx_entity and cx_entity["entities"]:
                output_path = entities_dir / f"{cx_entity['display_name']}.json"
                self._save_json(cx_entity, output_path)
                print(f"✅ Converted {cx_entity['display_name']} ({len(cx_entity['entities'])} entries)")

        # Convert intents
        intents_dir = self.output_dir / "intents"
        intents_dir.mkdir(exist_ok=True)

        print("\n🔍 Processing intents...")
        intent_files = list(self.input_dir.glob("intents/*.json"))
        for intent_file in intent_files:
            if "_usersays_" in intent_file.name:
                continue

            cx_intent = self.convert_intent(intent_file)
            if cx_intent and cx_intent["training_phrases"]:
                output_path = intents_dir / f"{cx_intent['display_name']}.json"
                self._save_json(cx_intent, output_path)
                print(f"✅ Converted {cx_intent['display_name']} ({len(cx_intent['training_phrases'])} phrases)")

        print("\n🎉 Conversion completed! Results in 'output_cx' folder")

if __name__ == "__main__":
    converter = ES2CXConverter()
    converter.process_all()