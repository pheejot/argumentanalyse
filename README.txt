DISKUSSIONS-ANALYSATOR - WEB-VERSION

Auf Handy und Lehrer-PC ist keine Python-Installation erforderlich.
Die Anwendung wird einmalig auf einem Webserver bereitgestellt.

EMPFOHLENE BEREITSTELLUNG: STREAMLIT COMMUNITY CLOUD
1. Einen GitHub-Account und ein neues Repository anlegen.
2. app.py und requirements.txt aus diesem Ordner hochladen.
3. Streamlit Community Cloud öffnen und "Create app" wählen.
4. Repository und app.py auswählen.
5. Unter den App-Secrets eintragen:
   OPENAI_API_KEY = "DEIN_API_KEY"
6. Deploy starten.
7. Danach die erzeugte HTTPS-Webadresse auf PC oder Handy öffnen.

HANDY ALS MIKROFON
Die HTTPS-Webadresse auf dem Handy öffnen und dem Browser Mikrofonzugriff erlauben.
Im Modus "Live-Mikrofon" kurze Diskussionsabschnitte aufnehmen und jeweils
"Abschnitt live auswerten" drücken.

WICHTIG ZUM AKTUELLEN PROTOTYP
Die Streamlit-Sitzung ist browserbezogen. Eine echte gemeinsame Sitzung, bei der
Handy und Beamer gleichzeitig dieselbe laufende Ansicht teilen, benötigt noch
einen serverseitigen gemeinsamen Sitzungsspeicher. Die Web-App selbst funktioniert
aber ohne lokale Python-Installation und kann auf jedem Gerät über HTTPS genutzt werden.
