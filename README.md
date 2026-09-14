# Diskussionstrainer

Übungs-App zu den vier Konter-Techniken aus dem Politikunterricht (UE „Direkte Demokratie", Block B03). Die Schüler antworten auf ein Argument der Gegenseite und bekommen eine Rückmeldung als drei Ampeln plus höchstens zwei Hinweise.

Einsatz: Selbstlernen zwischen B03 Teil 2 und der Fishbowl-Diskussion in B04, etwa 30 Minuten, auf Schul-iPads.

**Es wird nichts gespeichert.** Keine Namen, keine Serverablage, keine Lehrerübersicht. Die Schülertexte gehen an die OpenAI-API und werden danach verworfen.

---

## Dateien

| Datei | Inhalt |
| --- | --- |
| `app.py` | Oberfläche und Ablaufsteuerung |
| `trainer.py` | die vier KI-Aufrufe mit Systemanweisung und JSON-Schema |
| `argumente.py` | die vier Techniken, die 19 Pool-Argumente, die fünf Rollen |
| `glossar.py` | 65 erklärte Wörter; die App markiert sie automatisch in jedem Text |
| `wissensbasis.md` | verdichteter Materialpool, geht in jeden KI-Aufruf |
| `requirements.txt` | Streamlit und das OpenAI-SDK |
| `.streamlit/secrets.toml.example` | Vorlage für die Einstellungen |

---

## Einrichten

1. Repository auf GitHub anlegen und die Dateien hochladen.

   `app.py`, `trainer.py`, `argumente.py`, `glossar.py`, `wissensbasis.md`, `requirements.txt`, `README.md` und `.gitignore` lassen sich per Drag-and-drop hochladen.

   Für den Ordner `.streamlit` geht das nicht: **Add file → Create new file**, als Dateinamen `.streamlit/config.toml` eintippen — der Schrägstrich legt den Ordner mit an — Inhalt einfügen, **Commit**. Dasselbe für `.streamlit/secrets.toml.example`.

   Die Datei `secrets.toml` selbst gehört **nicht** ins Repository. Nur die `.example`-Vorlage; die echten Werte werden in Streamlit eingetragen.
2. Auf `share.streamlit.io` eine App aus dem Repository erstellen, Hauptdatei `app.py`.
3. Unter **Settings → Secrets** eintragen:

```toml
OPENAI_API_KEY = "sk-..."
KLASSENCODE = "volksentscheid"
FREIGABE_START = "2026-09-15"
FREIGABE_ENDE = "2026-09-17"
```

4. Im OpenAI-Konto ein niedriges Ausgabelimit setzen. Das ist die einzige Bremse, die auch bei einem Fehler in der App greift.
5. Die entstandene Adresse selbst einmal durchklicken, dann an die Klasse geben.

---

## Einstellungen

**Freigabefenster.** `FREIGABE_START` und `FREIGABE_ENDE` im Format `JJJJ-MM-TT`. Außerhalb des Fensters zeigt die App einen Hinweis und stellt keine Anfragen. Beide Zeilen sind optional. Zum Ändern die Secrets in der Streamlit-Oberfläche bearbeiten; die App startet danach von selbst neu.

**Klassencode.** `KLASSENCODE` steht auf der Rollenkarte. Zeile entfernen = jeder mit dem Link kommt hinein.

**Limits.** Oben in `app.py`:

```python
SITZUNGSLIMIT = 16   # KI-Antworten pro Schülersitzung (Feedback + Hilfe)
TAGESGRENZE  = 400   # KI-Antworten pro Tag für die gesamte App
```

**Modell.** Oben in `trainer.py`: `MODELL = 'gpt-5.6-luna'`. Reicht die Qualität nicht, hier auf `gpt-5.6-terra` wechseln — das kostet etwa das Zehnfache, bei 20 Schülern immer noch wenige Euro.

---

## Zwei Hilfen für schwächere Schüler

**Gestufte Hilfe vor dem Schreiben.** Wer nicht weiterkommt, klickt auf „Ich brauche einen Tipp" und bekommt einen Denkanstoß — wo die Technik an diesem Argument greift, als Frage formuliert, ohne fertigen Satz. Erst ein zweiter Klick („Ich komme immer noch nicht weiter") liefert eine ausformulierte Erwiderung, verbunden mit der Aufforderung, dasselbe in eigenen Worten zu schreiben. Dieselbe Logik wie die Hilfekarten in B03 Teil 1: Differenzierung auf Abruf, nicht auf Vorrat.

