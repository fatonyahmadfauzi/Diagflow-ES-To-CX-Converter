import os
import json
import time
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx
from google.api_core.exceptions import AlreadyExists

# System intents that shouldn't be deleted or recreated
SYSTEM_INTENTS = [
    'Default Welcome Intent',
    'Default Negative Intent',
    'Default Fallback Intent'
]

def is_intent_used(flows_client, pages_client, agent_path, intent_display_name):
    """Check if intent is referenced in any flow or page transition routes."""
    flows = flows_client.list_flows(parent=agent_path)
    for flow in flows:
        # Check flow-level transition routes
        flow_obj = flows_client.get_flow(name=flow.name)
        for route in getattr(flow_obj, "transition_routes", []):
            if getattr(route, "intent", "") == intent_display_name:
                return True

        # Check pages in this flow
        pages = pages_client.list_pages(parent=flow.name)
        for page in pages:
            page_obj = pages_client.get_page(name=page.name)
            for route in getattr(page_obj, "transition_routes", []):
                if getattr(route, "intent", "") == intent_display_name:
                    return True
    return False

def delete_all_intents(client, agent_path, flows_client, pages_client):
    """Safely delete all non-system intents only if they're not in use."""
    intents = list(client.list_intents(parent=agent_path))
    
    for intent in intents:
        intent_name = intent.name
        intent_display_name = intent.display_name

        if intent_display_name in SYSTEM_INTENTS:
            print(f"⏩ Skipping system intent: {intent_display_name}")
            continue

        print(f"🔍 Checking usage of intent: {intent_display_name}")

        # Check if intent is still referenced
        if is_intent_used(flows_client, pages_client, agent_path, intent_display_name):
            print(f"⛔ Cannot delete '{intent_display_name}' — still in use")
            continue

        try:
            client.delete_intent(name=intent_name)
            print(f"🗑️ Deleted intent: {intent_display_name}")
        except Exception as e:
            print(f"❌ Failed to delete intent '{intent_display_name}': {e}")

def check_entity_exists(entity_client, agent_path, entity_name):
    """Check if entity exists in the agent"""
    try:
        for entity in entity_client.list_entity_types(parent=agent_path):
            if entity.display_name == entity_name:
                return True
        return False
    except Exception as e:
        print(f"⚠️ Error checking entity {entity_name}: {str(e)}")
        return False

def convert_intents(intents_client, agent_path, intents_path, agent_id, entity_client):
    """Convert Dialogflow ES intents to CX format with proper parameter handling"""
    # First collect all training phrases from _usersays_ files
    training_data = {}
    
    # Load all user says files first
    print("\n🔍 Loading training phrases from user says files...")
    for file in os.listdir(intents_path):
        if "_usersays_" in file:
            try:
                base_name = file.split("_usersays_")[0]
                file_path = os.path.join(intents_path, file)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        if base_name not in training_data:
                            training_data[base_name] = []
                        training_data[base_name].extend(data)
            except Exception as e:
                print(f"⚠️ Error loading {file}: {e}")

    # Process main intent files
    print("\n🔄 Converting intents...")
    for file in os.listdir(intents_path):
        if "_usersays_" in file or not file.endswith(".json"):
            continue

        display_name = os.path.splitext(file)[0]
        
        # Skip system intents
        if display_name in SYSTEM_INTENTS:
            print(f"⏩ Skipping system intent: {display_name}")
            continue
        
        # Get phrases from collected data
        phrases = training_data.get(display_name, [])
        
        # Prepare training phrases
        training_phrases = []
        parameters = set()
        
        for phrase in phrases:
            parts = []
            for part in phrase.get("data", []):
                text = part.get("text", "").strip()
                alias = part.get("alias", "").strip()
                
                if text:
                    part_data = {"text": text}
                    if alias:
                        param_id = alias.lower().replace(" ", "_")
                        part_data["parameter_id"] = param_id
                        parameters.add(param_id)
                    parts.append(part_data)
            
            if parts:
                training_phrases.append({
                    "parts": parts,
                    "repeat_count": 1
                })

        if not training_phrases:
            print(f"⚠️ No valid phrases for {display_name}")
            continue

        # Create intent with proper entity references
        intent = {
            "display_name": display_name,
            "training_phrases": training_phrases
        }

        project_id = agent_path.split('/')[1]
        location = agent_path.split('/')[3]
        
        if parameters:
            # Get the actual entity IDs from the agent
            entity_id_map = {}
            for entity in entity_client.list_entity_types(parent=agent_path):
                entity_id_map[entity.display_name] = entity.name.split('/')[-1]
            
            intent["parameters"] = []
            for param in parameters:
                if param in entity_id_map:
                    intent["parameters"].append({
                        "id": param,
                        "entity_type": f"projects/{project_id}/locations/{location}/agents/{agent_id}/entityTypes/{entity_id_map[param]}",
                        "is_list": False,
                        "redact": False
                    })
                else:
                    print(f"⛔ Parameter '{param}' references missing entity")
                    return  # Skip this intent entirely if any parameter is invalid
            
        try:
            response = intents_client.create_intent(
                parent=agent_path,
                intent=intent
            )
            print(f"✅ Created intent: {display_name}")
        except AlreadyExists:
            print(f"⏩ Intent already exists: {display_name}")
        except Exception as e:
            print(f"❌ Failed to create {display_name}: {e}")