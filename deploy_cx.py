from google.cloud import dialogflowcx_v3beta1 as df
from google.oauth2 import service_account
import json
from pathlib import Path
import time
from typing import Dict, List

class CXDeployer:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.credentials = service_account.Credentials.from_service_account_file(
            self.config["service_account_path"]
        )
        self.client_options = {
            "api_endpoint": f"{self.config['location']}-dialogflow.googleapis.com"
        }
        self.agent_path = (
            f"projects/{self.config['project_id']}/locations/{self.config['location']}"
            f"/agents/{self.config['agent_id']}"
        )

    def _get_existing_entity(self, display_name: str):
        entity_client = df.EntityTypesClient(
            credentials=self.credentials,
            client_options=self.client_options
        )
        for entity in entity_client.list_entity_types(parent=self.agent_path):
            if entity.display_name == display_name:
                return entity
        return None

    def _get_existing_intent(self, display_name: str):
        intent_client = df.IntentsClient(
            credentials=self.credentials,
            client_options=self.client_options
        )
        for intent in intent_client.list_intents(parent=self.agent_path):
            if intent.display_name == display_name:
                return intent
        return None

    def deploy_entity(self, entity_file: Path) -> str:
        entity_client = df.EntityTypesClient(
            credentials=self.credentials,
            client_options=self.client_options
        )

        with open(entity_file, 'r', encoding='utf-8') as f:
            entity_data = json.load(f)

        display_name = entity_data["display_name"]
        existing_entity = self._get_existing_entity(display_name)

        entity_type = df.EntityType(
            display_name=display_name,
            kind=entity_data["kind"],
            entities=[
                df.EntityType.Entity(value=e["value"], synonyms=e["synonyms"])
                for e in entity_data["entities"]
            ]
        )

        try:
            if existing_entity:
                entity_type.name = existing_entity.name
                response = entity_client.update_entity_type(
                    entity_type=entity_type,
                    update_mask={"paths": ["entities"]}
                )
                print(f"✅ Entity updated: {response.display_name}")
            else:
                response = entity_client.create_entity_type(
                    parent=self.agent_path,
                    entity_type=entity_type
                )
                print(f"✅ Entity created: {response.display_name}")
            return response.name
        except Exception as e:
            print(f"❌ Failed to deploy {display_name}: {str(e)}")
            return None

    def deploy_intent(self, intent_file: Path, entity_map: Dict[str, str]) -> str:
        intent_client = df.IntentsClient(
            credentials=self.credentials,
            client_options=self.client_options
        )

        with open(intent_file, 'r', encoding='utf-8') as f:
            intent_data = json.load(f)

        display_name = intent_data["display_name"]
        existing_intent = self._get_existing_intent(display_name)

        parameters = []
        param_ids = []
        
        if "parameters" in intent_data:
            for param in intent_data["parameters"]:
                param_id = param["id"]
                entity_type = param.get("entity_type", "")
                
                # Handle location specially
                if param_id == "location":
                    if "location" in entity_map:
                        parameters.append(df.Intent.Parameter(
                            id=param_id,
                            entity_type=entity_map["location"],
                            is_list=param.get("is_list", False)
                        ))
                        param_ids.append(param_id)
                        print(f"🔧 Using custom entity for location parameter")
                    else:
                        print(f"⚠️ Location entity not found, using sys.location")
                        parameters.append(df.Intent.Parameter(
                            id=param_id,
                            entity_type="sys.location",
                            is_list=param.get("is_list", False)
                        ))
                        param_ids.append(param_id)
                # Handle @sys.any conversion
                elif entity_type == "@sys.any":
                    if param_id in entity_map:
                        parameters.append(df.Intent.Parameter(
                            id=param_id,
                            entity_type=entity_map[param_id],
                            is_list=param.get("is_list", False)
                        ))
                        param_ids.append(param_id)
                        print(f"🔧 Converted @sys.any to custom entity for {param_id}")
                    else:
                        print(f"⚠️ No entity mapping for {param_id}, skipping parameter")
                elif param_id in entity_map:
                    parameters.append(df.Intent.Parameter(
                        id=param_id,
                        entity_type=entity_map[param_id],
                        is_list=param.get("is_list", False)
                    ))
                    param_ids.append(param_id)

        training_phrases = []
        for phrase in intent_data["training_phrases"]:
            filtered_parts = []
            for part in phrase["parts"]:
                if "parameter_id" in part:
                    if part["parameter_id"] in param_ids:
                        filtered_parts.append(part)
                    else:
                        filtered_parts.append({"text": part["text"]})
                        print(f"⚠️ Converted parameter '{part['parameter_id']}' to text")
                else:
                    filtered_parts.append(part)
            
            training_phrases.append({
                "parts": filtered_parts,
                "repeat_count": phrase.get("repeat_count", 1)
            })

        intent = df.Intent(
            display_name=display_name,
            training_phrases=[
                df.Intent.TrainingPhrase(
                    parts=[
                        df.Intent.TrainingPhrase.Part(
                            text=p["text"],
                            parameter_id=p.get("parameter_id") if "parameter_id" in p else None
                        )
                        for p in phrase["parts"]
                    ],
                    repeat_count=phrase.get("repeat_count", 1)
                )
                for phrase in training_phrases
            ],
            parameters=parameters
        )

        try:
            if existing_intent:
                intent.name = existing_intent.name
                response = intent_client.update_intent(
                    intent=intent,
                    update_mask={"paths": ["training_phrases", "parameters"]}
                )
                print(f"✅ Intent updated: {response.display_name}")
            else:
                response = intent_client.create_intent(
                    parent=self.agent_path,
                    intent=intent
                )
                print(f"✅ Intent created: {response.display_name}")
            return response.name
        except Exception as e:
            print(f"❌ Failed to deploy {display_name}: {str(e)}")
            return None

    def deploy_all(self):
        print("🚀 Starting deployment to Dialogflow CX...")
        
        # First deploy entities
        entity_files = list(Path("output_cx/entities").glob("*.json"))
        entity_map = {}
        
        print("\n🔧 Deploying entities...")
        print("Found entity files:", [f.name for f in entity_files])  # Debug
        
        for entity_file in entity_files:
            entity_path = self.deploy_entity(entity_file)
            if entity_path:
                entity_name = entity_file.stem
                entity_map[entity_name] = entity_path
                print(f" - Mapped {entity_name} to {entity_path}")  # Debug

        print("\nFinal entity map:", entity_map)  # Debug
        print("\n⏳ Waiting for entities to propagate...")
        time.sleep(20)

        intent_files = list(Path("output_cx/intents").glob("*.json"))
        
        print("\n🔧 Deploying intents...")
        for intent_file in intent_files:
            self.deploy_intent(intent_file, entity_map)

        print("\n🎉 Deployment completed!")
        print(f"Agent URL: https://dialogflow.cloud.google.com/cx/projects/{self.config['project_id']}/locations/{self.config['location']}/agents/{self.config['agent_id']}")

if __name__ == "__main__":
    deployer = CXDeployer()
    deployer.deploy_all()