import sys
import os
import time
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx
from google.oauth2 import service_account
from config import PROJECT_ID, LOCATION, AGENT_ID, SERVICE_ACCOUNT_FILE, ZIP_PATH, EXTRACT_PATH
from utils.extract_zip import extract_zip
from utils.convert_intents import convert_intents, delete_all_intents
from utils.convert_entities import convert_entities, delete_all_entities
from utils.clean_flows import remove_transition_routes

def verify_entity_fully_created(entity_client, agent_path, entity_name):
    """Verify entity exists and is fully provisioned"""
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            for entity in entity_client.list_entity_types(parent=agent_path):
                if entity.display_name == entity_name:
                    # Try to get the full entity details
                    full_entity = entity_client.get_entity_type(name=entity.name)
                    if full_entity:
                        print(f"✓ Entity verified: {entity_name} (Attempt {attempt + 1})")
                        return True
            print(f"⚠️ Entity not found yet: {entity_name} (Attempt {attempt + 1})")
        except Exception as e:
            print(f"⚠️ Error checking entity {entity_name}: {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    return False

def main():
    # 🔐 Setup credentials
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
    api_endpoint = f"{LOCATION}-dialogflow.googleapis.com"

    # 🔧 Initialize clients
    clients = {
        'intents': dialogflowcx.IntentsClient(
            credentials=credentials,
            client_options={"api_endpoint": api_endpoint}
        ),
        'entities': dialogflowcx.EntityTypesClient(
            credentials=credentials,
            client_options={"api_endpoint": api_endpoint}
        ),
        'flows': dialogflowcx.FlowsClient(
            credentials=credentials,
            client_options={"api_endpoint": api_endpoint}
        ),
        'pages': dialogflowcx.PagesClient(
            credentials=credentials,
            client_options={"api_endpoint": api_endpoint}
        )
    }

    # 🧠 Agent path
    agent_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/agents/{AGENT_ID}"

    try:
        print("🚀 Starting Dialogflow ES to CX migration")
        
        # 📁 Extract ZIP
        print("\n🔍 Extracting ZIP file...")
        extract_zip(ZIP_PATH, EXTRACT_PATH)

        # 🧹 Clean transition routes
        print("\n🧹 Cleaning transition routes...")
        remove_transition_routes(clients['flows'], agent_path)

        # 🗑️ Delete existing intents and entities
        print("\n🗑️ Cleaning existing intents and entities...")
        delete_all_intents(clients['intents'], agent_path, clients['flows'], clients['pages'])
        delete_all_entities(clients['entities'], agent_path)

        # 🔄 Convert entities FIRST
        print("\n🔄 Converting entities...")
        entities_path = os.path.join(EXTRACT_PATH, "entities")
        convert_entities(clients['entities'], agent_path, entities_path)

        # Add delay for entities to propagate
        print("\n⏳ Waiting 20 seconds for entities to propagate...")
        time.sleep(20)

        # Verifikasi entities telah dibuat
        print("\n🔍 Verifying created entities...")
        required_entities = ['jenis_info_kiano', 'kiano_projects', 'location']
        all_entities_ready = True
        
        for entity_name in required_entities:
            if not verify_entity_fully_created(clients['entities'], agent_path, entity_name):
                print(f"❌ Critical Error: Entity {entity_name} not fully provisioned!")
                all_entities_ready = False
        
        if not all_entities_ready:
            print("⛔ Some entities failed to provision properly")
            sys.exit(1)

        # 🔄 Then convert intents with proper entity client reference
        print("\n🔄 Converting intents...")
        intents_path = os.path.join(EXTRACT_PATH, "intents")
        convert_intents(
            clients['intents'], 
            agent_path, 
            intents_path, 
            AGENT_ID,
            clients['entities']  # Pass the entity client
        )

        print("\n✅ Migration completed successfully!")
    
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def check_entity_exists(client, agent_path, entity_name):
    """Check if entity exists in the agent"""
    try:
        for entity in client.list_entity_types(parent=agent_path):
            if entity.display_name == entity_name:
                return True
        return False
    except Exception as e:
        print(f"⚠️ Error checking entity {entity_name}: {str(e)}")
        return False

if __name__ == "__main__":
    main()