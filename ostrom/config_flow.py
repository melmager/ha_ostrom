# get strill error - cant find the problem :-(
from __future__ import annotations

import logging
from typing import Any
from homeassistant import data_entry_flow

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant

import voluptuous as vol
#from functools import partial
#from aiohttp_requests import requests
#import requests
#from .ostrom_api import Ostrom
#from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ostrom"

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("apiuser"): str,
        vol.Required("apipass"): str
        
    })

    
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#class ExampleConfigFlow(data_entry_flow.FlowHandler):

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    # (this is not implemented yet)
    VERSION = 5

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle user step."""
        errors = {}
        if user_input is not None:
           self.data = user_input
           #test = Ostrom(data["apiuser"], data["apipass"])  
           result = True
           return self.async_create_entry(title=info["ostrom"], data=user_input)
           #result = await hass.async_add_executor_job(test.test_setup())
           #result = await validate_input(self.hass, user_input)    
           #result = await hass.async_add_executor_job(valiate_input, user_input['apikey'])
           #if result:
              #return self.async_create_entry(title=info["myostrom"], data=user_input)
           #else:
              #errors["base"] = "cannot_connect"
       
       
        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        ) 
    
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)
        
        
class OptionsFlowHandler(config_entries.OptionsFlow):
    """EnergyScore options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.current_config: dict = dict(config_entry.data)
        self.current_options = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

#schema = Schema({Optional('key', default='value'): str})
        options_schema = vol.Schema(
            {
                vol.Optional("Sensor_PriceNow"): str,
                vol.Optional("Counter_price"): str,
                vol.Optional("Counter_kWh"):str
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
        

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
        
        
