"""Tests for the topology coordinate mapper.

Validates city-to-coordinate mapping for the tactical map.
"""

import pytest

from adapters.inbound.api.topology_mapper import _CITY_COORDINATES, get_city_coordinates


class TestCityCoordinates:
    def test_all_eight_cities_present(self) -> None:
        """All 8 Argentine cities must have coordinate entries."""
        expected_cities = [
            "Buenos Aires",
            "Córdoba",
            "Rosario",
            "Mendoza",
            "Tucumán",
            "La Plata",
            "Mar del Plata",
            "Salta",
        ]
        for city in expected_cities:
            assert city in _CITY_COORDINATES, f"Missing coordinates for {city}"

    def test_buenos_aires_coordinates(self) -> None:
        """Buenos Aires has correct lat/lng and SVG coordinates."""
        coords = _CITY_COORDINATES["Buenos Aires"]
        assert coords["lat"] == pytest.approx(-34.6037, abs=0.0001)
        assert coords["lng"] == pytest.approx(-58.3816, abs=0.0001)
        assert coords["x"] == pytest.approx(620.0, abs=0.1)
        assert coords["y"] == pytest.approx(620.0, abs=0.1)

    def test_cordoba_coordinates(self) -> None:
        """Córdoba has correct lat/lng and SVG coordinates."""
        coords = _CITY_COORDINATES["Córdoba"]
        assert coords["lat"] == pytest.approx(-31.4201, abs=0.0001)
        assert coords["lng"] == pytest.approx(-64.1888, abs=0.0001)
        assert coords["x"] == pytest.approx(480.0, abs=0.1)
        assert coords["y"] == pytest.approx(450.0, abs=0.1)

    def test_rosario_coordinates(self) -> None:
        """Rosario has correct lat/lng and SVG coordinates."""
        coords = _CITY_COORDINATES["Rosario"]
        assert coords["lat"] == pytest.approx(-32.9442, abs=0.0001)
        assert coords["lng"] == pytest.approx(-60.6505, abs=0.0001)

    def test_mendoza_coordinates(self) -> None:
        """Mendoza has correct lat/lng and SVG coordinates."""
        coords = _CITY_COORDINATES["Mendoza"]
        assert coords["lat"] == pytest.approx(-32.8895, abs=0.0001)
        assert coords["lng"] == pytest.approx(-68.8458, abs=0.0001)

    def test_tucuman_coordinates(self) -> None:
        """Tucumán has correct lat/lng and SVG coordinates."""
        coords = _CITY_COORDINATES["Tucumán"]
        assert coords["lat"] == pytest.approx(-26.8083, abs=0.0001)
        assert coords["lng"] == pytest.approx(-65.2176, abs=0.0001)

    def test_la_plata_coordinates(self) -> None:
        """La Plata has correct lat/lng and SVG coordinates."""
        coords = _CITY_COORDINATES["La Plata"]
        assert coords["lat"] == pytest.approx(-34.9215, abs=0.0001)
        assert coords["lng"] == pytest.approx(-57.9545, abs=0.0001)

    def test_mar_del_plata_coordinates(self) -> None:
        """Mar del Plata has correct lat/lng and SVG coordinates."""
        coords = _CITY_COORDINATES["Mar del Plata"]
        assert coords["lat"] == pytest.approx(-38.0055, abs=0.0001)
        assert coords["lng"] == pytest.approx(-57.5426, abs=0.0001)

    def test_salta_coordinates(self) -> None:
        """Salta has correct lat/lng and SVG coordinates."""
        coords = _CITY_COORDINATES["Salta"]
        assert coords["lat"] == pytest.approx(-24.7821, abs=0.0001)
        assert coords["lng"] == pytest.approx(-65.4232, abs=0.0001)


class TestGetCityCoordinates:
    def test_known_city_returns_coords(self) -> None:
        """get_city_coordinates returns coordinates for known cities."""
        coords = get_city_coordinates("Buenos Aires")
        assert coords["lat"] == pytest.approx(-34.6037, abs=0.0001)

    def test_unknown_city_returns_zeros(self) -> None:
        """get_city_coordinates returns zero coordinates for unknown cities."""
        coords = get_city_coordinates("Unknown City")
        assert coords["lat"] == 0.0
        assert coords["lng"] == 0.0
        assert coords["x"] == 0.0
        assert coords["y"] == 0.0
