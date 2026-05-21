from __future__ import annotations

import os
import webbrowser
from pathlib import Path

import uvicorn
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ecommerce_product_image_workflow.backend.app import create_app


def main() -> None:
    host = os.environ.get("EPI_HOST", "127.0.0.1")
    port = int(os.environ.get("EPI_PORT", "8787"))
    app = create_app()
    frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    else:
        @app.get("/", response_class=HTMLResponse)
        def frontend_missing() -> str:
            return """
            <main style="font-family: system-ui; max-width: 760px; margin: 48px auto; line-height: 1.5">
              <h1>E-commerce Product Image Workflow</h1>
              <p>The API is running, but the frontend has not been built yet.</p>
              <pre style="background:#f1f5f9;padding:16px">cd frontend
npm install
npm run build
cd ..
python3 -m ecommerce_product_image_workflow.web</pre>
            </main>
            """
    if os.environ.get("EPI_NO_BROWSER") != "1":
        webbrowser.open(f"http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
