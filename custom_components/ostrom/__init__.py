"""
Configuration:
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
import logging

from .ostrom_api import OstromApi
from .coordinator import OstromCoordinator

DOMAIN = "ostrom"
PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Ostrom component from YAML configuration."""
    # YAML configuration is deprecated, but keep for backward compatibility
    if DOMAIN not in config:
        return True
    
    _LOGGER.warning(
        "Configuration via YAML is deprecated. "
        "Please use the UI to configure Ostrom integration."
    )
    
    # Legacy setup - create API and coordinator
    api = OstromApi(
        config[DOMAIN]["apiuser"],
        config[DOMAIN]["apipass"]
    )
    
    coordinator = OstromCoordinator(hass, api)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinator"] = coordinator
    
    # Perform initial refresh
    await coordinator.async_config_entry_first_refresh()
    
    return True

    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ostrom from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create API instance
    api = OstromApi(
        entry.data["apiuser"],
        entry.data["apipass"]
    )
    
    # Get ZIP and contract ID if available
    if "zip" in entry.data and "contract_id" in entry.data:
        api.set_zip_cid(entry.data["zip"], entry.data["contract_id"])
    
    # Create coordinator
    coordinator = OstromCoordinator(hass, api)
    
    # Store coordinator in hass.data
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Perform initial refresh
    await coordinator.async_config_entry_first_refresh()
    
    # Register services
    async def handle_simulate_error(call: ServiceCall) -> None:
        """Handle the simulate_error service call."""
        simulate = call.data.get("simulate_error", False)
        drop_raw = call.data.get("clear_last_data", False)
        
        # Find the coordinator (use the first one if multiple entries exist)
        for entry_id, coord in hass.data[DOMAIN].items():
            if isinstance(coord, OstromCoordinator):
                await coord.async_apitest_error(simulate, drop_raw)
                _LOGGER.info(
                    "Simulate error service called: simulate=%s, drop_raw=%s",
                    simulate, drop_raw
                )
                break
    
    # Register service only once (check if not already registered)
    if not hass.services.has_service(DOMAIN, "ostrom_apitest_error"):
        hass.services.async_register(
            DOMAIN,
            "ostrom_apitest_error",
            handle_simulate_error
        )
    
    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True



async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok    
    
