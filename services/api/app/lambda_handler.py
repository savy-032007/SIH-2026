"""AWS Lambda entry point for the FastAPI application.

The standard ASGI app remains the source of truth for local Uvicorn and Docker
Compose. Mangum only adapts incoming Lambda Function URL events to ASGI.
"""

from mangum import Mangum

from app.main import app

# The API has no startup work that Lambda needs to repeat per invocation.
# Disabling ASGI lifespan avoids running shutdown hooks after every request.
handler = Mangum(app, lifespan="off")
