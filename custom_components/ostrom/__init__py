"""
Configuration:
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
#from homeassistant.util.json import JsonObjectType as json
import asyncio
import datetime
#import timedelta
import logging
import requests
import json
import base64
import math
from .ostrom_api import *

DOMAIN = "ostrom"
PLATFORMS = [Platform.SENSOR]

CONF_TOPIC = 'ostrom_login setup'

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    
    if (DOMAIN in  config):
      hass.data[DOMAIN] = await hass.async_add_executor_job(ostrom_ha_setup ,config[DOMAIN]["apiuser"],config[DOMAIN]["apipass"])
    #hass.data[DOMAIN]["sensors"] = {"price_now":None,"supply_past":None,"price_past":None}
    #for vlo in hass.data[DOMAIN]["sensors"]:
    #    if vlo in config[DOMAIN]:
    #        hass.data[DOMAIN]["sensors"][vlo] = config[DOMAIN][vlo]
    #hass.data[DOMAIN]["counter"] = {"cost":0,"pwr":0}            
    #hass.states.async_set("ostrom.token","test",hass.data[DOMAIN])
    
    async def handle_price_forecast(call):
        erg={"average": 28.2, "low": {"date": "2025-01-23T22:00:00.000Z", "price": 22.79}, "data": [{"date": "2025-01-23T06:00:00.000Z", "price": 32.12}, {"date": "2025-01-23T07:00:00.000Z", "price": 34.79} ]}
        now = datetime.datetime.utcnow()
        #erg = ostrom_ha_price(hass.data[DOMAIN])
        #erg = await hass.async_add_executor_job(ostrom_price,hass.data[DOMAIN]["outh"]["token"],hass.data[DOMAIN]["contract"]["zip"],now)
        #erg = ostrom_price(hass.data[DOMAIN]["outh"]["token"],hass.data["contract"]["zip"],now)
        erg = await hass.async_add_executor_job(ostrom_ha_price,hass.data[DOMAIN])
        hass.states.async_set("ostrom.price", erg["data"][0]["price"],erg)
        #if hass.data[DOMAIN]["sensors"]["price_now"] != None:
        attr = {"state_class": "total",
                    "unit_of_measurement": "EUR/kWh",
                    "device_class": "monetary"
                }
           #hass.states.async_set("sensor."+hass.data[DOMAIN]["sensors"]["price_now"],float(erg["data"][0]["price"])/100,attr)
        hass.states.async_set("sensor.ostrom_price_now",float(erg["data"][0]["price"])/100,attr)
        
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
        if hass.data[DOMAIN]["sensors"]["price_past"] != None:
            attr = {"state_class": "total",
                    "unit_of_measurement": "EUR",
                    "device_class": "monetary",
                    "imsys_date": erg['price_data']['date'] }
                    #"last_changed": erg['price_data']['date'] }
            hass.data[DOMAIN]["counter"]["cost"] = (hass.data[DOMAIN]["counter"]["cost"] + pay)         
            hass.states.async_set("sensor."+hass.data[DOMAIN]["sensors"]["price_past"],hass.data[DOMAIN]["counter"]["cost"],attr)
            #hass.states.async_set("ostrom.token","price_past",{"erg":attr})
        if hass.data[DOMAIN]["sensors"]["supply_past"] != None:
            hass.data[DOMAIN]["counter"]["pwr"] = hass.data[DOMAIN]["counter"]["pwr"] + float(erg["consum_data"]["kWh"])
            attr ={"state_class": "total",
                   "unit_of_measurement": "kWh",
                   "device_class": "energy",
                   "imsys_date": erg['consum_data']['date'] }
                   #"last_changed": erg['consum_data']['date'] }
            hass.states.async_set("sensor."+hass.data[DOMAIN]["sensors"]["supply_past"],hass.data[DOMAIN]["counter"]["pwr"],attr)
            
    async def handle_reset(call):
        hass.data[DOMAIN]["counter"]["cost"] = 0
        hass.data[DOMAIN]["counter"]["pwr"] = 0
        

    async def handle_get_timerduration(call):
        
        calltime =  datetime.now()
        #pdat = erg["data"][:36]
        #if (call.data.get('last_hour') != None):
        #    inx = max(1,( int(call.data.get('last_hour') ) - int(calltime.hour) ) )
        #    pdat = erg["data"][:inx]
        #pdat.sort(key=price_sort_helper)
        #lowt = datetime.strptime(pdat[0]["date"], '%Y-%m-%dT%H:00:00.000Z')
        #dftm = calltime - lowt
        #return (int(dftm.total_seconds()))
        
    hass.services.async_register(DOMAIN, "get_price", handle_price_forecast)  
    #hass.services.async_register(DOMAIN, "get_power", handle_pwr_relation)
    #hass.services.async_register(DOMAIN, "get_cost", handle_day_cost)
    #hass.services.async_register(DOMAIN, "reset_meter", handle_reset)
    #hass.services.async_register(DOMAIN, "timer_duration", handle_get_timerduration)
        
        
    # Return boolean to indicate that initialization was successful.
    return True
    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    #hass.data[DOMAIN][entry.entry_id] = entry.data
    hass.data[DOMAIN] = await hass.async_add_executor_job(ostrom_ha_setup ,entry.data["apiuser"],entry.data["apipass"])
        # Forward the setup to the sensor platform.
    await hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok    
    
