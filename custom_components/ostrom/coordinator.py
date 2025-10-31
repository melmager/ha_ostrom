"""Integration 101 Template integration using DataUpdateCoordinator."""

from datetime import timedelta, datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_change

from .ostrom_api import OstromApi, APIConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_get_data(lnk_api,get_cost):
    # Replace with your actual async data fetching logic
    # For example, fetch from API or storage
    return {
        "price_48h_past": 0.25,
        "consum": 12.5,
        "price": 3.12,
        "time": "2025-08-20T01:01:00Z",
    }

class OstromCoordinator(DataUpdateCoordinator):
    
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self.apiuser = config_entry.data.get("apiuser")
        self.apipass = config_entry.data.get("apipass")
        self.zip_code = config_entry.data.get("zip")
        self.contract_id = config_entry.data.get("contract_id")
        self.use_past_sensor = config_entry.options.get("use_past_sensor", False)
        # Der Index kann bei Multi-Contract später gesetzt werden (hier z.B. 1)
        self.contract_index = config_entry.data.get("contract_index", 1)
        self.want_consumption = config_entry.data.get("want_consumption", False)

        self.api_client = OstromApi(self.apiuser, self.apipass, hass.loop)
        # Setze ZIP und CID direkt nach Instanziierung
        self.api_client.set_zip_cid(self.zip_code, self.contract_id)
        # Lies Option aus:
        self.use_past_sensor = config_entry.options.get("use_past_sensor", False)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            # No update_interval, we'll trigger manually at minute 1 every hour
        )
        self._hass = hass
        
    async def _async_update_data(self):
        ostromdaten = {
            "cost_48h_past": 0,
            "price": 0,           # in Cent!
            "actual_price": 0,    # in EUR!
            "time": "",
            "past": "",
            "raw": "",
            "last_update_failed": False,
            "last_update_error": "",
        }
        try:
            erg = await self.api_client.get_forecast_prices()
            price_cent = erg["data"][0]["price"]              # Cent vom API
            price_eur = price_cent / 100                      # Umrechnung in Euro

            ostromdaten["price"] = price_cent                 # Cent
            ostromdaten["actual_price"] = price_eur           # Euro
            ostromdaten["time"] = erg["data"][0]["date"]
            ostromdaten["raw"] = erg
            # Verbrauchsdaten holen, wenn gewünscht
            if self.use_past_sensor: 
                ostromdaten.update(await self.api_client.get_past_price_consum())
                #consum = await self.api_client.get_past_price_consum()
            #ostromdaten["consum"] = consum
            # Letztes Update war erfolgreich:
            ostromdaten["last_update_failed"] = False
            ostromdaten["last_update_error"] = ""
            return ostromdaten
        except Exception as e:
            import datetime   
            # Logging und Retry-Hinweis
            _LOGGER.error(f"Ostrom API update failed: {e}")
            retry_minutes = 10
            retry_time = (datetime.datetime.now() + timedelta(minutes=retry_minutes)).strftime("%H:%M")
            _LOGGER.warning(f"Abfragefehler, Retry um {retry_time}")
            # Retry auslösen
            from homeassistant.helpers.event import async_call_later
            async_call_later(self._hass, retry_minutes * 60, self._retry_update)

            # Alte Daten behalten, aber Fehler-Flags setzen
            if hasattr(self, "data") and self.data:
                failed_data = dict(self.data)
            else:
                failed_data = {
                    "cost_48h_past": None,
                    "price": None,
                    "actual_price": None,
                    "time": None,
                    "raw": None,
                }
            failed_data["last_update_failed"] = True
            failed_data["last_update_error"] = str(e)
            return failed_data

    async def _retry_update(self, _):
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _LOGGER.info(f"Führe Retry-Update aus (nach Fehler) um {now}")
        await self.async_refresh()  

    async def async_setup_hourly_update(self):
        
        async def hourly_update(now):
            _LOGGER.debug("Triggering hourly update at minute 1")
            await self.async_refresh()

        # Schedule update at minute 1 every hour
        async_track_time_change(
            self._hass,
            hourly_update,
            minute=1,
            second=0,
        )
        
