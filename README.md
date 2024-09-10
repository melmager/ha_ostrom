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
  api_key64: base64key
```
als ergebnis wird ein states erzeugt mit attribute expire, das zur zeit nirgends ausgewertet wird, aus dem Grund 
ist es sinnvoll ein sequence zu erstellen die immer mit get_token startet und im Anschluss die Price Daten abfragt
Siehe Beispiel 
```
{{ states('ostrom.token') }}
```
Die Strompreise können maximal 24 Stunden in der Zukunft abgefragt werden - aller dings erhält man nicht immer 24 ergebnisse
das liegt daran das immer zur Mittagszeit die forecast Preise für den nächsten Tag ausgehandelt werden.
Also Mittags gibt es mehr Daten wie Morgens :-)
```
action: ostrom.get_price
data:
  token: "{{ states('ostrom.token') }}"
  start_offset: -1
  end_offset: 24
  my_zip: "60000"
```
start_offset - Startzeitpunkt = Aktuelle Stunde + start_offset 
-1 damit man noch den Preis von vergangener Stunde hat und damit die Möglichkeit hat mit dem Stromverbrauch der letzten 
Stunde die Kosten zu berrechnen

end_offset: wie weit in die Zukunft - max 24 Stunden - ergebinsmenge abhängig von der Abfrage Uhrzeit (siehe Erklärung oben)
my_zip: deine Postleitzahl, ist zwingend sonst keine Preisdaten !
```
{{ states('ostrom.price') }}
```

Die Raw Daten von Ostom werden drastisch gekürzt da es eine maximal Grosse gibt von 255 zeichen für den erzeugten state
Ergebnis ist eine List und jeder Wert ist eine addition von grossKwhPrice + grossKwhTaxAndLevies
Sprich Brutto
Strompreis plus Brutto Steuern und Netzabgabe
Ergebniss:
```
[29.68, 27.9, 23.14, 17.14, 16.01, 16.0, 15.99, 16.0, 16.03, 18.6, 25.57, 27.06, 25.91, 25.77, 25.12, 23.67]
```

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
