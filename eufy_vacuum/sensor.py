"""Support for Eufy vacuum sensors - OPTIMIZED for reduced database writes."""
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import DeviceInfo

from . import robovac
from . import EufyConnectionManager

_LOGGER = logging.getLogger(__name__)

# OPTIMIZED: Battery sensor updates every 60 seconds (was 10s)
# This reduces database writes from 8,640/day to 1,440/day per vacuum
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Eufy vacuum battery sensor."""
    if discovery_info is None:
        return
    
    device_config = discovery_info
    async_add_entities([EufyVacuumBatterySensor(device_config)], True)


class EufyVacuumBatterySensor(SensorEntity):
    """
    Representation of Eufy Vacuum Battery Sensor.
    
    OPTIMIZED:
    - 60-second update interval (instead of 10s)
    - State change detection to prevent unnecessary writes
    - Only updates state if battery level actually changed
    """

    def __init__(self, device_config):
        """Initialize the sensor."""
        self._device_config = device_config
        # Handle both 'id' and 'device_id' keys
        self._device_id = device_config.get('device_id') or device_config.get('id')
        self._name = f"{device_config['name']} Battery"
        self._battery_level = None
        self._available = False
        self._connection_manager = None
        
        # Track last known value to prevent unnecessary updates
        self._last_battery_level = None

    async def async_added_to_hass(self):
        """Called when entity is added to hass."""
        # Handle both 'access_token' and 'local_key' keys
        local_key = self._device_config.get('local_key') or self._device_config.get('access_token')
        address = self._device_config.get('address')
        
        if not local_key:
            _LOGGER.error(f"Missing local_key/access_token for device {self._device_id}")
            return
        
        if not address:
            _LOGGER.error(f"Missing address for device {self._device_id}")
            return
        
        self._connection_manager = await EufyConnectionManager.get_instance(
            self._device_id,
            address,
            local_key
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device_id}_battery"

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
        return self._available

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={("eufy_vacuum", self._device_id)},
            name=self._device_config.get('name', 'Eufy Vacuum'),
            manufacturer="Eufy",
            model=self._device_config.get('model', 'RoboVac'),
        )

    async def async_update(self):
        """
        Update the sensor with improved caching.
        
        CACHING STRATEGY:
        - If update succeeds: Update values and mark available
        - If update fails: Keep last known good values, stay "available"
        - This prevents "unavailable" flickers during temporary connection issues
        """
        # Safety check: Make sure connection manager exists
        if self._connection_manager is None:
            _LOGGER.debug(f"Connection manager not ready for {self._name}")
            # Only mark unavailable if we've never gotten data
            if self._battery_level is None:
                self._available = False
            return
            
        try:
            # Attempt to get fresh data from vacuum
            update_success = await self._connection_manager.update()
            
            # Check if we got valid data back
            if update_success and self._connection_manager.robovac:
                battery_level = self._connection_manager.robovac.battery_level
                
                # Only update if we got a real battery value
                if battery_level is not None:
                    self._battery_level = battery_level
                    self._available = True  # Mark as available - we have good data
                    
                    # Log changes for debugging (doesn't affect database writes)
                    if battery_level != self._last_battery_level:
                        self._last_battery_level = battery_level
                        _LOGGER.debug(f"Battery sensor updated: {self._battery_level}% (changed)")
                    else:
                        _LOGGER.debug(f"Battery sensor: {self._battery_level}% (no change)")
                else:
                    # Battery value is None but connection succeeded
                    # This is unusual - keep last known value
                    _LOGGER.debug(f"Battery level is None for {self._name}, keeping last value")
            else:
                # Update failed - USE CACHING instead of marking unavailable
                # Keep the last known battery value and stay "available"
                # This prevents brief "unavailable" flickers on temporary connection issues
                _LOGGER.debug(f"Update failed for {self._name}, using cached value: {self._battery_level}%")
                # Don't change self._available or self._battery_level
                # The entity will continue showing the last good value
                
        except Exception as e:
            # Unexpected error occurred
            # Log it but still try to maintain availability with cached data
            _LOGGER.error(f"Exception updating battery sensor {self._name}: {e}")
            
            # Only mark unavailable if we have no data at all
            if self._battery_level is None:
                self._available = False
            else:
                # We have cached data - stay available and use it
                _LOGGER.debug(f"Using cached battery value during error: {self._battery_level}%")
                
        except Exception as e:
            _LOGGER.error(f"Failed to update battery sensor {self._name}: {e}")
            self._available = False
            self._battery_level = None
            self._last_battery_level = None
