# -*- coding: utf-8 -*-

# Copyright 2019 Richard Mitchell
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Eufy Vacuum integration with optimized connection management."""
import asyncio
import time
import logging
from typing import Dict, Optional

from homeassistant.helpers.discovery import async_load_platform

from .robovac import Robovac

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eufy_vacuum"


async def async_setup(hass, config):
    """Set up the Eufy Vacuum component."""
    if DOMAIN not in config:
        return True

    # Process each device
    for device_config in config[DOMAIN].get("devices", []):
        device_config["model"] = device_config.get("type", "T2118")
        device_config["device_id"] = device_config.get("id")
        
        # Load vacuum platform
        hass.async_create_task(
            async_load_platform(hass, 'vacuum', DOMAIN, device_config, config)
        )
        
        # Load sensor platform (battery)
        hass.async_create_task(
            async_load_platform(hass, 'sensor', DOMAIN, device_config, config)
        )
        
        # Load binary_sensor platform (charging)
        hass.async_create_task(
            async_load_platform(hass, 'binary_sensor', DOMAIN, device_config, config)
        )

    return True


class EufyConnectionManager:
    """
    Manages a shared connection to a Eufy vacuum to prevent connection spam.
    
    OPTIMIZED FOR REDUCED DATABASE WRITES:
    - Increased update intervals to reduce polling frequency
    - State change detection to prevent unnecessary writes
    - Configurable update intervals for different scenarios
    """
    
    _instances: Dict[str, 'EufyConnectionManager'] = {}
    _lock = asyncio.Lock()
    
    def __init__(self, device_id: str, address: str, local_key: str):
        """Initialize the connection manager."""
        self.device_id = device_id
        self.address = address
        self.local_key = local_key
        self.robovac: Optional[Robovac] = None
        self._update_lock = asyncio.Lock()
        self._last_update = 0
        
        # OPTIMIZED INTERVALS - Reduced update frequency
        self._update_interval = 30  # Default: 30s between updates (was 5s)
        self._command_update_delay = 2  # Wait after commands
        self._min_update_interval = 10  # Minimum time between any updates
        
        # State tracking to prevent unnecessary updates
        self._last_state = {}
        
    @classmethod
    async def get_instance(cls, device_id: str, address: str, local_key: str) -> 'EufyConnectionManager':
        """Get or create a connection manager instance for a device."""
        async with cls._lock:
            if device_id not in cls._instances:
                _LOGGER.info(f"Creating new connection manager for device {device_id}")
                cls._instances[device_id] = cls(device_id, address, local_key)
            else:
                _LOGGER.debug(f"Reusing existing connection manager for device {device_id}")
            return cls._instances[device_id]
    
    async def get_robovac(self) -> Robovac:
        """Get or create the robovac instance."""
        if self.robovac is None:
            _LOGGER.info(f"Creating robovac instance for {self.device_id}")
            self.robovac = Robovac(self.device_id, self.address, self.local_key)
        return self.robovac
    
    def _has_state_changed(self) -> bool:
        """Check if the vacuum state has actually changed since last update."""
        if not self.robovac:
            return False
            
        current_state = {
            'battery_level': getattr(self.robovac, 'battery_level', None),
            'work_status': getattr(self.robovac, 'work_status', None),
            'clean_speed': getattr(self.robovac, 'clean_speed', None),
            'error_code': getattr(self.robovac, 'error_code', None),
        }
        
        # First update always counts as changed
        if not self._last_state:
            self._last_state = current_state
            return True
        
        # Check if anything actually changed
        changed = current_state != self._last_state
        if changed:
            self._last_state = current_state
            _LOGGER.debug(f"State changed for {self.device_id}")
        
        return changed
    
    async def update(self, force=False, min_interval=None) -> bool:
        """
        Update the vacuum state with intelligent rate limiting.
        
        Args:
            force: If True, bypass normal rate limiting (but still respect min_interval)
            min_interval: Override the minimum interval between updates
        
        Returns:
            True if update was successful, False otherwise
        """
        async with self._update_lock:
            now = time.time()
            time_since_last = now - self._last_update
            
            # Determine which interval to use
            if min_interval is not None:
                effective_interval = min_interval
            elif force:
                effective_interval = self._min_update_interval
            else:
                effective_interval = self._update_interval
            
            # Rate limit check
            if time_since_last < effective_interval:
                _LOGGER.debug(
                    f"Skipping update for {self.device_id} - too soon "
                    f"(last: {time_since_last:.1f}s ago, min: {effective_interval}s)"
                )
                return self.robovac is not None and getattr(self.robovac, '_connected', False)
            
            try:
                vacuum = await self.get_robovac()
                
                # Check if connection is still valid
                if not getattr(vacuum, '_connected', False):
                    _LOGGER.info(f"Reconnecting to vacuum {self.device_id} at {self.address}")
                    await vacuum.async_connect()
                
                # Get current state from vacuum
                await vacuum.async_get()
                self._last_update = now
                
                # Log whether state actually changed
                if self._has_state_changed():
                    _LOGGER.debug(f"Successfully updated vacuum {self.device_id} (state changed)")
                else:
                    _LOGGER.debug(f"Updated vacuum {self.device_id} (no state change)")
                
                return True
                
            except Exception as e:
                _LOGGER.warning(f"Connection issue with vacuum {self.device_id}: {e}")
                
                # DON'T immediately reset the connection on a single failure
                # This could be a temporary network blip
                # Connection will be re-established on next successful update
                # This prevents "unavailable" flickers from brief connection issues
                _LOGGER.info(f"Keeping connection for {self.device_id}, will retry on next update")
                
                # Return False to indicate update failed, but don't destroy the connection
                # Entities will use their cached values until next successful update
                return False
    
    async def send_command_and_update(self, command_coro):
        """
        Send a command and then update after a short delay.
        
        This uses force=True to get immediate feedback, but still respects
        the minimum update interval to prevent database spam.
        """
        try:
            # Send the command
            await command_coro
            
            # Wait for vacuum to process the command
            await asyncio.sleep(self._command_update_delay)
            
            # Force an update (but still respect min_interval)
            await self.update(force=True)
            
        except Exception as e:
            _LOGGER.error(f"Error sending command to {self.device_id}: {e}")
