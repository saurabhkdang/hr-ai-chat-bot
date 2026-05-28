# HR AI Chatbot Widget

Standalone bottom-right chatbot widget for any existing HR panel.

## Use

Add this before the closing `</body>` tag of your existing page:

```html
<script
  src="./hr-chatbot-widget.js"
  data-api-base-url="http://localhost:8000"
></script>
```

The widget calls:

```text
POST /ask
```

with:

```json
{
  "question": "leave balance of saurabh"
}
```

## Demo

Run a small static server while your FastAPI service is running:

```bash
cd chatbot-widget
python -m http.server 5500
```

Then open:

```text
http://localhost:5500/demo.html
```

For production, add your HR panel domain to the FastAPI CORS allowlist in `main.py`.
