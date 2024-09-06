"""
Configuration:

To use the hello_world component you will need to add the following to your
configuration.yaml file.

ostrom:
  ostrom_login64key : "your base64 ostrom login key"
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
#from homeassistant.util.json import JsonObjectType as json
import datetime
import logging
import requests
import json

DOMAIN = "ostrom"

CONF_TOPIC = 'ostrom_login64key'

_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    now = datetime.datetime.now()
    expire_attr = {'expire':now}
    hass.states.set("ostrom.token", "no token",expire_attr)
        
    def handle_token(call):
        """Handle the service action call."""
        usrpwd64 = call.data.get('api_key64')
        future = datetime.datetime.now() + datetime.timedelta(seconds = 3500)
        expire_attr = {'expire':future}
        url = "https://auth.production.ostrom-api.io/oauth2/token"
        payload = { "grant_type": "client_credentials" }
        headers = {
          "accept": "application/json",
          "content-type": "application/x-www-form-urlencoded",
          "authorization": "Basic " + usrpwd64 
        }
        response = requests.post(url, data=payload, headers=headers)
        auth = json.loads(response.text)
        token = auth['token_type']+" "+auth['access_token']
        hass.states.set("ostrom.token", token, expire_attr)
        _LOGGER.info("daten bekommen " + token)
        
    def handle_price(call):
        """Handle the service action call."""
        #token = hass.states.get("ostrom.token")
        token = call.data.get('token')
        tax="grossKwhTaxAndLevies"
        kwprice="grossKwhPrice"
        myzip = "35789"
        timeformat="%Y-%m-%dT%H:00:00.000Z"
        now = datetime.datetime.utcnow().strftime(timeformat)
        future = (datetime.datetime.utcnow() + datetime.timedelta(hours=24)).strftime(timeformat)
        url = "https://production.ostrom-api.io/spot-prices?startDate="+now+"&endDate=" + future + "&resolution=HOUR&zip="+ myzip
        headers = {
          "accept": "application/json",
          "authorization": token
        }
        response = requests.get(url, headers=headers)
        erg = json.loads(response.text)
        exlist=[]
        for ix in erg['data']:
            exlist.append(round(float(ix[tax])+float(ix[kwprice]),2))
        hass.states.set("ostrom.price", exlist)
        
        
    hass.services.register(DOMAIN, "get_token", handle_token)
    hass.services.register(DOMAIN, "get_price", handle_price)
        

    # Return boolean to indicate that initialization was successful.
    return True
