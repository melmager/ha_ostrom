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

Aus Beiden Angaben getrennt mit einem : wird ein Base64 Login erstellt, den die Software benötigt.

für den Zugriff auf Daten wird ein zugangstoken benötigt, der nur eine gewisse Zeit gültig ist
```
action: ostrom.get_token
data: 
  api_key64: >-
     ihr_base64key_fuer_ostrom_zugang
```
als ergebnis wird ein states erzeugt mit angabe Zeitpunkt expire und einem state.attribute token das bei weiteren abfragen benutzt werden muss
, expire wird derzeit von mir nicht ausgewertet - ist auf der to do liste :-)
es ist sinnvoll ein sequence zu erstellen die immer mit get_token startet und im Anschluss die Price Daten abfragt
in Entwicklung / template
```
Ablauf {{ states('ostrom.token') }}
Zugangstoken {{ state_attr('ostrom.token','token') }}

```
Abfrage der Price daten

  token: muss der token übergeben werden von der Abfrage get_token
  start_offset:0 = startzeitpunkt der abfrage - hier aktuelle Stunde (wird wohl ein fester Wert 0 werden)
  end_offset: 36 = endzeitpunkt - Ergebnismenge ist abhängig vom Abfragezeitpunkt 
  Ostrom liefert immer pricedaten bis 23:00 Uhr (test mit sommerzeit)
  Mittags ab 14:00 Uhr gibt es die Daten für den nächsten Tag (sommerzeit) bis dahin nur aktueller Tag
Also hat man bei Abfrage Morgens nur die Price daten bis 23:00 Uhr des Tages. 


```
- action: ostrom.get_price
        metadata: {}
        data:
          token: "{{ state_attr('ostrom.token','token') }}"
          start_offset: 0
          end_offset: 36
          my_zip: "60000"
```

  my_zip: "ihre postleitzahl" - ist ein muss - ohne gibt es keine preisdaten !
  start_offset: Startzeitpunkt = 0  = Aktuelle Stunde 
  end_offset: wie weit in die Zukunft - max 36 Stunden - ergebinsmenge abhängig von der Abfrage Uhrzeit (siehe Erklärung oben)

```
Aktueller Preis {{ states('ostrom.price') }}
Raw Daten die Ostrom liefert {{ state_attr('ostrom.price','raw') }}
Durchschnitts Preis {{ state_attr('ostrom.price','average') }}
Gekürztes Ergebnis für Datenquelle Apexchart {{ state_attr('ostrom.price','apex') }}
Günstigster Strompreis Zeitpunkt {{ state_attr('ostrom.price','low') }}

```
übermittelter Strompreis ergibt sich aus Brutto Strompreis "grossKwhPrice" plus Brutto Steuern und Netzabgabe "grossKwhTaxAndLevies"

Beispiel Raw Daten von Ostrom für eine Stunde:

```
{ "data": [
    {
      "date": "2023-10-22T01:00:00.000Z",
      "netMwhPrice": 926,
      "netKwhPrice": 92.6,
      "grossKwhPrice": 110.2,
      "netKwhTaxAndLevies": 16.2,
      "grossKwhTaxAndLevies": 19.28,
      "netMonthlyOstromBaseFee": 5.04,
      "grossMonthlyOstromBaseFee": 6,
      "netMonthlyGridFees": 3.84,
      "grossMonthlyGridFees": 4.57
    }
  ]
}
```

Bekannte Bugs, die wegen Beginner Status noch nicht lösen kann

- kein Eintrag im Logfile
- api_key64: !secret base64key !secret ist leider nicht möglich der Key muss noch dem get_token übergeben werden
