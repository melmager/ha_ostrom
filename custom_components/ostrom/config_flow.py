""" ConfigFlow for Ostrom """

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant, callback


#from functools import partial
#from aiohttp_requests import requests
#import requests
#from .ostrom_api import Ostrom
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("apiuser"): str,
        vol.Required("apipass"): str
    })

    
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 5

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle inital step."""
        errors = {}
        if user_input is not None:
           self.data = user_input
           # Create a unique ID:
           _unique_id = self.data['apiuser'][:8]
           #test = Ostrom(data["apiuser"], data["apipass"])  
           #result = True
           #errors["base"] = "cannot_connect"
           _LOGGER.warning("user "+user_input["apiuser"])
           #return result
           #result = await hass.async_add_executor_job(test.test_setup())
           #result = await validate_input(self.hass, user_input)    
           #result = await hass.async_add_executor_job(valiate_input, user_input['apikey'])
           #if result:
           return self.async_create_entry(title="myostrom", data=user_input)
           #else:
      
       
       
        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        ) 

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
        
        
