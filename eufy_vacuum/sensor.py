"""Support for Eufy vacuum sensors."""
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import DeviceInfo

from . import robovac
from . import EufyConnectionManager

_LOGGER = logging.getLogger(__name__)

# Battery sensor updates every 10 seconds
SCAN_INTERVAL = timedelta(seconds=10)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Eufy vacuum sensors."""
    if discovery_info is None:
        return
    
    # Add battery sensor only
    add_entities([EufyVacuumBatterySensor(discovery_info)], True)


class EufyVacuumBatterySensor(SensorEntity):
    """Battery sensor for Eufy vacuum."""

    def __init__(self, device_config):
        """Initialize the battery sensor."""
        self._device_config = device_config
        self._device_id = device_config['device_id']
        self._name = f"{device_config['name']} Battery"
        self._available = False
        self._battery_level = None
        self._connection_manager = None

    async def async_added_to_hass(self):
        """Called when entity is added to hass."""
        self._connection_manager = await EufyConnectionManager.get_instance(
            self._device_config['device_id'],
            self._device_config['address'], 
            self._device_config['local_key']
        )

    async def async_update(self):
        """Update the sensor."""
        if self._connection_manager is None:
            return
            
        try:
            # Force update since we want 10-second intervals for battery
            self._available = await self._connection_manager.update(force=True)
            if self._available and self._connection_manager.robovac:
                self._battery_level = self._connection_manager.robovac.battery_level
                _LOGGER.debug(f"Battery sensor updated: {self._battery_level}%")
            else:
                self._battery_level = None
        except Exception as e:
            _LOGGER.error(f"Failed to update battery sensor {self._name}: {e}")
            self._available = False
            self._battery_level = None

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device_id}_battery"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._battery_level

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return PERCENTAGE

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.BATTERY

    @property
    def state_class(self):
        """Return the state class."""
        return SensorStateClass.MEASUREMENT

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available and self._battery_level is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={("eufy_vacuum", self._device_id)},
            name=self._device_config.get('name', 'Eufy Vacuum'),
            manufacturer="Eufy",
            model=self._device_config.get('model', 'RoboVac'),
        )