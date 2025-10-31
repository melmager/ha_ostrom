"""Sensor platform for Ostrom integration."""
from __future__ import annotations

from typing import Any
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import OstromCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ostrom sensors from a config entry."""
    coordinator: OstromCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Create sensor entities
    entities = [
        OstromPriceNowSensor(coordinator),
        OstromAveragePriceSensor(coordinator),
        OstromLowestPriceSensor(coordinator),
        OstromLowestPriceNowBinarySensor(coordinator),
    ]
    
    async_add_entities(entities)


class OstromPriceNowSensor(CoordinatorEntity, SensorEntity):
    """Sensor for current Ostrom spot price."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Ostrom Price Now"
        self._attr_unique_id = "ostrom_price_now"

    @property
    def native_value(self) -> float | None:
        """Return the current price in EUR/kWh."""
        if self.coordinator.data is None:
            # No data available - return fallback
            _LOGGER.debug("No coordinator data, using fallback price")
            return 0.30  # Default fallback price in EUR/kWh
        
        try:
            data_list = self.coordinator.data.get("data", [])
            if not data_list:
                _LOGGER.warning("Coordinator data has no price entries, using fallback")
                return 0.30
            
            # First entry is current hour price in cents/kWh, convert to EUR/kWh
            price_cents = float(data_list[0].get("price", 30.0))
            return round(price_cents / 100.0, 4)
        except (KeyError, IndexError, ValueError, TypeError) as err:
            _LOGGER.error("Error extracting price: %s, using fallback", err)
            return 0.30

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {}
        
        if self.coordinator.data is not None:
            attrs["price_source"] = self.coordinator.data.get("price_source", "unknown")
        else:
            attrs["price_source"] = "fallback"
        
        if self.coordinator.last_update_error:
            attrs["last_error"] = self.coordinator.last_update_error
        
        return attrs


class OstromAveragePriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for average Ostrom spot price."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Ostrom Average Price"
        self._attr_unique_id = "ostrom_average_price"

    @property
    def native_value(self) -> float | None:
        """Return the average price in EUR/kWh."""
        if self.coordinator.data is None:
            return None
        
        try:
            # Average is stored in cents/kWh, convert to EUR/kWh
            avg_cents = float(self.coordinator.data.get("average", 0.0))
            return round(avg_cents / 100.0, 4)
        except (ValueError, TypeError) as err:
            _LOGGER.error("Error extracting average price: %s", err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {}
        
        if self.coordinator.data is not None:
            attrs["price_source"] = self.coordinator.data.get("price_source", "unknown")
        else:
            attrs["price_source"] = "unavailable"
        
        return attrs


class OstromLowestPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for lowest Ostrom spot price in forecast."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "EUR/kWh"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Ostrom Lowest Price"
        self._attr_unique_id = "ostrom_lowest_price"

    @property
    def native_value(self) -> float | None:
        """Return the lowest price in EUR/kWh."""
        if self.coordinator.data is None:
            return None
        
        try:
            low_info = self.coordinator.data.get("low", {})
            if not low_info:
                return None
            
            # Lowest price is in cents/kWh, convert to EUR/kWh
            low_cents = float(low_info.get("price", 0.0))
            return round(low_cents / 100.0, 4)
        except (ValueError, TypeError) as err:
            _LOGGER.error("Error extracting lowest price: %s", err)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {}
        
        if self.coordinator.data is not None:
            low_info = self.coordinator.data.get("low", {})
            if low_info:
                attrs["lowest_price_time"] = low_info.get("date")
            attrs["price_source"] = self.coordinator.data.get("price_source", "unknown")
        else:
            attrs["price_source"] = "unavailable"
        
        return attrs


class OstromLowestPriceNowBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating if current price is the lowest."""

    def __init__(self, coordinator: OstromCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = "Ostrom Lowest Price Now"
        self._attr_unique_id = "ostrom_lowest_price_now"

    @property
    def is_on(self) -> bool:
        """Return True if current price is lowest and source is ostrom."""
        if self.coordinator.data is None:
            return False
        
        # Only return True for ostrom source data
        price_source = self.coordinator.data.get("price_source", "unknown")
        if price_source != "ostrom":
            return False
        
        try:
            data_list = self.coordinator.data.get("data", [])
            low_info = self.coordinator.data.get("low", {})
            
            if not data_list or not low_info:
                return False
            
            # Compare current price with lowest
            current_price = float(data_list[0].get("price", 0.0))
            lowest_price = float(low_info.get("price", 0.0))
            
            # Allow small tolerance for floating point comparison
            return abs(current_price - lowest_price) < 0.01
        except (KeyError, IndexError, ValueError, TypeError) as err:
            _LOGGER.error("Error checking lowest price: %s", err)
            return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {}
        
        if self.coordinator.data is not None:
            attrs["price_source"] = self.coordinator.data.get("price_source", "unknown")
        else:
            attrs["price_source"] = "unavailable"
        
        return attrs

