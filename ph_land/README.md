# ph_land

A simple FastAPI web app with a landing page and basic REST endpoints.

## Run locally

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
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


4. Add OPENAI_API_KEY=  ...   in .env file
