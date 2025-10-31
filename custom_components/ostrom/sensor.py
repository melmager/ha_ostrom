from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

class OstromApiStatusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        contract_id = getattr(coordinator, "contract_id", "unknown")
        contract_index = getattr(coordinator, "contract_index", 1)
        self._attr_name = f"Ostrom API Status ({contract_index})"
        self._attr_unique_id = f"ostrom_api_status__{contract_id}"
        self._attr_icon = "mdi:cloud-alert"

    @property
    def native_value(self):
        failed = self.coordinator.data.get("last_update_failed", False)
        return "Error" if failed else "OK"

    @property
    def extra_state_attributes(self):
        return {
            "last_error": self.coordinator.data.get("last_update_error"),
            "last_time": self.coordinator.data.get("time"),
        }

class Ostrom_Price_Now(CoordinatorEntity, SensorEntity):
    
    def __init__(self, coordinator):
        super().__init__(coordinator)
        contract_id = getattr(coordinator, "contract_id", "unknown")
        contract_index = getattr(coordinator, "contract_index", 1)
        self._attr_name = f"Ostrom actual Price ({contract_index})"
        self._attr_native_unit_of_measurement = "EUR/kWh"
        self._attr_unique_id = f"ostrom_price_now_{contract_id}"
        self._attr_icon = "mdi:currency-eur"
        #_LOGGER.warning(f"Ostrom_Price_Now: contract_id={contract_id}")
        #_LOGGER.warning(f"Ostrom_Price_Now: contract_index={contract_index}")

    @property
    def native_value(self):
        eur_price = self.coordinator.data.get("actual_price")
        return eur_price
        
    @property
    def extra_state_attributes(self):
        return {
            "id": self._attr_unique_id,
        }    
        
class Ostrom_Price_Raw(CoordinatorEntity, SensorEntity):
    
    def __init__(self, coordinator):
        super().__init__(coordinator)
        contract_id = getattr(coordinator, "contract_id", "unknown")
        contract_index = getattr(coordinator, "contract_index", 1)
        self._attr_name = f"Ostrom Raw forcast Data ({contract_index})"
        self._attr_unique_id = f"ostrom_raw_forecastdata_{contract_id}"
        self._attr_icon = "mdi:chart-timeline-variant"
        
    @property
    def native_value(self):
        cent_price = self.coordinator.data.get("price")
        return cent_price
        
    @property
    def extra_state_attributes(self):
        raw_data = self.coordinator.data.get("raw") 
        attrs = {}
        if raw_data:
            attrs.update(raw_data)
        attrs["id"] = self._attr_unique_id
        return attrs    

class Cost_48hPast(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        contract_id = getattr(coordinator, "contract_id", "unknown")
        contract_index = getattr(coordinator, "contract_index", 1)
        self._attr_name = f"Cost 48h Past ({contract_index})"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_unique_id = f"ostrom_cost_48h_past_{contract_id}"
        self._attr_device_class = "monetary"
        self._attr_icon = "mdi:cash"

    @property
    def native_value(self):
        return self.coordinator.data.get("cost_48h_past")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        return {
            "consum": data.get("consum_48h_past"),
            "price": data.get("price_48h_past"),
            "time": data.get("time_48h_past"),
            "id": self._attr_unique_id,
            "date_mismatch": data.get("date_mismatch", False),  # <------ hier das Boolean-Attribut!
        }


class LowestPriceNowBinary(CoordinatorEntity, BinarySensorEntity):
     def __init__(self, coordinator):
        super().__init__(coordinator)
        contract_id = getattr(coordinator, "contract_id", "unknown")
        contract_index = getattr(coordinator, "contract_index", 1)
        self._attr_name = f"Lowest Price Now ({contract_index})"
        self._attr_unique_id = f"ostrom_lowest_price_now_{contract_id}"
        self._attr_device_class = "power"
        self._attr_icon = "mdi:power-plug"
        
     def truncate_float(self, val, digits=2):
        if val is None:
            return None
        try:
            return int(float(val) * 10**digits) / 10**digits
        except (TypeError, ValueError):
            return None   
            
     @property
     def is_on(self):
        raw_data = self.coordinator.data.get("raw")
        if raw_data and "low" in raw_data and "data" in raw_data and len(raw_data["data"]) > 0:
            low_price = self.truncate_float(raw_data["low"]["price"], 1)
            current_price = self.truncate_float(raw_data["data"][0]["price"], 1)
            return current_price == low_price
        return False        

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        Ostrom_Price_Raw(coordinator),
        Ostrom_Price_Now(coordinator),
        LowestPriceNowBinary(coordinator),
        OstromApiStatusSensor(coordinator), 
    ]
    if config_entry.options.get("use_past_sensor", False):
        entities.append(Cost_48hPast(coordinator))

    async_add_entities(entities)    