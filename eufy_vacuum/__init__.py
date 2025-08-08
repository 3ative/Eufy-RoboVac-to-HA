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

import asyncio
import time
import logging
from typing import Dict, Optional

from .robovac import Robovac

try:
    from .platform import *
except ImportError:
    pass

_LOGGER = logging.getLogger(__name__)


class EufyConnectionManager:
    """Manages a single shared connection per vacuum device."""
    
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
        self._update_interval = 5  # seconds between updates (faster response)
        self._command_update_delay = 2  # seconds to wait after sending a command
        
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
        """Get the shared robovac instance."""
        if self.robovac is None:
            _LOGGER.info(f"Creating robovac instance for {self.device_id}")
            self.robovac = Robovac(self.device_id, self.address, self.local_key)
        return self.robovac
    
    async def update(self, force=False) -> bool:
        """Update the vacuum state, with rate limiting."""
        async with self._update_lock:
            now = time.time()
            
            # Rate limit updates to prevent overwhelming the vacuum (unless forced)
            if not force and now - self._last_update < self._update_interval:
                _LOGGER.debug(f"Skipping update for {self.device_id} - too soon (last update {now - self._last_update:.1f}s ago)")
                return self.robovac is not None and self.robovac._connected
            
            try:
                vacuum = await self.get_robovac()
                
                # Check if connection is still valid
                if not vacuum._connected:
                    _LOGGER.info(f"Reconnecting to vacuum {self.device_id} at {self.address}")
                    await vacuum.async_connect()
                
                await vacuum.async_get()
                self._last_update = now
                _LOGGER.debug(f"Successfully updated vacuum {self.device_id}")
                return True
                
            except Exception as e:
                _LOGGER.warning(f"Connection issue with vacuum {self.device_id}: {e}")
                # Force reconnection on any error
                if self.robovac:
                    try:
                        _LOGGER.info(f"Resetting connection for {self.device_id}")
                        await self.robovac.async_disconnect()
                    except Exception as disconnect_error:
                        _LOGGER.debug(f"Error during disconnect: {disconnect_error}")
                    finally:
                        # Mark as disconnected so next update will reconnect
                        self.robovac._connected = False
                
                return False

    async def send_command_and_update(self, command_coro):
        """Send a command and then force an update after a short delay."""
        try:
            # Send the command
            await command_coro
            
            # Wait a moment for the vacuum to process the command
            await asyncio.sleep(self._command_update_delay)
            
            # Force an immediate update to get the new state
            await self.update(force=True)
            
        except Exception as e:
            _LOGGER.error(f"Error sending command to {self.device_id}: {e}")
    
    async def disconnect(self):
        """Disconnect from the vacuum."""
        if self.robovac and self.robovac._connected:
            try:
                _LOGGER.info(f"Disconnecting from {self.device_id}")
                await self.robovac.async_disconnect()
            except Exception as e:
                _LOGGER.error(f"Error disconnecting from {self.device_id}: {e}")
