"""
Configuration:
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
#from homeassistant.util.json import JsonObjectType as json
import asyncio
import datetime
import logging
import requests
import json
import base64
import math
from .ostrom_api import *

DOMAIN = "ostrom"

CONF_TOPIC = 'ostrom_login setup'

_LOGGER = logging.getLogger(__name__)

#myapi = ostrom_api.Ostrom_api()

#def setup(hass, config):
async def async_setup(hass, config):
    
    hass.data[DOMAIN] = await hass.async_add_executor_job(ostrom_ha_setup ,config[DOMAIN]["apiuser"],config[DOMAIN]["apipass"])
    #hass.states.async_set("ostrom.token","test",hass.data[DOMAIN])
    
    async def handle_price_forecast(call):
        erg={"average": 28.2, "low": {"date": "2025-01-23T22:00:00.000Z", "price": 22.79}, "data": [{"date": "2025-01-23T06:00:00.000Z", "price": 32.12}, {"date": "2025-01-23T07:00:00.000Z", "price": 34.79} ]}
        now = datetime.datetime.utcnow()
        #erg = ostrom_ha_price(hass.data[DOMAIN])
        #erg = await hass.async_add_executor_job(ostrom_price,hass.data[DOMAIN]["outh"]["token"],hass.data[DOMAIN]["contract"]["zip"],now)
        #erg = ostrom_price(hass.data[DOMAIN]["outh"]["token"],hass.data["contract"]["zip"],now)
        erg = await hass.async_add_executor_job(ostrom_ha_price,hass.data[DOMAIN])
        hass.states.async_set("ostrom.price", erg["data"][0]["price"],erg)
       
        
    async def handle_pwr_relation(call):
        tage = 2
        if (call.data.get('days_back') != None): 
            tage = int(call.data.get('days_back'))
        #hass.states.async_set("ostrom.token","test",call.data)
        #erg = {'data': [{'date': '2025-01-31T00:00:00.000Z', 'kWh': 0.531}, {'date': '2025-01-31T01:00:00.000Z', 'kWh': 0.556}]}
        erg = await hass.async_add_executor_job(ostrom_ha_power,hass.data[DOMAIN])
        hass.states.async_set("ostrom.grid",erg["daysum"],erg)
        
    async def handle_day_cost(call): 
        past = (datetime.datetime.utcnow() - datetime.timedelta(days=2))   
        
        erg = await hass.async_add_executor_job(ostrom_ha_cost, hass.data[DOMAIN])
        #pay =  (float(erg["price_data"]["price"]) * float(erg["consum_data"]["kWh"]) / 100)
        pay = round(erg["consum_data"]["kWh"] * erg["price_data"]["price"] / 100,5)
        hass.states.async_set("ostrom.cost",pay,erg)
        
    hass.services.async_register(DOMAIN, "get_price", handle_price_forecast)  
    hass.services.async_register(DOMAIN, "get_power", handle_pwr_relation)
    hass.services.async_register(DOMAIN, "get_cost", handle_day_cost)
    
        
        
    # Return boolean to indicate that initialization was successful.
    return True
    
    
    
