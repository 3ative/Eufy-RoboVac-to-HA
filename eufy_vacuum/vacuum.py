"""Support for Eufy vacuum cleaners."""
import logging

from homeassistant.components.vacuum import (
    StateVacuumEntity, VacuumEntityFeature, VacuumActivity
)
from homeassistant.helpers.entity import DeviceInfo

from . import robovac
from . import EufyConnectionManager

_LOGGER = logging.getLogger(__name__)


FAN_SPEED_OFF = 'Off'
FAN_SPEED_STANDARD = 'Standard'
FAN_SPEED_BOOST_IQ = 'Boost IQ'
FAN_SPEED_MAX = 'Max'
FAN_SPEEDS = {
    robovac.CleanSpeed.NO_SUCTION: FAN_SPEED_OFF,
    robovac.CleanSpeed.STANDARD: FAN_SPEED_STANDARD,
    robovac.CleanSpeed.BOOST_IQ: FAN_SPEED_BOOST_IQ,
    robovac.CleanSpeed.MAX: FAN_SPEED_MAX,
}


SUPPORT_ROBOVAC_T2118 = (
    VacuumEntityFeature.CLEAN_SPOT | 
    VacuumEntityFeature.FAN_SPEED | VacuumEntityFeature.LOCATE |
    VacuumEntityFeature.PAUSE | VacuumEntityFeature.RETURN_HOME | 
    VacuumEntityFeature.START | VacuumEntityFeature.STATUS |
    VacuumEntityFeature.TURN_OFF | VacuumEntityFeature.TURN_ON
)


