# HR AI Assistant UI

React UI for the FastAPI `/ask` endpoint.

## Run

```bash
npm install
npm run dev
```

The UI runs on `http://127.0.0.1:5173` by default.

## API URL

By default, the app calls:

```text
http://localhost:8000/ask
```

To point it somewhere else, create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

The API expects:

```json
{
  "question": "who joined earlier saurabh or shanky"
}
```
