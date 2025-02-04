# ha_ostrom
Integration Ostrom in to Home Assistant

only Playground!
Beginner Level Programming for Homeassistant#

Path in Home Assistant 
/homeassistant/custom_components/ostrom

Man muss Kunde bei Ostrom sein
in der Web App account erstellen

Beschreibung der Web API https://docs.ostrom-api.io/reference/introduction

Zugang erstellen https://developer.ostrom-api.io/auth/login

dort hat man die Wahl zwischen Sandbox und Production - meine Software arbeitet mit Production Umgebung

Beim Anlegen erhält man eine Client ID und erzeugt dann ein Secret - beides wird benötigt

eintrag in configuration.yaml
```
ostrom:
  apiuser: "ostrom_user_id"
  apipass: "ostrom_secret"
```


 es werden 2 services erzeugt 
-   ostrom.get_price
-   ostrom.get_power

beide aktuell ohne übergabe von daten
als ergebnis wird ein states erzeugt, im fall von ostrom.getprice
als state der aktueller preis in cent(brutto) 
(aus dem grund muss der service jede stunde aufgerufen werden 
(am besten nicht zur vollen strunde sondern eine minute verzögert.)

im states ostrom.price was von der Api angelegt wird gibt es attribute:
```
average: durchschnittspreis in cent von den gelieferten  Daten
	low: 
		date: '2025-02-04T12:00:00.000Z'
		price: 29.33
		
 low["date"] Uhrzeit vom nidrigsten Preis  
 low["price"] der preis in cent zu dem zeitpunkt

 
data: liste von forcast preisen
  jeweils mit
  date "datum/uhrzeit"
  price "centpreis zu dem zeitpunkt"
```
also preis nächste stunde nach service aufruf
data[1]["price"] 

daten menge ist abhängig von der Uhrzeit - in der regel gibt es um 14 Uhr daten bis 23 Uhr nächsten tag

ostrom.get_power geht nur wenn in der Handy Anwendung von Ostrom auch Stromdaten angezeigt werden - dazu muss man ein Smartmeter haben
ansonsten gibt es nur fehler von der API
und der service ermittelt im Moment immer den Stromverbrauch von einem gesamten Tag , start 0 Uhr 
also nur einmal täglich aufrufen :-) 

states ostrom.grid

das ergebnis wird auf jedenfall noch verändert - aktuell gibt es eine Liste welcher Verbrauch Stundengenau vorlag
allerdings geht das nur 2 Tage in die Vergangenheit (liegt auch an Ostrom/Netzbetreiber datenübertragung)

mir fehlt noch was sinnvolle verarbeitung - denke es wird noch ein € Kostenzähler geben müssen ...
