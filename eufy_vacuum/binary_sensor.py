"""Support for Eufy vacuum binary sensors."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo

from . import robovac
from . import EufyConnectionManager

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Eufy vacuum binary sensors."""
    if discovery_info is None:
        return
    
    # Add charging binary sensor
    add_entities([EufyVacuumChargingBinarySensor(discovery_info)], True)


class EufyVacuumChargingBinarySensor(BinarySensorEntity):
    """Charging binary sensor for Eufy vacuum."""

    def __init__(self, device_config):
        """Initialize the charging sensor."""
        self._device_config = device_config
        self._device_id = device_config['device_id']
        self._name = f"{device_config['name']} Charging"
        self._available = False
        self._is_charging = None
        self._connection_manager = None

    async def async_added_to_hass(self):
        """Called when entity is added to hass."""
        self._connection_manager = await EufyConnectionManager.get_instance(
            self._device_config['device_id'],
            self._device_config['address'], 
            self._device_config['local_key']
        )

    async def async_update(self):
        """Update the binary sensor."""
        if self._connection_manager is None:
            return
            
        try:
            self._available = await self._connection_manager.update()
            if self._available and self._connection_manager.robovac:
                self._is_charging = self._connection_manager.robovac.work_status == robovac.WorkStatus.CHARGING
                _LOGGER.debug(f"Charging sensor updated: {self._is_charging}")
            else:
                self._is_charging = None
        except Exception as e:
            _LOGGER.error(f"Failed to update charging sensor {self._name}: {e}")
            self._available = False
            self._is_charging = None

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device_id}_charging"

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return true if the vacuum is charging."""
        return self._is_charging

    @property
    def device_class(self):
        """Return the device class."""
        return BinarySensorDeviceClass.BATTERY_CHARGING

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available and self._is_charging is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={("eufy_vacuum", self._device_id)},
            name=self._device_config.get('name', 'Eufy Vacuum'),
            manufacturer="Eufy",
            model=self._device_config.get('model', 'RoboVac'),
        )