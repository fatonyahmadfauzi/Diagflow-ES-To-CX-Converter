import json
from pathlib import Path

def fix_empty_entities():
    entities_dir = Path("output_cx/entities")
    
    # Data manual untuk jenis_info_kiano
    jenis_info = {
        "display_name": "jenis_info_kiano",
        "kind": "KIND_MAP",
        "entities": [
            {"value": "harga", "synonyms": ["biaya", "tarif"]},
            {"value": "lokasi", "synonyms": ["alamat", "letak"]},
            {"value": "fasilitas", "synonyms": ["fitur", "sarana"]}
        ]
    }
    
    # Data manual untuk kiano_projects
    kiano_projects = {
        "display_name": "kiano_projects",
        "kind": "KIND_MAP",
        "entities": [
            {"value": "Kiano 1", "synonyms": ["Kiano Satu"]},
            {"value": "Kiano 2", "synonyms": ["Kiano Dua"]}
        ]
    }

    # Simpan perbaikan
    with open(entities_dir / "jenis_info_kiano.json", 'w', encoding='utf-8') as f:
        json.dump(jenis_info, f, indent=2, ensure_ascii=False)
    
    with open(entities_dir / "kiano_projects.json", 'w', encoding='utf-8') as f:
        json.dump(kiano_projects, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("🔧 Patching empty entities...")
    fix_empty_entities()
    print("✅ Entities fixed! Please verify with verify_conversion.py")