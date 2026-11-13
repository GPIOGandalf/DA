# TdoT-Demo Spulenteststand – Kurzanleitung

Der umgebaute 3D-Drucker (CR-10 Max) fährt im Dauerlauf ein Messraster ab und „misst“ an jedem Punkt.
Der Hall-Sensor ist montiert, aber **nicht angeschlossen**. Die angezeigten Werte sind **erfunden** (Demo).

## Einmalig: Laptop vorbereiten
1. Python 3 muss installiert sein. Dann im Ordner `C:\tdot-demo` die Datei **`installieren.bat`** doppelklicken (installiert `paramiko`).
2. **Statische IP am LAN-Adapter** setzen. Der Pi hängt direkt per LAN-Kabel am Laptop und hat die feste IP `192.168.10.2`.
   - Windows-Taste → „Netzwerkverbindungen anzeigen“ → **Ethernet** (LAN-Adapter) → Rechtsklick → *Eigenschaften*
   - *Internetprotokoll, Version 4 (TCP/IPv4)* → *Eigenschaften* → **Folgende IP-Adresse verwenden**
   - IP-Adresse: `192.168.10.4` · Subnetzmaske: `255.255.255.0` · Gateway: leer lassen → OK
3. Test: Eingabeaufforderung öffnen → `ping 192.168.10.2` → es muss „Antwort von 192.168.10.2“ kommen.

## Einschalten
1. Drucker und Raspberry Pi einschalten, ca. 1 Minute warten.
2. LAN-Kabel Pi ↔ Laptop stecken. Das USB-Kabel vom Drucker zum Pi muss stecken.
3. **`demo_starten.bat`** doppelklicken.

## Bedienung
1. **Verbinden**: IP `192.168.10.2`, Benutzer `piben`, Passwort eingeben (bekommen Sie von Benedikt, steht nicht hier).
   Oben erscheint dann „Düse: X… Y… Z…“.
2. **Ecken anfahren**: Mit **Z+** zuerst nach oben, bis der Messarm sicher über allem ist. Dann mit X±/Y± zur ersten Ecke fahren und **Ecke 1 übernehmen** drücken.
   Danach zur gegenüberliegenden Ecke fahren und **Ecke 2 übernehmen**. Zum Anfahren lieber 10 mm Schritte nehmen, kurz vor dem Ziel 1 mm.
3. **▶ DEMO STARTEN**: Der Drucker fährt das Rechteck in der Höhe der höheren Ecke ab, so lange, bis Sie stoppen.
4. **⏹ STOPP**: Die Düse fährt 10 mm hoch und das Programm am Pi endet. Zum Weitermachen wieder **Verbinden** drücken, dann gleich **DEMO STARTEN**. Die Ecken bleiben gespeichert.

## Wichtig
- Es gibt **keine Referenzfahrt** (Home). Bitte auch nicht am Drucker-Display „Home“ drücken, sonst fährt der Messarm ins Bett.
- Wurde der Drucker aus- und eingeschaltet, sind die Ecken ungültig. Dann die Ecken bitte neu anfahren.
- **Notfall:** Drucker am Netzschalter ausschalten.

## Wenn etwas nicht geht
| Problem | Lösung |
|---|---|
| „FEHLER Verbindung: timed out“ | LAN-Kabel steckt? Statische IP gesetzt (Schritt 2)? `ping 192.168.10.2` testen. |
| „Authentication failed“ | Passwort prüfen |
| „Kein Drucker-Port gefunden“ | USB-Kabel Drucker ↔ Pi prüfen, Drucker eingeschaltet? |
| Drucker fährt nicht in eine Richtung | Am mechanischen Ende angekommen, in die andere Richtung fahren. |

Bei Fragen: Benedikt Klein
