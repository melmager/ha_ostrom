from homeassistant.core import HomeAssistant
from homeassistant.const import (
   STATE_UNKNOWN
   )
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorStateClass,
)   
from homeassistant.helpers.entity import Entity
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ostrom"

class Ostrom_Price_Now(SensorEntity):
    
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "EUR/kWh"
    
    attr = {"state_class": "total",
                    "unit_of_measurement": "EUR/kWh",
                    "device_class": "monetary"
            }
    
    def __init__(self):
        self._name = "Ostrom Price Now"
        self._uid = "ostrom_price_now"
        #            "state_class": "total",
        #            "unit_of_measurement": "EUR",
        #            "device_class": "monetary",
                    
    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._uid
                
    
    #async def async_update(self):
    #    # Your logic to get the new sensor value
    #    new_value = self.calculate_new_value() 
    #    self.state = new_value

    #def calculate_new_value(self):
    #    # Replace this with your actual logic to determine the new value
    #    return 42.0
        
    async def set_sensor_state(self, new_state, attributes=None):
           self._state = new_state
           if attributes:
               self._attributes = attributes
           self.async_write_ha_state() # Important: Update the state in HA
           # OR use hass.states.set directly (if not using async_write_ha_state)
           # self._hass.states.set(self.entity_id, new_state, attributes)  
           
