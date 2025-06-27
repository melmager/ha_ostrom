# ha_ostrom
Integration Ostrom in to Home Assistant

Beta Version!
Beginner Level Programming for Homeassistant#
Version 3.0


Path in Home Assistant 
/homeassistant/custom_components/ostrom

Man muss Kunde bei Ostrom sein
in der Web App account erstellen

Beschreibung der Web API https://docs.ostrom-api.io/reference/introduction

Zugang erstellen https://developer.ostrom-api.io/auth/login

dort hat man die Wahl zwischen Sandbox und Production - meine Software arbeitet mit Production Umgebung

Beim Anlegen erhält man eine Client ID und erzeugt dann ein Secret - beides wird benötigt

Setup geht via GUI 


 es wird 1 services erzeugt 
-   ostrom.get_price
	```
	Abfrage von Forcast Preisen maximal 36 Stunden in die Zukunft,
	Normal gibt es neue Daten nachmittags um 14 oder 15 Uhr
	Aufruf ohne Optionen - muss Stündliche aufgerufen werden
	im states ostrom.price was von der Api angelegt wird, Aktueller Strompreis in Cent
	attribute:
	average: durchschnittspreis in cent von den gelieferten  Daten
	low: 
		date: 'Zeitpunkt des günstigsten Strompreises'
		price: 'der dann gültige Preis in Cent' 
	data: liste von forcast preisen jeweils mit
  		date "datum/uhrzeit"
  		price "centpreis zu dem zeitpunkt"
	
	```
zusätzlich wird ein sensor.ostrom_price_now angelegt der den Strompreis in EUR/kWh liefert.
```
state_class: total
unit_of_measurement: EUR/kWh
device_class: monetary
```

Damit sollte man den
https://github.com/zeronounours/HA-custom-component-energy-meter
ansteuern können, der braucht allerdings Ein Zähler im Zählerschrank der den Aktuellen Verbrauch erfasst - 

Den in alter Version vorhandenen sensor der Kosten und Verbrauch erfasst hat wurde rausgeworfen. Leider liegen die Verbrauchsdaten vom Smartmeter nur mit eine Verzögerung von 2 tagen bei Ostrom vor und Homeassistant kann nicht mit alten Sensorwerten arbeiten. Das verwirrt mehr wie es hilft das zwischen sensor erstellungszeit und den gespeicherten Verbrauchswerten 48 Stunden differenz sind.

für die Darstellung sollte man 
https://github.com/RomRider/apexcharts-card
nutzen
```
type: custom:apexcharts-card
graph_span: 48h
span:
  start: hour
  offset: "-12h"
now:
  show: true
  label: Jetzt
all_series_config:
  unit: cent
header:
  show: true
  show_states: true
  colorize_states: true
  title: Preis Forecast
series:
  - entity: ostrom.price
    data_generator: |
      return entity.attributes.data.map((start, index) => {
        return [new Date(start["date"]).getTime(), (entity.attributes.data[index]["price"])];
      });
    extend_to: false
    show:
      legend_value: false
      in_header: false
    name: ostrom_forecast
  - entity: ostrom.price
    extend_to: now

```

die version gefällt mir am besten :-)




Falls einer noch kein Ostrom Kunde ist unter Promo.text 
ist mein Promocode den man bei Neuvertrag angeben kann.
	
