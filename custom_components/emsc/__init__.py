"""The Earthquake Monitoring integration for seismicportal.eu."""
import asyncio
import logging
import voluptuous as vol
import ssl
import aiohttp
import json
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS

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
    _LOGGER.info("Setting up Earthquake Monitoring integration")
    hass.data.setdefault(DOMAIN, {})

    # Initialize WebSocket client and data handler
    ws_client = EarthquakeWebSocketClient(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = ws_client

    # Start WebSocket connection
    await ws_client.async_connect()

    # Ensure the WebSocket connection is established
    if ws_client.websocket is None:
        _LOGGER.error("Failed to establish WebSocket connection")
        return False

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Platforms set up")

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Earthquake Monitoring integration")
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
        self.session = None
        self.websocket = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5

    async def async_connect(self):
        """Connect to the WebSocket server."""
        await self._async_connect_websocket()

    async def _async_connect_websocket(self):
        """Establish WebSocket connection."""
        try:
            _LOGGER.info("Attempting to connect to %s", WS_URI)
            ssl_context = ssl.create_default_context()
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
            self.websocket = await self.session.ws_connect(WS_URI, ssl=ssl_context)
            _LOGGER.info("Connected to seismicportal.eu WebSocket")
            self._reconnect_attempts = 0
            self.hass.async_create_task(self._async_handle_messages())
        except Exception as e:
            _LOGGER.error("Error connecting to WebSocket: %s", e, exc_info=True)
            await self._async_schedule_reconnect()

    async def _async_handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message.data)
                    if self._filter_earthquake(data):
                        await self._async_dispatch_event(data)
                except json.JSONDecodeError as e:
                    _LOGGER.error("Error decoding WebSocket message: %s", e)
                except Exception as e:
                    _LOGGER.error("Unexpected error processing WebSocket message: %s", e, exc_info=True)
        except aiohttp.ClientError as e:
            _LOGGER.error("WebSocket connection error: %s", e)
        except asyncio.CancelledError:
            _LOGGER.info("WebSocket message handling cancelled")
        except Exception as e:
            _LOGGER.error("Unexpected error handling WebSocket message: %s", e, exc_info=True)
        finally:
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
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    async def _async_dispatch_event(self, data: dict):
        """Dispatch earthquake event to Home Assistant."""
        self.hass.bus.async_fire(
            EVENT_EARTHQUAKE_DETECTED,
            {
                ATTR_MAGNITUDE: data["mag"],
                ATTR_LATITUDE: data["latitude"],
                ATTR_LONGITUDE: data["longitude"],
                ATTR_LOCALITY: data.get("flynn_region", "Unknown"),
                ATTR_TIME: data["time"],
            },
        )

    async def _async_schedule_reconnect(self):
        """Schedule a reconnection attempt."""
        if self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            _LOGGER.warning(
                "Attempting to reconnect (%d/%d)...",
                self._reconnect_attempts,
                self._max_reconnect_attempts,
            )
            await asyncio.sleep(5)
            await self._async_connect_websocket()
        else:
            _LOGGER.error("Max reconnection attempts reached")

    async def async_disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        if self.session:
            await self.session.close()
            self.session = None
        _LOGGER.info("Disconnected from seismicportal.eu WebSocket")
