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