MODEL_CONFIG = {
    'T2118': {
        'fan_speeds': FAN_SPEEDS,
        'support': SUPPORT_ROBOVAC_T2118
    }
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Eufy vacuum cleaners."""
    if discovery_info is None:
        return
    add_entities([EufyVacuum(discovery_info)], True)


class EufyVacuum(StateVacuumEntity):
    """Representation of a Eufy vacuum cleaner."""

    def __init__(self, device_config):
        """Initialize the vacuum."""

        try:
            self._config = MODEL_CONFIG[device_config['model'].upper()]
        except KeyError:
            raise RuntimeError("Unsupported model {}".format(
                device_config['model']))

        self._fan_speed_reverse_mapping = {
            v: k for k, v in self._config['fan_speeds'].items()}
        self._device_id = device_config['device_id']
        self._device_config = device_config
        self._name = device_config['name']
        self._available = False
        self._connection_manager = None

    async def async_added_to_hass(self):
        """Called when entity is added to hass."""
        self._connection_manager = await EufyConnectionManager.get_instance(
            self._device_config['device_id'],
            self._device_config['address'], 
            self._device_config['local_key']
        )

    async def async_update(self):
        """Synchronise state from the vacuum."""
        if self._connection_manager is None:
            return
            
        try:
            self._available = await self._connection_manager.update()
            if self._available:
                _LOGGER.debug(f"Successfully updated vacuum {self._name}")
        except Exception as e:
            _LOGGER.error(f"Failed to update vacuum {self._name}: {e}")
            self._available = False

    @property
    def robovac(self):
        """Get the robovac instance."""
        if self._connection_manager and self._connection_manager.robovac:
            return self._connection_manager.robovac
        return None

    @property
    def unique_id(self):
        """Return the ID of this vacuum."""
        return self._device_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def is_on(self):
        """Return true if device is on."""
        if not self.robovac:
            return False
        return self.robovac.work_status == robovac.WorkStatus.RUNNING

    @property
    def supported_features(self):
        """Flag vacuum cleaner robot features that are supported."""
        return self._config['support']

    @property
    def fan_speed(self):
        """Return the fan speed of the vacuum cleaner."""
        if not self.robovac:
            return FAN_SPEED_OFF
        return self._config['fan_speeds'].get(
            self.robovac.clean_speed, FAN_SPEED_OFF)

    @property
    def fan_speed_list(self):
        """Get the list of available fan speed steps of the vacuum cleaner."""
        return list(self._config['fan_speeds'].values())

    @property
    def activity(self) -> VacuumActivity | None:
        """Return the current activity of the vacuum cleaner."""
        if not self.robovac:
            return VacuumActivity.IDLE
            
        if self.robovac.error_code != robovac.ErrorCode.NO_ERROR:
            return VacuumActivity.ERROR
        elif self.robovac.go_home:
            return VacuumActivity.RETURNING
        elif self.robovac.work_status == robovac.WorkStatus.RUNNING:
            return VacuumActivity.CLEANING
        elif self.robovac.work_status == robovac.WorkStatus.CHARGING:
            return VacuumActivity.DOCKED
        elif self.robovac.work_status == robovac.WorkStatus.RECHARGE_NEEDED:
            return VacuumActivity.RETURNING
        elif self.robovac.work_status == robovac.WorkStatus.SLEEPING:
            return VacuumActivity.IDLE
        elif self.robovac.work_status == robovac.WorkStatus.STAND_BY:
            return VacuumActivity.PAUSED
        elif self.robovac.work_status == robovac.WorkStatus.COMPLETED:
            return VacuumActivity.DOCKED
        
        return VacuumActivity.IDLE

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attributes = {}
        
        # Add battery level and charging status for compatibility with vacuum cards
        if self._connection_manager and self._connection_manager.robovac:
            try:
                # Get battery from the shared connection
                battery_level = self._connection_manager.robovac.battery_level
                if battery_level is not None:
                    attributes['battery_level'] = battery_level
                    attributes['battery_icon'] = self._get_battery_icon(battery_level)
                
                # Get charging status from the shared connection
                is_charging = self._connection_manager.robovac.work_status == robovac.WorkStatus.CHARGING
                attributes['charging'] = is_charging
                attributes['charging_status'] = "Charging" if is_charging else "Not Charging"
                
            except:
                pass
                
        return attributes
    
    def _get_battery_icon(self, battery_level):
        """Return a battery icon based on the battery level."""
        if battery_level is None:
            return 'mdi:battery-unknown'
        elif battery_level <= 5:
            return 'mdi:battery-outline'
        elif battery_level <= 15:
            return 'mdi:battery-10'
        elif battery_level <= 25:
            return 'mdi:battery-20'
        elif battery_level <= 35:
            return 'mdi:battery-30'
        elif battery_level <= 45:
            return 'mdi:battery-40'
        elif battery_level <= 55:
            return 'mdi:battery-50'
        elif battery_level <= 65:
            return 'mdi:battery-60'
        elif battery_level <= 75:
            return 'mdi:battery-70'
        elif battery_level <= 85:
            return 'mdi:battery-80'
        elif battery_level <= 95:
            return 'mdi:battery-90'
        else:
            return 'mdi:battery'

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={("eufy_vacuum", self._device_id)},
            name=self._device_config.get('name', 'Eufy Vacuum'),
            manufacturer="Eufy",
            model=self._device_config.get('model', 'RoboVac'),
        )

    async def async_return_to_base(self, **kwargs):
        """Set the vacuum cleaner to return to the dock."""
        if self._connection_manager and self._connection_manager.robovac:
            await self._connection_manager.robovac.async_go_home()

    async def async_clean_spot(self, **kwargs):
        """Perform a spot clean-up."""
        if self._connection_manager and self._connection_manager.robovac:
            await self._connection_manager.robovac.async_set_work_mode(robovac.WorkMode.SPOT)

    async def async_locate(self, **kwargs):
        """Locate the vacuum cleaner."""
        if self._connection_manager and self._connection_manager.robovac:
            await self._connection_manager.robovac.async_find_robot()

    async def async_set_fan_speed(self, fan_speed, **kwargs):
        """Set fan speed."""
        if self._connection_manager and self._connection_manager.robovac:
            clean_speed = self._fan_speed_reverse_mapping[fan_speed]
            await self._connection_manager.send_command_and_update(
                self._connection_manager.robovac.async_set_clean_speed(clean_speed)
            )

    async def async_turn_on(self, **kwargs):
        """Turn the vacuum on."""
        if self._connection_manager and self._connection_manager.robovac:
            await self._connection_manager.send_command_and_update(
                self._connection_manager.robovac.async_set_work_mode(robovac.WorkMode.AUTO)
            )

    async def async_turn_off(self, **kwargs):
        """Turn the vacuum off and return to home."""
        await self.async_return_to_base()

    async def async_start(self, **kwargs):
        """Resume the cleaning cycle."""
        await self.async_turn_on()

    async def async_resume(self, **kwargs):
        """Resume the cleaning cycle."""
        if self._connection_manager and self._connection_manager.robovac:
            await self._connection_manager.send_command_and_update(
                self._connection_manager.robovac.async_play()
            )

    async def async_pause(self, **kwargs):
        """Pause the cleaning cycle."""
        if self._connection_manager and self._connection_manager.robovac:
            await self._connection_manager.send_command_and_update(
                self._connection_manager.robovac.async_pause()
            )

    async def async_start_pause(self, **kwargs):
        """Pause the cleaning task or resume it."""
        if self._connection_manager and self._connection_manager.robovac:
            if self._connection_manager.robovac.play_pause:
                await self.async_pause()
            else:
                await self.async_resume()
