# Dialogflow ES to CX Converter

A migration tool to convert Dialogflow ES agents to Dialogflow CX format with proper entity and intent handling.

## Features

- 🗂️ Extracts ZIP package from Dialogflow ES
- 🧹 Cleans existing CX agent (intents, entities, flows)
- 🔄 Converts ES entities to CX format with synonyms
- 💬 Migrates intents with training phrases and parameters
- ✅ Handles system intents and entity validation

## Prerequisites

- Python 3.7+
- Google Cloud SDK
- Dialogflow CX API enabled
- Service account credentials

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/fatonyahmadfauzi/dialogflow-es-to-cx-converter.git
   cd dialogflow-es-to-cx-converter
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. You can use either `config.py` or `config.json`:
   ```python
   # config.py example
   PROJECT_ID = "your-project-id"
   LOCATION = "your-region"  # e.g., "asia-southeast1"
   AGENT_ID = "your-agent-id"
   SERVICE_ACCOUNT_FILE = "path/to/service-account.json"
   ZIP_PATH = "path/to/your-es-agent.zip"
   EXTRACT_PATH = "extracted"
   ```
   ```json
   // config.json example
   {
     "project_id": "your-project-id",
     "location": "your-region",
     "agent_id": "your-agent-id",
     "service_account_path": "service-account.json"
   }
   ```
2. Place your Dialogflow ES export ZIP file in the specified location

## Features

- 🛠️ Manual entity patching (`patch_entities.py`)
- 🔍 Conversion verification (`verify_conversion.py`)
- 🔄 Name correction mapping (`fix_names_config.py`)
- 🚀 Direct deployment to CX (`deploy_cx.py`)

## Usage

Run the migration script:

```bash
python main.py
```

1. Convert ES to CX format:
   ```bash
   python converter.py
   ```
2. (Optional) Patch entities if needed:
   ```bash
   python patch_entities.py
   ```
3. Verify conversion:
   ```bash
   python verify_conversion.py
   ```
4. Deploy to Dialogflow CX:
   ```bash
   python deploy_cx.py
   ```

## Migration Process

1. Extracts the ES agent ZIP
2. Deletes existing CX intents/entities (except system ones)
3. Creates new entities with proper synonyms
4. Converts intents with training phrases
5. Links parameters to entities

## Troubleshooting

### Common Issues

**Entity not found errors:**

- Ensure entity names match exactly (case-sensitive)
- Verify service account has "Dialogflow API Admin" role

**Intent creation fails:**

- Check training phrases for special characters
- Verify no duplicate intent names exist

**Deployment fails:**

- Verify service account has proper roles
- Check entity names match exactly
- Run `verify_conversion.py` before deploying

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first.
