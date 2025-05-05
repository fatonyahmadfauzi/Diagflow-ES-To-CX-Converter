import json
import os
from google.cloud.dialogflowcx_v3beta1.types import EntityType

def delete_all_entities(client, agent_path):
    """Delete all existing entities"""
    entities = client.list_entity_types(parent=agent_path)
    for entity in entities:
        try:
            client.delete_entity_type(name=entity.name)
            print(f"🗑️ Deleted entity: {entity.display_name}")
        except Exception as e:
            print(f"❌ Failed to delete entity {entity.display_name}: {e}")

def convert_entities(client, agent_path, entities_path):
    """Create entities with exact display names matching parameter IDs"""
    entity_map = {
        'jenis_info_kiano': {
            'display_name': 'jenis_info_kiano',  # Must match exactly
            'kind': 'KIND_MAP',
            'entities': [
                {'value': 'harga', 'synonyms': ['biaya', 'tarif', 'budget', 'uang', 'cicilan']},
                {'value': 'fasilitas', 'synonyms': ['keunggulan', 'fitur', 'sarana', 'akses']},
                {'value': 'promo', 'synonyms': ['diskon', 'penawaran', 'program', 'KPR Zero']},
                {'value': 'lokasi', 'synonyms': ['alamat', 'letak', 'daerah']},
                {'value': 'soldout', 'synonyms': ['sold out', 'habis', 'tidak tersedia']},
                {'value': 'keunggulan', 'synonyms': ['kelebihan', 'keistimewaan']},
                {'value': 'ketersediaan', 'synonyms': ['stok', 'ready stock']},
                {'value': 'perbandingan', 'synonyms': ['bandingkan', 'vs', 'dibanding']},
                {'value': 'spesifikasi', 'synonyms': ['detail teknis', 'bahan bangunan', 'struktur']}
            ]
        },
        'kiano_projects': {
            'display_name': 'kiano_projects',  # Must match exactly
            'kind': 'KIND_MAP',
            'entities': [
                {'value': 'Kiano 1', 'synonyms': ['Kiano Satu', 'Proyek Kiano 1', 'Perumahan Kiano 1']},
                {'value': 'Kiano 2', 'synonyms': ['Kiano Dua', 'Proyek Kiano 2', 'Perumahan Kiano 2']},
                {'value': 'Kiano 3', 'synonyms': ['Kiano Tiga', 'Proyek Kiano 3', 'Perumahan Kiano 3']},
                {'value': 'Green Jonggol Village', 'synonyms': ['Green Jonggol', 'Proyek Green Jonggol']}
            ]
        },
        'location': {
            'display_name': 'location',  # Must match exactly
            'kind': 'KIND_MAP',
            'entities': [
                {'value': 'Green Jonggol Village', 'synonyms': ['GV']},
                {'value': 'BTN', 'synonyms': ['Bank Tabungan Negara']}
            ]
        }
    }

    for entity_id, entity_data in entity_map.items():
        try:
            # Explicitly create EntityType object
            entity_type = EntityType(
                display_name=entity_data['display_name'],
                kind=entity_data['kind'],
                entities=entity_data['entities']
            )
            
            response = client.create_entity_type(
                parent=agent_path,
                entity_type=entity_type
            )
            print(f"✅ Created entity: {response.display_name} (ID: {response.name.split('/')[-1]})")
        except Exception as e:
            print(f"❌ Failed to create {entity_id}: {e}")