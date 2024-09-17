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
        future = str(datetime.datetime.now() + datetime.timedelta(seconds = 3500))
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
        jsontoken = {'token':token}
        hass.states.set("ostrom.token", future , jsontoken )
        _LOGGER.info('Get token')
        
    def handle_price(call):
        """Handle the service action call."""
        #token = hass.states.get("ostrom.token")
        token = call.data.get('token')
        myzip = call.data.get('my_zip')
        _LOGGER.warning(call.data.get('start_offset'))
        tax="grossKwhTaxAndLevies"
        kwprice="grossKwhPrice"
        # myzip = "35789"
        #offstart = int(call.data.get('start_offset'))
        offstart = 0
        #offend = int(call.data.get('end_offset'))
        offend= 36
        timeformat="%Y-%m-%dT%H:00:00.000Z"
        now = (datetime.datetime.utcnow() + datetime.timedelta(hours=offstart)).strftime(timeformat) 
        future = (datetime.datetime.utcnow() + datetime.timedelta(hours=offend)).strftime(timeformat)
        url = "https://production.ostrom-api.io/spot-prices?startDate="+now+"&endDate=" + future + "&resolution=HOUR&zip="+ myzip
        headers = {
          "accept": "application/json",
          "authorization": token
        }
        response = requests.get(url, headers=headers)
        erg = json.loads(response.text)
        exlist=[]
        japex=[]
        for ix in erg['data']:
            exlist.append(round(float(ix[tax])+float(ix[kwprice]),2))
            jd = { 'date':ix['date'] }
            jr = round(float(ix[tax])+float(ix[kwprice]),2)
            jd["price"] = str(jr)
            japex.append(jd)
        jerglist = json.dumps(exlist) 
        avg = round((sum(exlist)/len(exlist)),2)
        pricelow =  japex[exlist.index(min(exlist))]['date']   
        nowprice = exlist[0]
        raw_data = {'raw':erg["data"],'average':avg,'apex':japex,'low':pricelow}
        #hass.states.set("ostrom.price", jerglist,raw_data)
        hass.states.set("ostrom.price", nowprice,raw_data)
        
    def handle_custom(call):
        """Handle the service action call."""
        token = call.data.get('token')
        url = "https://production.ostrom-api.io/contracts"
        headers = {
          "accept": "application/json",
          "authorization": token
        }
        response = requests.get(url, headers=headers)
        hass.states.set("ostrom_contract_data",erg)
        
    def handle_delay(call):
        """Handle the service action call."""
 
        
    hass.services.register(DOMAIN, "get_token", handle_token)
    hass.services.register(DOMAIN, "get_price", handle_price)
    hass.services.register(DOMAIN, "get_customer", handle_custom)
        

    # Return boolean to indicate that initialization was successful.
    return True
  
