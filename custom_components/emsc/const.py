"""Constants for the Earthquake Monitoring integration."""
DOMAIN = "seismicportal"

CONF_MIN_MAGNITUDE = "min_magnitude"
CONF_RADIUS = "radius"

DEFAULT_MIN_MAGNITUDE = 3.0
DEFAULT_RADIUS = 500.0  # km

WS_URI = "wss://www.seismicportal.eu/standing_order/websocket"

EVENT_EARTHQUAKE_DETECTED = "zemetrasenia.earthquake_detected"

ATTR_MAGNITUDE = "magnitude"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"
ATTR_LOCALITY = "locality"
ATTR_TIME = "time"