Die App merkt sich, welche Stufe geholt wurde, und gibt das an die Rückmeldung weiter. Wer die Formulierung fast wortgleich abschreibt, wird freundlich darauf hingewiesen — ohne Abwertung.

**Verbesserungsvorschläge nach der Rückmeldung.** Unter den Ampeln steht „So machst du es besser" mit ein bis zwei konkreten Vorschlägen: was zu ergänzen ist und grob mit welchem Inhalt, wo möglich aus der Wissensbasis. Dazu eine **Formulierungshilfe** — ein angefangener Satz, zugeschnitten auf genau diese Antwort, den der Schüler selbst zu Ende schreibt.

Die Abstufung bleibt dabei erhalten: Vorschlag → angefangener Satz → gestufte Hilfe → Musterantwort. Eine vollständige Musterantwort gibt es weiterhin erst nach dem eigenen Überarbeitungsversuch.

---

## Glossar zum Antippen

Wörter, die die Lerngruppe vermutlich nicht kennt, sind in allen KI-Texten **automatisch markiert**: blau, gepunktet unterstrichen, mit einem kleinen Fragezeichen. Ein Tipp darauf klappt eine kurze Erklärung auf, ein zweiter schließt sie wieder. Das ist natives HTML (`<details>`), kein JavaScript — funktioniert auf dem iPad ohne Hover und ohne Umwege.

Die Liste in `glossar.py` setzt **bewusst niedriger an als das Glossar im Materialpool**: Dort steht „Quorum", aber nicht „Votum", „Vorlage" oder „Frist". Genau solche Wörter kosten eine leseschwache Lerngruppe den Anschluss.

**Ergänzen ist einfach.** In `glossar.py` eine Zeile in das `GLOSSAR`-Wörterbuch eintragen:

```python
'Legislaturperiode': 'Die Zeit, für die ein Parlament gewählt ist. In Deutschland vier Jahre.',
```

Mehr ist nicht nötig — die App findet das Wort danach in jedem Text von selbst, auch in gebeugten Formen wie „Fristen" oder „Argumente". Unregelmäßige Mehrzahlen (Kriterium → Kriterien, Quorum → Quoren) stehen im `ALIASE`-Wörterbuch darunter.

Zwei Regeln für die Erklärungen: ein bis zwei kurze Sätze, und **kein Fachwort in der Erklärung**, das selbst wieder erklärt werden müsste. Jeder Begriff wird pro Textblock nur beim ersten Vorkommen markiert.

**Nach einer Änderung an `glossar.py` die App rebooten** (siehe unten).

---

## Verweise in den Materialpool

An zwei Stellen kann der Schüler direkt im veröffentlichten Materialpool nachschlagen: im Schreibschritt unter dem Eingabefeld und noch einmal unter der Rückmeldung. Der Bereich heißt „Im Materialpool nachschlagen" und ist zugeklappt, damit er nicht ablenkt.

Darin stehen, sofern das Ausgangsargument aus dem Pool stammt:

- **Dieses Argument im Materialpool** — die vollständige Seite mit Beleg und Gegenstrang
- **Was die Gegenseite sagt** — die Seite des Gegenstrangs, automatisch passend zum gewählten Argument

Dazu immer: die vier Techniken, alle Kriterien und Argumente, und die Ausgestaltungsseite. Hat die KI ein Kriterium erkannt, erscheint außerdem ein direkter Verweis darauf.

**Alle Verweise öffnen einen neuen Tab** (`target="_blank"`). Das ist keine Kosmetik: Streamlit hält den Sitzungszustand nur im geöffneten Tab. Würde der Link die Seite ersetzen, wäre beim Zurückgehen die halbfertige Erwiderung verloren.

**Zwei Dinge zum Wissen:**

