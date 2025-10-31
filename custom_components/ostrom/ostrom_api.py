import aiohttp
import json
import datetime
import base64
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

TIMEFORMAT = "%Y-%m-%dT%H:00:00.000Z"


class APIRequestError(Exception):
    """Rich exception for API request failures.

    Attributes:
      source: str - where the failure happened: 'auth' | 'price' | 'consumption' | ...
      status: int | str - HTTP status or symbolic code ('timeout','connection','no_data', ...)
      reason: str - short reason (e.g. response.reason)
      body: str - response body (long)
      sensor_message: str - short text suitable for sensor UI
      log_message: str - verbose text suitable for logs
    """

    def __init__(self, *, source: str = None, status=None, reason=None, body=None,
                 sensor_message: str | None = None, log_message: str | None = None):
        self.source = source
        self.status = status
        self.reason = reason
        self.body = body or ""
        self.log_message = log_message or f"API {source} error {status}: {reason} - {self.body}"
        # Kurztext für Sensor/UI
        self.sensor_message = sensor_message or f"{(source or 'api').upper()}: {status} {reason}"
        super().__init__(self.log_message)

    def as_sensor_text(self, maxlen: int = 120) -> str:
        txt = str(self.sensor_message)
        if maxlen and len(txt) > maxlen:
            return txt[: maxlen - 3] + "..."
        return txt

    def as_log_text(self) -> str:
        return str(self.log_message)


