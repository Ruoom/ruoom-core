import logging
import uuid

from django.conf import settings

try:
    import googlemaps
except ImportError:  # pragma: no cover - availability is exercised through runtime fallback.
    googlemaps = None


logger = logging.getLogger(__name__)


class GeocodingService:
    """Core address lookup boundary for features that need place suggestions."""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        api_key = getattr(settings, "GOOGLE_PLACES_API_KEY", "")
        if not api_key or googlemaps is None or self._client is not None:
            return
        try:
            self._client = googlemaps.Client(key=api_key)
        except Exception as exc:
            logger.error("Failed to initialize Google Maps client: %s", exc)
            self._client = None

    @property
    def client(self):
        if self._client is None:
            self._initialize()
        return self._client

    def is_available(self):
        return self.client is not None

    def autocomplete_address(self, input_text, city_bias=None, session_token=None):
        if not self.is_available():
            return []
        try:
            components = f"country:us|locality:{city_bias.lower()}" if city_bias else None
            result = self.client.places_autocomplete(
                input_text=input_text,
                session_token=session_token or str(uuid.uuid4()),
                components=components,
                types="address",
            )
        except Exception as exc:
            logger.error("Error getting autocomplete suggestions for '%s': %s", input_text, exc)
            return []

        suggestions = []
        for prediction in result:
            structured = prediction.get("structured_formatting", {})
            suggestions.append(
                {
                    "description": prediction.get("description", ""),
                    "place_id": prediction.get("place_id", ""),
                    "main_text": structured.get("main_text", prediction.get("description", "")),
                    "secondary_text": structured.get("secondary_text", ""),
                }
            )
        return suggestions

    def place_details(self, place_id):
        if not self.is_available():
            return {}
        try:
            result = self.client.place(place_id=place_id)
        except Exception as exc:
            logger.error("Error getting place details for '%s': %s", place_id, exc)
            return {}

        place = result.get("result", {})
        details = {
            "formatted_address": place.get("formatted_address", ""),
            "place_id": place_id,
            "street_number": "",
            "route": "",
            "city": "",
            "state": "",
            "zipcode": "",
        }
        for component in place.get("address_components", []):
            types = component.get("types", [])
            if "street_number" in types:
                details["street_number"] = component.get("long_name", "")
            elif "route" in types:
                details["route"] = component.get("long_name", "")
            elif "locality" in types:
                details["city"] = component.get("long_name", "")
            elif "administrative_area_level_1" in types:
                details["state"] = component.get("short_name", "")
            elif "postal_code" in types:
                details["zipcode"] = component.get("long_name", "")

        street = (details["street_number"] + " " + details["route"]).strip()
        details["street"] = street or details["formatted_address"]
        return details


def get_geocoding_service():
    return GeocodingService()
