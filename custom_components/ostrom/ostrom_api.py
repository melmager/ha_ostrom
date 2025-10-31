import aiohttp
import json
import datetime
import base64
import math
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

TIMEFORMAT = "%Y-%m-%dT%H:00:00.000Z"

class OstromApi:
    
    def __init__(self,user: str, pwd: str, haloop) -> None:
        """Initialise."""
        self.user = user
        self.pwd = pwd
        self.zip = "00000"
        self.loop = haloop
        self.expire = datetime.datetime.utcnow()
        auth_key_str = user + ":" + pwd
        auth_key = base64.b64encode(auth_key_str.encode("ascii"))
        self.apikey = auth_key.decode("ascii")
        self.api_error_cnt = 0
        self-api_error_msg = "OK"
        
    def set_zip_cid(self,zipin,cidin):
        self.zip = zipin
        self.cid = cidin
        
    def get_api_status(self):
        if self.api_error_msg == "OK":
            self.api_error_cnt = 0
            stat = "OK"
        else:
            self.api_error_cnt =+ 1
            stat = "Error_" + str(api_error_cnt)
        return stat , self.api_error_msg   
        
    #get a token - token expires normaly after 3600 secs. (base64_apikey)
    async def ostrom_outh(self):    
        url = "https://auth.production.ostrom-api.io/oauth2/token"
        payload = {"grant_type": "client_credentials"}
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "authorization": "Basic " + self.apikey
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, headers=headers, timeout=10) as response:
                   text = await response.text()
                   self.api_error_msg = response.reason
                   if response.status == 201:
                       auth = json.loads(text)
                       self.token = auth['token_type'] + " " + auth['access_token']
                       self.expire = (datetime.datetime.utcnow() + datetime.timedelta(seconds = (int(auth['expires_in']) - 30))) 
                   else:
                       _LOGGER.error("Authentication failed: status=%s, text=%s", response.status, text)
                       raise APIAuthError(f"Auth failed: {response.status} - {text}")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during Ostrom API authentication")
            raise APIAuthError("Timeout during authentication") 
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error during Ostrom API authentication: %s", str(e))
            raise APIAuthError(f"Connection error: {str(e)}")
        except Exception as e:
            _LOGGER.error("Unexpected error during Ostrom API authentication: %s", str(e))
            raise    
                       
    #  liste alle Verträge
    async def ostrom_contracts(self):
        url = "https://production.ostrom-api.io/contracts"
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    text = await response.text()
                    if response.status == 200:
                        cdat = json.loads(text)
                        return cdat['data']
                        #self.zip = cdat['data'][nr]['address']['zip']
                        #self.cid = str(cdat['data'][nr]['id'])
                    else:
                        _LOGGER.error("Get Contract failed: status=%s, text=%s", response.status, text) 
                        raise APIConnectionError(f"Contracts failed: {response.status} - {text}")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during Ostrom API Get Contracts")
            raise APIAuthError("Timeout during contract") 
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error during Ostrom API get contracts: %s", str(e))
            raise APIAuthError(f"Connection error: {str(e)}")
        except Exception as e:
            _LOGGER.error("Unexpected error during Ostrom API contract: %s", str(e))
            raise      
        
    def _fallback_entry(self,source: str = "fallback"):
            """Return a fallback japex structure. price expressed as float (EUR)."""
            aktuelle_stunde = datetime.datetime.utcnow().hour
            default_price = round((30.0 + (aktuelle_stunde / 100.0)),2)
            iso_now = datetime.datetime.utcnow().strftime(TIMEFORMAT)
            japex = {
                "average": default_price,
                "low": {"date": iso_now, "price": default_price},
                "data": [{"date": iso_now, "price": default_price}],
                "price_source": source,
            }
            return japex    
                
    # forcast price maxinal data 36 hours and data are processed to "date" and enduser "price"
    # forcast hours (max 36)
    async def ostrom_price(self, starttime, stunden = 36):
        tax = "grossKwhTaxAndLevies"
        kwprice = "grossKwhPrice"
        timeformat = "%Y-%m-%dT%H:00:00.000Z"
        now = starttime.strftime(timeformat)
        future = (starttime + datetime.timedelta(hours=stunden)).strftime(timeformat)
        url = "https://production.ostrom-api.io/spot-prices?startDate=" + now + "&endDate=" + future + "&resolution=HOUR&zip=" + self.zip
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:    
                    text = await response.text()
                    self.api_error_msg = response.reason
                    if response.status == 200:
                        try:
                            erg = json.loads(text)
                        except Exception as e:
                            _LOGGER.error("Ostrom API: Failed to parse JSON response: %s", e)
                            return self._fallback_entry("fallback")
                            
                        japex = {"average":0 , "low" : {"date":"","price":100.0}, "data":[] }
                        
                        if not erg['data']:
                             _LOGGER.warning("Ostrom API: Keine Preisdaten geliefert, erg['data'] ist leer.")
                             return self._fallback_entry("fallback")
                        
                        for ix in erg['data']:
                            #gesamtpreis ermitteln
                            total_price = round(float(ix[tax]) + float(ix[kwprice]), 2)
                            japex["average"] += total_price
                            #minmalwert
                            if  total_price < japex["low"]["price"]:
                                japex["low"]["date"] = ix['date']
                                japex["low"]["price"] = total_price
                            # liste aufbauen
                            japex["data"].append({'date': ix['date'],'price': total_price})
                            
                        if not japex["data"]:
                            # all entries were malformed
                            _LOGGER.warning("Ostrom API: Alle Einträge ungültig.")
                            return self._fallback_entry("fallback")
    
                        # durchschnitt
                        japex['average'] = round(japex['average'] / len(japex['data']),2)
                        japex["price_source"] = "ostrom"
                        return japex # json.dumps(japex)
                        # one hour {"date":"string date.hour","price": powerprice}
                        #{"average": price_average over data, "low": lowes Hour, "data": [{one hour},...]  
                    else:
                        _LOGGER.error("Get Price failed: status=%s, text=%s", response.status, text) 
                        #raise APIConnectionError(f"get Price failed: {response.status} - {text}")
                        return self._fallback_entry("fallback")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during Ostrom API Get Contracts")
            #raise APIConnectionError("Timeout during get Price")
            return self._fallback_entry("fallback")
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error during Ostrom API get contracts: %s", str(e))
            return self._fallback_entry("fallback")
            #raise APIConnectionError(f"Price error: {str(e)}")
        except Exception as e:
            _LOGGER.error("Unexpected error during Ostrom API get price: %s", str(e))
            #raise       
            return self._fallback_entry("fallback")
                    
       
    async def ostrom_consum(self, starttime, stunden = 1):
        timeformat = "%Y-%m-%dT%H:00:00.000Z"
        dvon = starttime.strftime(timeformat)
        dbis = (starttime + datetime.timedelta(hours=stunden)).strftime(timeformat)
        url = "https://production.ostrom-api.io/contracts/" + self.cid + "/energy-consumption?startDate=" + dvon + "&endDate=" + dbis + "&resolution=HOUR"
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        cdat = json.loads(text)
                        return cdat['data']
                    else:
                        _LOGGER.error("Get Consum failed: status=%s, text=%s", response.status, text) 
                        raise APIConnectionError(f"get Consum failed: {response.status} - {text}")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during Ostrom API Get Consum")
            raise APIConnectionError("Timeout during get Price") 
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error during Ostrom API get consum: %s", str(e))
            raise APIConnectionError(f"Price error: {str(e)}")
        except Exception as e:
            _LOGGER.error("Unexpected error during Ostrom API get consum: %s", str(e))
            raise                         
                
    async def get_forecast_prices(self):
        jetzt = datetime.datetime.utcnow()
        # Prüfe die Token-Gültigkeit:
        try:
            if not self.expire or self.expire < jetzt:
                await self.ostrom_outh()
        except APIAuthError as e:
            _LOGGER.error("Ostrom auth failed during get_forecast_prices: %s", e)
            # return structured fallback via central helper
            return self._fallback_entry("fallback")        
        # Preise mit gültigem Token abfragen:
        daten = await self.ostrom_price(jetzt, stunden=36)
        return daten            
        
        
    async def get_past_price_consum(self):
        # Zeitpunkt vor 48h
        past = datetime.datetime.utcnow() - datetime.timedelta(hours=48)
        jetzt = datetime.datetime.utcnow()   
        if not self.expire or self.expire < jetzt:
            await self.ostrom_outh()
        # Preis für die Stunde vor 48h holen
        price_data = await self.ostrom_price(past, stunden=1)
        price = price_data["data"][0]["price"]  # in cent!
        date_price = price_data["data"][0]["date"]
        # Verbrauch für die Stunde vor 48h holen
        consum_data = await self.ostrom_consum(past, stunden=1)
        consum_kwh = consum_data[0]["kWh"]
        date_consum = consum_data[0]["date"]
        # Vergleich der Zeitstempel
        date_mismatch = (date_price != date_consum)
        if date_mismatch:
            _LOGGER.warning(f"Mismatch in date between price ({date_price}) and consumption ({date_consum}) data.")
            kosten = 0
        else:
            kosten = round(price * consum_kwh / 100, 4)
        return {
            "cost_48h_past": kosten,
            "price_48h_past": price,
            "consum_48h_past": consum_kwh,
            "time_48h_past": date_price,
            "date_mismatch": date_mismatch,
        }    


class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""
