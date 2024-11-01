
import logging
from typing import Any
from homeassistant import data_entry_flow

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant

import voluptuous as vol
from aiohttp_requests import requests

DOMAIN = "ostrom"

DATA_SCHEMA = vol.Schema({("apikey"): str})

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
         """get a outh token"""    
         url = "https://auth.production.ostrom-api.io/oauth2/token"
         payload = { "grant_type": "client_credentials" }
         headers = {
           "accept": "application/json",
           "content-type": "application/x-www-form-urlencoded",
           "authorization": "Basic " + data['apikey']
         }
         response = await requests.post(url, data=payload, headers=headers)
         ok = (response.status_code  == requests.codes.created)
         return ok
    
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#class ExampleConfigFlow(data_entry_flow.FlowHandler):

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    # (this is not implemented yet)
    VERSION = 4

    async def async_step_user(self, user_input=None):
        """Handle user step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="myostrom", data=user_input)
        
        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        ) 

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
        
