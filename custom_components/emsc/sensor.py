"""Sensor platform for Earthquake Monitoring integration."""
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    EVENT_EARTHQUAKE_DETECTED,
    ATTR_MAGNITUDE,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    ATTR_LOCALITY,
    ATTR_TIME,
)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Earthquake Monitoring sensors."""
    sensors = [
        EarthquakeMagnitudeSensor(entry),
        EarthquakeLatitudeSensor(entry),
        EarthquakeLongitudeSensor(entry),
        EarthquakeLocalitySensor(entry),
    ]
    async_add_entities(sensors, True)

class EarthquakeSensorBase(SensorEntity):
    """Base class for Earthquake Monitoring sensors."""

    def __init__(self, entry):
        """Initialize the sensor."""
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Earthquake Monitor",
            manufacturer="EMSC",
        )

    @callback
    def async_update_state(self, data):
        """Update the sensor state."""
        self.async_write_ha_state()

class EarthquakeMagnitudeSensor(EarthquakeSensorBase):
    """Sensor for earthquake magnitude."""

    def __init__(self, entry):
        """Initialize the magnitude sensor."""
        super().__init__(entry)
        self._attr_name = "Earthquake Magnitude"
        self._attr_native_unit_of_measurement = "M"  # Magnitude unit
        #self._attr_device_class = SensorDeviceClass.MAGNITUDE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"{entry.entry_id}_magnitude"

    @callback
    def async_update_state(self, data):
        """Update the magnitude sensor state."""
        self._attr_native_value = data[ATTR_MAGNITUDE]
        super().async_update_state(data)

class EarthquakeLatitudeSensor(EarthquakeSensorBase):
    """Sensor for earthquake latitude."""

    def __init__(self, entry):
        """Initialize the latitude sensor."""
        super().__init__(entry)
        self._attr_name = "Earthquake Latitude"
        self._attr_native_unit_of_measurement = "°"  # Degree symbol for latitude
        self._attr_device_class = SensorDeviceClass.LATITUDE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"{entry.entry_id}_latitude"

    @callback
    def async_update_state(self, data):
        """Update the latitude sensor state."""
        self._attr_native_value = data[ATTR_LATITUDE]
        super().async_update_state(data)

class EarthquakeLongitudeSensor(EarthquakeSensorBase):
    """Sensor for earthquake longitude."""

    def __init__(self, entry):
        """Initialize the longitude sensor."""
        super().__init__(entry)
        self._attr_name = "Earthquake Longitude"
        self._attr_native_unit_of_measurement = "°"  # Degree symbol for longitude
        self._attr_device_class = SensorDeviceClass.LONGITUDE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"{entry.entry_id}_longitude"

    @callback
    def async_update_state(self, data):
        """Update the longitude sensor state."""
        self._attr_native_value = data[ATTR_LONGITUDE]
        super().async_update_state(data)

class EarthquakeLocalitySensor(EarthquakeSensorBase):
    """Sensor for earthquake locality."""

    def __init__(self, entry):
        """Initialize the locality sensor."""
        super().__init__(entry)
        self._attr_name = "Earthquake Locality"
        self._attr_unique_id = f"{entry.entry_id}_locality"

    @callback
    def async_update_state(self, data):
        """Update the locality sensor state."""
        self._attr_native_value = data[ATTR_LOCALITY]
        super().async_update_state(data)
