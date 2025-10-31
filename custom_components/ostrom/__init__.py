"""
Ostrom Configuration mit vertragsauswahl
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
import logging

from .coordinator import OstromCoordinator  # <-- Coordinator import
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)
 

PLATFORMS = [Platform.SENSOR]

CONF_TOPIC = 'ostrom_login setup'

_LOGGER = logging.getLogger(__name__)

#async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
#    """Set up Ostrom from yaml (old version 3.0.0). wird nicht mehr ausgewertet !"""
#    if DOMAIN in config:
#        hass.data[DOMAIN] = await hass.async_add_executor_job(
#            ostrom_ha_setup, config[DOMAIN]["apiuser"], config[DOMAIN]["apipass"]
#        )
#    return True
    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = OstromCoordinator(hass, entry)
    await coordinator.async_setup_hourly_update()
    await coordinator.async_config_entry_first_refresh()
    # Coordinator im Data-Dictionary speichern!
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = coordinator
    # Forward to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    return True
    
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN, None)
    return unload_ok    
    
async def async_migrate_entry(hass, entry):
    """Migrate old entry (ConfigEntry) to new version."""
    # Beispiel: Version 1 → 2
    old_version = entry.version
    _LOGGER.info("Migrating from version %s", old_version)

    # Deine Migrationslogik hier (meist: Datenstruktur anpassen)
    # Beispiel: Wenn du neue Felder brauchst, setze sie auf Defaults
    if old_version < 5:
        new_data = {**entry.data}
        # z.B. neues Feld einfügen:
        # new_data["new_field"] = "default_value"
        entry.version = 5
        hass.config_entries.async_update_entry(entry, data=new_data)

    _LOGGER.info("Migration to version %s successful", entry.version)
    return True
    
    


