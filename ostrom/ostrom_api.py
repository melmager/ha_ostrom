import requests
import json
import datetime
import base64
import math

#create api key from user / password info
def get_base64_key(user, passwd):
    auth_key_str = user + ":" + passwd
    auth_key = base64.b64encode(auth_key_str.encode("ascii"))
    keyout = {"apikey":auth_key.decode("ascii")}
    return keyout
#{"apikey":"base64_api_key"}    

#get a token - token expires normaly after 3600 secs. (base64_apikey)
def ostrom_outh(mykey):
    url = "https://auth.production.ostrom-api.io/oauth2/token"
    payload = {"grant_type": "client_credentials"}
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
        "authorization": "Basic " + mykey
    }
    response = requests.post(url, data=payload, headers=headers)
    auth = json.loads(response.text)
    ok = (response.status_code == requests.codes.created)
    conf= {}
    if response.status_code == requests.codes.created:
        conf["token"] = auth['token_type'] + " " + auth['access_token']
        conf["expire"] = (datetime.datetime.utcnow() + datetime.timedelta(seconds = (int(auth['expires_in']) - 30)))
    else:
        conf["err"] = str(response.status_code) + "#" + response.text
    return conf
#{"token":"aktual_token,"expire": datetime.ablauf }

# mytoke = aktual_token , nr index contract id - normaly only 1 - so index 0 default
def ostrom_contracts(mytoken,nr=0):
    url = "https://production.ostrom-api.io/contracts"
    headers = {
        "accept": "application/json",
        "authorization": mytoken
    }
    response = requests.get(url, headers=headers)
    cdat = json.loads(response.text)
    ok = (response.status_code == requests.codes.ok)
    conf= {}
    if response.status_code == requests.codes.ok:
        conf["zip"] = cdat['data'][nr]['address']['zip']
        conf["cid"] = str(cdat['data'][nr]['id'])
    else:
        conf["err"] = str(response.status_code) + "#" + response.text
    return conf
#{'zip': 'postleitzahl', 'cid': 'vertragrsid'}

def ostrom_ha_setup(apiuser,passwd):
    config = get_base64_key(apiuser,passwd)
    config["outh"] = ostrom_outh(config["apikey"])
    config["contract"] = ostrom_contracts(config["outh"]["token"])
    return config
    

# forcast price maxinal data 36 hours and data are processed to "date" and enduser "price"
# aktual_token, Zip(Plz), startdate(now), forcast hours (max 36)
def ostrom_price(mytoken, zip, starttime, stunden = 36):
    tax = "grossKwhTaxAndLevies"
    kwprice = "grossKwhPrice"
    timeformat = "%Y-%m-%dT%H:00:00.000Z"
    now = starttime.strftime(timeformat)
    future = (starttime + datetime.timedelta(hours=stunden)).strftime(timeformat)
    url = "https://production.ostrom-api.io/spot-prices?startDate=" + now + "&endDate=" + future + "&resolution=HOUR&zip=" + zip
    headers = {
        "accept": "application/json",
        "authorization": mytoken
    }
    response = requests.get(url, headers=headers)
    erg = json.loads(response.text)
    ok = (response.status_code == requests.codes.ok)
    japex = {"average":0 , "low" : {"date":"","price":100.0}, "data":[] }
    for ix in erg['data']:
        #gesamtpreis ermitteln
        jg = round(float(ix[tax]) + float(ix[kwprice]), 2)
        #minmalwert
        if  jg < japex["low"]["price"]:
            japex["low"]["date"] = ix['date']
            japex["low"]["price"] = jg
        # liste aufbauen
        japex["data"].append({'date': ix['date'],'price':jg})
        # summe aufaddieren
        japex['average'] = japex['average']+jg
        # durchschnitt
    japex['average'] = round(japex['average'] / len(japex['data']),2)
    return japex # json.dumps(japex)
# one hour {"date":"string date.hour","price": powerprice}
#{"average": price_average over data, "low": lowes Hour, "data": [{one hour},...]}

# get used power from grid - only past data, full day
# aktual_token, vertragsid, past day - default 2 days

# data hour : {"date": "string.datetime", "kWh": from_grid }
#[{data_hour},....] start at 0:00 , end 23:00 selected day in past.
def ostrom_consum(mytoken,cid, daypast=2):
    timeformat = "%Y-%m-%dT00:00:00.000Z" #ganze tage
    dvon = (datetime.datetime.utcnow() - datetime.timedelta(days=daypast)).strftime(timeformat)
    dbis = (datetime.datetime.utcnow() - datetime.timedelta(days=(daypast-1))).strftime(timeformat)
    url = "https://production.ostrom-api.io/contracts/" + cid + "/energy-consumption?startDate=" + dvon + "&endDate=" + dbis + "&resolution=HOUR"
    headers = {
        "accept": "application/json",
        "authorization": mytoken
    }
    response = requests.get(url, headers=headers)
    ok = (response.status_code == requests.codes.ok)
    if response.status_code == requests.codes.ok:
        erg = json.loads(response.text)
        tsum = 0
        for lo in erg["data"]:
            #print(lo)
            tsum = tsum + lo["kWh"]
        erg["daysum"]=tsum
    else:
        erg= {"err" : str(response.status_code) + "#" + response.text}
    return erg #json.dumps(erg['data'])

#hass[DOMAIN]
def ostrom_ha_price(domaindata):
    
    valid = (domaindata["outh"]["expire"] > datetime.datetime.utcnow())
    if valid == False:
        domaindata["outh"] = ostrom_outh(domaindata["apikey"])
    daten = ostrom_price(domaindata["outh"]["token"],domaindata["contract"]["zip"],datetime.datetime.utcnow()) 
    return daten
    
def ostrom_ha_power(domaindata):
    valid = (domaindata["outh"]["expire"] > datetime.datetime.utcnow())
    if valid == False:
        domaindata["outh"] = ostrom_outh(domaindata["apikey"])
    daten = ostrom_consum(domaindata["outh"]["token"],domaindata["contract"]["cid"],2)  
    return daten
    
        
    
        
        

