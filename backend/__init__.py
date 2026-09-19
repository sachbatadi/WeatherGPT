"""
WeatherGPT Web Backend Package (backend/).

Provides the FastAPI REST API layer exposing:
- GET /api/health
- GET /api/weather/current
- POST /api/pipeline/run
- GET /api/farmers
- GET /api/farmers/{farmer_id}/dashboard
- GET /api/alerts
"""

from .app import app

__all__ = ["app"]
