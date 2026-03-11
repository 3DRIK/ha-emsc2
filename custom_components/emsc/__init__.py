"""The Earthquake Monitoring integration for seismicportal.eu."""
import asyncio
import logging
import voluptuous as vol
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import device_registry as dr
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS
import homeassistant.helpers.config_validation as cv
import websockets
import json

from .const import (
    DOMAIN,
    CONF_MIN_MAGNITUDE,
    DEFAULT_MIN_MAGNITUDE,
    DEFAULT_RADIUS,
    WS_URI,
    EVENT_EARTHQUAKE_DETECTED,
    ATTR_MAGNITUDE,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_LOCALITY,
    ATTR_TIME,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Earthquake Monitoring from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize WebSocket client and data handler
    ws_client = EarthquakeWebSocketClient(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = ws_client

    # Start WebSocket connection
    await ws_client.async_connect()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        ws_client = hass.data[DOMAIN][entry.entry_id]
        await ws_client.async_disconnect()
        del hass.data[DOMAIN][entry.entry_id]

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

class EarthquakeWebSocketClient:
    """WebSocket client for seismicportal.eu."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the WebSocket client."""
        self.hass = hass
        self.entry = entry
        self.websocket = None
        self._unsub_interval = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5

    async def async_connect(self):
        """Connect to the WebSocket server."""
        _LOGGER.info("Attempting to connect to %s", WS_URI)
        await self._async_connect_websocket()
        
    async def async_disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            _LOGGER.info("Disconnected from seismicportal.eu WebSocket")

    async def _async_connect_websocket(self):
        """Establish WebSocket connection."""
        try:
            self.websocket = await websockets.connect(WS_URI, ping_interval=15, ssl=False)
            _LOGGER.info("Connected to seismicportal.eu WebSocket")
            self._reconnect_attempts = 0
            self.hass.async_create_task(self._async_handle_messages())
        except Exception as e:
            _LOGGER.error("Error connecting to WebSocket: %s", e)
            await self._async_schedule_reconnect()

    async def _async_handle_messages(self):
        """Handle incoming WebSocket messages."""
        _LOGGER.info("Received earthquake message")
        try:
            async for message in self.websocket:
                _LOGGER.info("Parsing message: %s", message)
                data = json.loads(message)
                if self._filter_earthquake(data):
                    await self._async_dispatch_event(data)
        except websockets.exceptions.ConnectionClosed:
            _LOGGER.warning("WebSocket connection closed")
            await self._async_schedule_reconnect()
        except Exception as e:
            _LOGGER.error("Error handling WebSocket message: %s", e)
            await self._async_schedule_reconnect()

    def _filter_earthquake(self, data: dict) -> bool:
        """Filter earthquake data based on user config."""
        if data.get("mag", 0) < self.entry.data[CONF_MIN_MAGNITUDE]:
            return False

        # Calculate distance from user's location to earthquake epicenter
        distance = self._haversine(
            self.entry.data[CONF_LATITUDE],
            self.entry.data[CONF_LONGITUDE],
            data["latitude"],
            data["longitude"],
        )

        return distance <= self.entry.data[CONF_RADIUS]

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        """Calculate the great-circle distance between two points on the Earth."""
        from math import radians, sin, cos, sqrt, atan2
        R = 6371  # Earth radius in km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)