Auf den Argumentseiten des Vaults steht die **Erwiderungsidee im Klartext**. Wer während des Schreibens dorthin klickt, findet dort eine mögliche Lösung. Das ist eine bewusste Entscheidung — der Materialpool ist das Rechercheinstrument der Einheit, und Nachschlagen ist selbst eine Kompetenz. Soll das enger geführt werden, lassen sich die beiden argumentbezogenen Verweise in `materialpool_block()` an `st.session_state.fb` koppeln, also erst nach dem ersten Feedback zeigen.

**Ordner-Adressen funktionieren nicht.** `…/02_ARGUMENTE` gibt „This page does not exist" — Obsidian Publish liefert nur einzelne Notizen aus. Als Sammeleinstieg dient deshalb `00_START/00_LEITFRAGE`, wo alle Kriterien mit ihren Argumenten verlinkt sind.

Die Pfade stehen in `argumente.py`: `pfad` und `gegen` je Argument, dazu `KRITERIEN_PFAD` und `POOL_SEITEN`. Ändern sich Dateinamen im Vault, müssen sie hier nachgezogen werden.

---

## Was die App kostet

Pro Aufruf gehen rund 10.100 Tokens konstante Vorlage hinein (Anweisung plus Wissensbasis), dazu etwa 200 Tokens Schülertext; heraus kommen 400 bis 1.000 Tokens. Bei 20 Schülern und höchstens 16 Rückmeldungen je Sitzung liegt das Ganze mit GPT-5.6 Luna zwischen etwa 0,10 und 0,75 Euro für die Klasse. Klassencode und Limits sind deshalb Missbrauchsschutz, keine Kostenbremse.

---

## Nach jeder Änderung an einem Modul: Reboot

Streamlit Community Cloud zieht Änderungen aus GitHub automatisch nach, führt dabei aber nur `app.py` neu aus. **Importierte Module — `trainer.py`, `argumente.py` — bleiben in ihrer alten Fassung im Speicher.** Die App läuft dann mit einer Mischung aus alt und neu und wirft Fehler, die in die Irre führen (etwa `module 'trainer' has no attribute ...`).

Deshalb: Wurde etwas anderes als `app.py` geändert — also `trainer.py`, `argumente.py` oder `glossar.py` —, in der App unten rechts auf **Manage app** → Drei-Punkte-Menü → **Reboot app**. Dauert etwa eine Minute.

---

## Zwei bekannte Grenzen

**Die Tagesgrenze überlebt keinen Neustart.** Streamlit Community Cloud startet den Container bei Inaktivität neu, danach zählt die App wieder bei null. Als Bremse gegen einen durchgedrehten Link reicht das; eine verlässliche Abrechnung ist es nicht. Dafür bräuchte es einen externen Speicher.

**Der Zustand hängt am Browser.** Jeder Schüler hat seine eigene Sitzung — genau so soll es sein. Wer die Seite neu lädt, beginnt aber von vorn. Deshalb liegt das Ergebnis am Ende zum Kopieren bereit und wird sofort auf die Rollenkarte übertragen.

---

## Fachliche Grundlage

Alles Fachliche stammt aus dem Materialpool-Vault „Volksentscheide – Diskussionsvorbereitung", veröffentlicht unter <https://publish.obsidian.md/volksentscheide-recherche/00_START/00_LEITFRAGE>. `wissensbasis.md` ist ein verdichteter Auszug daraus: die vier Bausteine eines guten Arguments, die elf Kriterien, die vier Techniken im Vault-Wortlaut, 19 Argumente mit Gegenstrang und Erwiderungsidee, 17 Belege und ein Glossar.

Die KI behandelt **nur** die Belege aus Abschnitt 7 der Wissensbasis als belegt. Alles andere, was wie ein Beleg klingt, wird als ungeprüft markiert und der Schüler nach der Quelle gefragt.

**Wenn sich der Vault ändert, muss `wissensbasis.md` nachgezogen werden.** Die IDs `P1`–`P10`, `K1`–`K9` und `B-…` sind die Schnittstelle zwischen App, Wissensbasis und KI und sollten stabil bleiben.
