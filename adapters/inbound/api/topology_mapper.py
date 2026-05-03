"""Topology Mapper — Adapter layer coordinate mapping and DTO conversion.

This module lives in the adapter layer (infrastructure concern).
It maps domain entities to presentation DTOs and adds geographic
coordinates that are NOT part of the domain model.
"""

from core.domain.entities import Branch

# Real lat/lng and artistic SVG coordinates for 8 Argentine cities.
# Coordinates are presentation concerns and belong in the adapter layer.
_CITY_COORDINATES: dict[str, dict[str, float]] = {
    "Buenos Aires": {
        "lat": -34.6037,
        "lng": -58.3816,
        "x": 620.0,
        "y": 620.0,
    },
    "Córdoba": {
        "lat": -31.4201,
        "lng": -64.1888,
        "x": 480.0,
        "y": 450.0,
    },
    "Rosario": {
        "lat": -32.9442,
        "lng": -60.6505,
        "x": 550.0,
        "y": 520.0,
    },
    "Mendoza": {
        "lat": -32.8895,
        "lng": -68.8458,
        "x": 320.0,
        "y": 480.0,
    },
    "Tucumán": {
        "lat": -26.8083,
        "lng": -65.2176,
        "x": 420.0,
        "y": 280.0,
    },
    "La Plata": {
        "lat": -34.9215,
        "lng": -57.9545,
        "x": 670.0,
        "y": 650.0,
    },
    "Mar del Plata": {
        "lat": -38.0055,
        "lng": -57.5426,
        "x": 700.0,
        "y": 740.0,
    },
    "Salta": {
        "lat": -24.7821,
        "lng": -65.4232,
        "x": 380.0,
        "y": 220.0,
    },
}


def get_city_coordinates(city: str) -> dict[str, float]:
    """Return coordinates for a given city.

    Args:
        city: City name as assigned by TopologyFactory.

    Returns:
        dict with lat, lng, x, y. Returns zeros for unknown cities.
    """
    return _CITY_COORDINATES.get(city, {"lat": 0.0, "lng": 0.0, "x": 0.0, "y": 0.0})
