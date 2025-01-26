from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="CarLogix Loading Optimizer")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CarLogix Vehicle Manager</title>
    </head>
    <body>
        <div id="root"></div>
        <script type="module">
            import { createRoot } from 'react-dom/client';
            import VehicleManager from './VehicleManager';

            createRoot(document.getElementById('root')).render(<VehicleManager />);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)