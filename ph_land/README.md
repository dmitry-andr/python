# ph_land

A simple FastAPI web app with a landing page and basic REST endpoints.

## Run locally

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  - linux
   .\.venv\Scripts\activate.bat - windows

   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Open the landing page:
   ```
   http://127.0.0.1:8000/
   ```

## API endpoints

- `GET /api/health`
- `GET /api/orders`
- `GET /api/orders/{order_id}`


4. .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=  ... 
WORKSPACE_FOLDER_PATH = user/my_workspace/

5. RAG Init - alternative for UI
Place your business data files (.md or .txt) in rag_context_data at the repository root (or point --source to another folder).
Run the script to build the Chroma DB (or force rebuild):

#force rebuild
python -m app.llm.rag.rag_data_init_from_files --force

What this does

Loads .md and .txt files from the source folder
Splits them into chunks and embeds with the configured EMBEDDING_MODEL
Persists a Chroma vector DB to VECTOR_DB_DIR (used by get_retriever())

