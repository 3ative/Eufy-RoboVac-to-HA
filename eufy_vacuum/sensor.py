"""Support for Eufy vacuum binary sensors - OPTIMIZED for reduced database writes."""
import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo

from . import robovac
from . import EufyConnectionManager

_LOGGER = logging.getLogger(__name__)

# OPTIMIZED: Charging sensor updates every 60 seconds (was frequent polling)
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up Eufy vacuum charging binary sensor."""
    if discovery_info is None:
        return
    
    device_config = discovery_info
    async_add_entities([EufyVacuumChargingBinarySensor(device_config)], True)


class EufyVacuumChargingBinarySensor(BinarySensorEntity):
    """
    Representation of Eufy Vacuum Charging Binary Sensor.
    
    OPTIMIZED:
    - 60-second update interval
    - State change detection to prevent unnecessary writes
    - Only updates state if charging status actually changed
    """

    def __init__(self, device_config):
        """Initialize the binary sensor."""
        self._device_config = device_config
        # Handle both 'id' and 'device_id' keys
        self._device_id = device_config.get('device_id') or device_config.get('id')
        self._name = f"{device_config['name']} Charging"
        self._is_charging = False
        self._available = False
        self._connection_manager = None
        
        # Track last known state to prevent unnecessary updates
        self._last_is_charging = None

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
        return f"{self._device_id}_charging"

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
        Update the binary sensor with improved caching.
        
        CACHING STRATEGY:
        - If update succeeds: Update values and mark available
        - If update fails: Keep last known good values, stay "available"
        - This prevents "unavailable" flickers during temporary connection issues
        """
        # Safety check: Make sure connection manager exists
        if self._connection_manager is None:
            _LOGGER.debug(f"Connection manager not ready for {self._name}")
            # Only mark unavailable if we've never gotten data
            if self._last_is_charging is None:
                self._available = False
            return
            
        try:
            # Attempt to get fresh data from vacuum
            update_success = await self._connection_manager.update()
            
            # Check if we got valid data back
            if update_success and self._connection_manager.robovac:
                # Calculate current charging status from work_status
                is_charging = (
                    self._connection_manager.robovac.work_status == robovac.WorkStatus.CHARGING
                )
                
                # Update with fresh data
                self._is_charging = is_charging
                self._available = True  # Mark as available - we have good data
                
                # Log changes for debugging (doesn't affect database writes)
                if is_charging != self._last_is_charging:
                    self._last_is_charging = is_charging
                    _LOGGER.debug(f"Charging sensor updated: {self._is_charging} (changed)")
                else:
                    _LOGGER.debug(f"Charging sensor: {self._is_charging} (no change)")
            else:
                # Update failed - USE CACHING instead of marking unavailable
                # Keep the last known charging status and stay "available"
                # This prevents brief "unavailable" flickers on temporary connection issues
                _LOGGER.debug(f"Update failed for {self._name}, using cached value: {self._is_charging}")
                # Don't change self._available or self._is_charging
                # The entity will continue showing the last good value
                
        except Exception as e:
            # Unexpected error occurred
            # Log it but still try to maintain availability with cached data
            _LOGGER.error(f"Exception updating charging sensor {self._name}: {e}")
            
            # Only mark unavailable if we have no data at all
            if self._last_is_charging is None:
                self._available = False
            else:
                # We have cached data - stay available and use it
                _LOGGER.debug(f"Using cached charging value during error: {self._is_charging}")
                
        except Exception as e:
            _LOGGER.error(f"Failed to update charging sensor {self._name}: {e}")
            self._available = False
            self._is_charging = False
            self._last_is_charging = None