class OstromApi:
    def __init__(self, user: str, pwd: str) -> None:
        """Initialise."""
        self.user = user
        self.pwd = pwd
        self.zip = "00000"
        self.cid = "0"
        self.expire = datetime.datetime.utcnow()
        self.token = None
        auth_key_str = user + ":" + pwd
        auth_key = base64.b64encode(auth_key_str.encode("ascii"))
        self.apikey = auth_key.decode("ascii")

    def set_zip_cid(self, zipin, cidin):
        self.zip = zipin
        self.cid = cidin

    async def ostrom_outh(self):
        """Get OAuth token. Raise APIRequestError on failures (source='auth')."""
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
                    if response.status in (200, 201):
                        try:
                            auth = json.loads(text)
                        except Exception as e:
                            _LOGGER.error("Failed to parse auth JSON: %s", e)
                            raise APIRequestError(source="auth", status=response.status, reason="invalid_json",
                                                  body=text,
                                                  sensor_message="Auth parse error",
                                                  log_message=f"Auth parse error: {e} - response: {text}")
                        access_token = auth.get("access_token") or auth.get("token")
                        token_type = auth.get("token_type", "Bearer")
                        expires_in = int(auth.get("expires_in", 3600))
                        if not access_token:
                            _LOGGER.error("Authentication response missing access token: %s", text)
                            raise APIRequestError(source="auth", status=response.status, reason="missing_token", body=text,
                                                  sensor_message="Auth missing token",
                                                  log_message=f"Auth missing token: {text}")
                        self.token = f"{token_type} {access_token}"
                        self.expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=(expires_in - 30))
                        return
                    else:
                        _LOGGER.error("Authentication failed: status=%s, text=%s", response.status, text)
                        raise APIRequestError(source="auth", status=response.status, reason=response.reason or "auth_failed", body=text,
                                              sensor_message=f"Auth {response.status}", log_message=f"Auth failed: {response.status} - {text}")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during Ostrom API authentication")
            raise APIRequestError(source="auth", status="timeout", reason="Timeout", body="",
                                  sensor_message="Auth timeout", log_message="Timeout during authentication")
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error during Ostrom API authentication: %s", str(e))
            raise APIRequestError(source="auth", status="connection", reason=str(e), body="",
                                  sensor_message="Auth connection error", log_message=f"Connection error during auth: {e}")
        except APIRequestError:
            raise
        except Exception as e:
            _LOGGER.exception("Unexpected error during auth: %s", e)
            raise APIRequestError(source="auth", status="exception", reason=str(e), body="",
                                  sensor_message="Auth exception", log_message=f"Unexpected auth error: {e}")

    async def ostrom_price(self, starttime, stunden=36):
        """Fetch spot prices. On HTTP/parse/timeout errors raise APIRequestError(source='price')."""
        tax = "grossKwhTaxAndLevies"
        kwprice = "grossKwhPrice"
        timeformat = TIMEFORMAT
        now = starttime.strftime(timeformat)
        future = (starttime + datetime.timedelta(hours=stunden)).strftime(timeformat)
        url = f"https://production.ostrom-api.io/spot-prices?startDate={now}&endDate={future}&resolution=HOUR&zip={self.zip}"
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    text = await response.text()
                    if response.status != 200:
                        _LOGGER.error("Get Price failed: status=%s, text=%s", response.status, text)
                        raise APIRequestError(source="price", status=response.status, reason=response.reason or "http_error", body=text,
                                              sensor_message=f"Price {response.status}", log_message=f"Price request failed: {response.status} - {text}")
                    try:
                        erg = json.loads(text)
                    except Exception as e:
                        _LOGGER.error("Ostrom API: Failed to parse JSON response: %s", e)
                        raise APIRequestError(source="price", status="invalid_json", reason=str(e), body=text,
                                              sensor_message="Price JSON parse error", log_message=f"Price JSON parse error: {e} - body: {text}")

                    data_list = erg.get("data") if isinstance(erg, dict) else None
                    # If data_list is missing or empty -> raise APIRequestError so coordinator decides
                    if not data_list:
                        _LOGGER.warning("Ostrom API: Keine Preisdaten geliefert oder 'data' fehlt/leer.")
                        raise APIRequestError(source="price", status="no_data", reason="no_data", body=text,
                                              sensor_message="Price no data", log_message=f"No data in price response: {text}")

                    japex = {"average": 0.0, "low": {"date": "", "price": 1e9}, "data": []}
                    for ix in data_list:
                        try:
                            tax_val = float(ix.get(tax, 0.0))
                            kw_val = float(ix.get(kwprice, 0.0))
                        except Exception:
                            _LOGGER.debug("Malformed price entry, skipping: %s", ix)
                            continue
                        total_price_eur = round(tax_val + kw_val, 4)  # EUR/kWh
                        total_price_cents = round(total_price_eur * 100, 2)  # cent/kWh
                        japex["average"] += total_price_cents
                        if total_price_cents < japex["low"]["price"]:
                            japex["low"]["date"] = ix.get("date", "")
                            japex["low"]["price"] = total_price_cents
                        japex["data"].append({"date": ix.get("date", ""), "price": total_price_cents})

                    if not japex["data"]:
                        _LOGGER.warning("Ostrom API: Alle Einträge ungültig.")
                        raise APIRequestError(source="price", status="invalid_entries", reason="all_invalid", body=text,
                                              sensor_message="Price entries invalid", log_message=f"All price entries invalid: {text}")

                    japex["average"] = round(japex["average"] / len(japex["data"]), 2)
                    japex["price_source"] = "ostrom"
                    return japex
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during Ostrom API Get Price")
            raise APIRequestError(source="price", status="timeout", reason="Timeout", body="",
                                  sensor_message="Price timeout", log_message="Timeout during price request")
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error during Ostrom API get price: %s", str(e))
            raise APIRequestError(source="price", status="connection", reason=str(e), body="",
                                  sensor_message="Price connection error", log_message=f"Connection error during price request: {e}")
        except APIRequestError:
            raise
        except Exception as e:
            _LOGGER.exception("Unexpected error during Ostrom API get price: %s", e)
            raise APIRequestError(source="price", status="exception", reason=str(e), body="",
                                  sensor_message="Price exception", log_message=f"Unexpected price error: {e}")

    async def ostrom_consum(self, starttime, stunden=1):
        """Fetch consumption for contract. Raises APIRequestError(source='consumption') on errors."""
        timeformat = TIMEFORMAT
        dvon = starttime.strftime(timeformat)
        dbis = (starttime + datetime.timedelta(hours=stunden)).strftime(timeformat)
        url = f"https://production.ostrom-api.io/contracts/{self.cid}/energy-consumption?startDate={dvon}&endDate={dbis}&resolution=HOUR"
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    text = await response.text()
                    if response.status != 200:
                        _LOGGER.error("Get Consum failed: status=%s, text=%s", response.status, text)
                        raise APIRequestError(source="consumption", status=response.status, reason=response.reason or "http_error", body=text,
                                              sensor_message=f"Consum {response.status}", log_message=f"Consum request failed: {response.status} - {text}")
                    try:
                        cdat = json.loads(text)
                    except Exception as e:
                        _LOGGER.error("Failed to parse consumption JSON: %s", e)
                        raise APIRequestError(source="consumption", status="invalid_json", reason=str(e), body=text,
                                              sensor_message="Consum JSON parse error", log_message=f"Consum JSON parse error: {e} - body: {text}")
                    return cdat.get("data", [])
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout during Ostrom API Get Consum")
            raise APIRequestError(source="consumption", status="timeout", reason="Timeout", body="",
                                  sensor_message="Consum timeout", log_message="Timeout during consumption request")
        except aiohttp.ClientError as e:
            _LOGGER.error("Connection error during Ostrom API get consum: %s", str(e))
            raise APIRequestError(source="consumption", status="connection", reason=str(e), body="",
                                  sensor_message="Consum connection error", log_message=f"Connection error during consum request: {e}")
        except APIRequestError:
            raise
        except Exception as e:
            _LOGGER.exception("Unexpected error during Ostrom API get consum: %s", e)
            raise APIRequestError(source="consumption", status="exception", reason=str(e), body="",
                                  sensor_message="Consum exception", log_message=f"Unexpected consum error: {e}")

    async def get_forecast_prices(self):
        """High-level helper: ensure token, then request prices. Propagates APIRequestError."""
        jetzt = datetime.datetime.utcnow()
        if not self.expire or self.expire < jetzt:
            await self.ostrom_outh()
        # will raise APIRequestError on failure (price or auth)
        daten = await self.ostrom_price(jetzt, stunden=36)
        return daten

