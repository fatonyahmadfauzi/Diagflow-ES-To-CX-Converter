# Konfigurasi koreksi nama
NAME_CORRECTIONS = {
    # Entities
    "jenis_info_klano": "jenis_info_kiano",
    "klano_projects": "kiano_projects",
    
    # Intents
    "CariRumab_Awal": "CariRumah_Awal"
}

ENTITY_SYNONYM_ADDITIONS = {
    "jenis_info_kiano": {
        "harga": ["tarif", "budget"],
        "lokasi": ["alamat", "letak"]
    },
    "kiano_projects": {
        "Kiano 1": ["Kiano Satu"],
        "Green Jonggol Village": ["GV"]
    }
}