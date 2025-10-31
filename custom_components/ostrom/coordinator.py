"""DataUpdateCoordinator for Ostrom integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .ostrom_api import OstromApi, APIRequestError

_LOGGER = logging.getLogger(__name__)

# Maximum number of consecutive errors before failing completely
MAX_ERROR_COUNT = 3


class OstromCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Ostrom data."""

    def __init__(self, hass: HomeAssistant, api: OstromApi) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ostrom",
            update_interval=timedelta(minutes=60),
        )
        self.api = api
        self._error_count = 0
        self._simulate_error = False
        self._drop_raw_data = False
        self.last_update_error: str | None = None

    def _should_preserve_data(self) -> bool:
        """Check if we should preserve old data instead of failing completely."""
        return self.data is not None and self._error_count < MAX_ERROR_COUNT

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Ostrom API."""
        # Handle simulate_error for testing
        if self._simulate_error:
            _LOGGER.warning("Simulated error active - forcing API failure")
            if self._drop_raw_data:
                # Drop existing data and raise error
                self.last_update_error = "Simulated error (data dropped)"
                raise UpdateFailed("Simulated error (data dropped)")
            else:
                # Keep existing data but mark as error
                self.last_update_error = "Simulated error (data preserved)"
                raise UpdateFailed("Simulated error (data preserved)")

        try:
            # Fetch price data from API
            data = await self.api.get_forecast_prices()
            
            # Reset error tracking on success
            self._error_count = 0
            self.last_update_error = None
            
            return data

        except APIRequestError as err:
            # Track consecutive errors
            self._error_count += 1
            self.last_update_error = err.as_sensor_text()
            
            _LOGGER.error(
                "Error fetching Ostrom data (attempt %d): %s",
                self._error_count,
                err.as_log_text()
            )
            
            # Check if authentication error - these should not be retried
            if err.source == "auth":
                raise ConfigEntryAuthFailed(f"Authentication failed: {err.as_sensor_text()}") from err
            
            # For other errors, decide whether to keep old data or fail completely
            if self._should_preserve_data():
                # Keep existing data for a few failures
                _LOGGER.warning(
                    "Keeping previous data after error (attempt %d/%d)",
                    self._error_count, MAX_ERROR_COUNT
                )
                return self.data
            else:
                # Too many failures or no previous data - propagate error
                raise UpdateFailed(f"Failed to fetch Ostrom data: {err.as_sensor_text()}") from err

        except Exception as err:
            # Unexpected errors
            self._error_count += 1
            self.last_update_error = f"Unexpected error: {str(err)}"
            
            _LOGGER.exception("Unexpected error fetching Ostrom data: %s", err)
            
            if self._should_preserve_data():
                _LOGGER.warning(
                    "Keeping previous data after unexpected error (attempt %d/%d)",
                    self._error_count, MAX_ERROR_COUNT
                )
                return self.data
            else:
                raise UpdateFailed(f"Unexpected error: {str(err)}") from err

    async def async_apitest_error(self, simulate: bool, drop_raw: bool = False) -> None:
        """Enable/disable simulated API errors for testing.
        
        Args:
            simulate: If True, simulate API errors on next update
            drop_raw: If True and simulate=True, drop existing data; if False, preserve it
        """
        self._simulate_error = simulate
        self._drop_raw_data = drop_raw
        
        if simulate:
            _LOGGER.warning(
                "API error simulation enabled (drop_raw=%s)", drop_raw
            )
        else:
            _LOGGER.info("API error simulation disabled")
            self.last_update_error = None
            self._error_count = 0
