"""Glossar fuer die Schuelerinnen und Schueler.

Setzt bewusst NIEDRIGER an als das Glossar im Materialpool-Vault: auch Woerter
wie "Votum", "Vorlage" oder "Frist" sind erklaert, nicht nur die Fachbegriffe
der Demokratietheorie. Das Vorwissen der Lerngruppe ist gering.

Regeln fuer die Erklaerungen:
- ein bis zwei kurze Saetze
- keine Fachwoerter in der Erklaerung, die selbst wieder erklaert werden muessten
- konkret statt abstrakt

Die App markiert diese Woerter automatisch in jedem KI-Text. Es muss also
nichts von Hand ausgezeichnet werden - Liste ergaenzen genuegt.
"""

import re

GLOSSAR = {
    # --- Abstimmen und Verfahren ---
    'Votum': 'Das Ergebnis einer Abstimmung. Also das, was herauskommt, wenn alle abgestimmt haben.',
    'Vorlage': 'Der Text, über den abgestimmt wird. Zum Beispiel ein Gesetz, zu dem man Ja oder Nein sagen kann.',
    'Abstimmung': 'Alle sagen Ja oder Nein zu einer Frage. Danach werden die Stimmen gezählt.',
    'Volksentscheid': 'Alle Wahlberechtigten stimmen selbst über eine Sachfrage ab.',
    'Volksbegehren': 'Bürger sammeln Unterschriften, um eine Volksabstimmung zu verlangen.',
    'Volksinitiative': 'Bürger bringen mit genügend Unterschriften einen eigenen Vorschlag auf die Tagesordnung.',
    'Referendum': 'Eine Abstimmung über etwas, das schon beschlossen wurde.',
    'Fakultatives Referendum': 'Eine Abstimmung, die nur stattfindet, wenn genug Bürger sie verlangen.',
    'Obligatorisches Referendum': 'Eine Abstimmung, die bei bestimmten wichtigen Fragen immer stattfinden muss.',
    'Quorum': 'Eine Mindestzahl. Zum Beispiel: So viele müssen mindestens zustimmen, sonst gilt das Ergebnis nicht.',
    'Frist': 'Eine feste Zeit, in der etwas passieren muss. Danach ist es zu spät.',
    'Stimmzettel': 'Das Blatt, auf dem man sein Kreuz macht.',
    'Wahlberechtigte': 'Alle Menschen, die wählen oder abstimmen dürfen.',
    'Beteiligung': 'Wie viele Menschen mitmachen. Zum Beispiel: wie viele wirklich abstimmen gehen.',
    'verbindlich': 'Man muss sich daran halten. Es ist kein Vorschlag, sondern eine Pflicht.',
    'Verfahren': 'Der festgelegte Weg, wie etwas abläuft. Wer darf wann was machen.',
    'Instrument': 'Ein Mittel oder Werkzeug. Hier: eine bestimmte Art, abstimmen zu lassen.',
    'Ausgestaltung': 'Wie genau etwas geregelt wird. Welche Regeln also gelten.',
    'Umsetzung': 'Wenn eine Entscheidung wirklich gemacht wird – mit Geld, Personal und Regeln.',

    # --- Staat und Politik ---
    'Parlament': 'Die gewählten Abgeordneten, die zusammen Gesetze beschließen. In Deutschland der Bundestag.',
    'Bundestag': 'Das Parlament für ganz Deutschland. Die Abgeordneten werden gewählt.',
    'Bundesrat': 'Hier reden die Bundesländer bei Gesetzen mit.',
    'Abgeordnete': 'Gewählte Personen, die im Parlament für andere entscheiden.',
    'Gesetzentwurf': 'Ein fertig geschriebener Vorschlag für ein neues Gesetz. Noch nicht beschlossen.',
    'Bundesebene': 'Ganz Deutschland zusammen – nicht nur ein Bundesland oder eine Stadt.',
    'Grundgesetz': 'Die Verfassung von Deutschland. Dort stehen die wichtigsten Regeln.',
    'Verfassung': 'Das wichtigste Regelwerk eines Staates. Alle anderen Gesetze müssen dazu passen.',
    'Grundrechte': 'Rechte, die jeder Mensch hat, zum Beispiel die Meinungsfreiheit. Auch eine Mehrheit darf sie nicht abschaffen.',
    'Freies Mandat': 'Abgeordnete entscheiden nach ihrem Gewissen. Niemand darf ihnen vorschreiben, wie sie abstimmen.',
    'Veto': 'Das Recht, etwas zu stoppen.',
    'Initiative': 'Wenn jemand von sich aus etwas anstößt und in Gang bringt.',
    'Kampagne': 'Geplante Werbung für oder gegen eine politische Sache.',
    'Demagoge': 'Jemand, der mit einfachen Parolen und starken Gefühlen Stimmung macht, statt sachlich zu überzeugen.',
    'Kompromiss': 'Eine Lösung, bei der jede Seite etwas bekommt und auf etwas verzichtet.',
    'Mehrheit': 'Die größere Zahl. Wer mehr Stimmen hat, hat die Mehrheit.',
    'Minderheit': 'Eine kleinere Gruppe in der Gesellschaft. Sie kann andere Interessen haben als die Mehrheit.',
    'Direkte Demokratie': 'Die Bürger entscheiden Sachfragen selbst, statt nur Abgeordnete zu wählen.',
    'Repräsentative Demokratie': 'Wir wählen Abgeordnete. Die entscheiden dann für uns.',
    'Konkordanzdemokratie': 'Ein System, in dem die großen Parteien zusammen regieren und früh Kompromisse suchen.',
    'Legitimität': 'Dass eine Entscheidung anerkannt wird, weil sie richtig zustande gekommen ist.',
    'Sachfrage': 'Eine einzelne Frage zu einem Thema – nicht ein ganzes Parteiprogramm.',

    # --- Die elf Kriterien ---
    'Kriterium': 'Der Maßstab, an dem du etwas misst. Woran du festmachst, ob etwas gut oder schlecht ist.',
    'Partizipation': 'Mitmachen können bei politischen Entscheidungen.',
    'Politische Gleichheit': 'Dass alle die gleiche Chance auf Einfluss haben – egal wie viel Geld oder Bildung sie haben.',
    'Transparenz': 'Dass man erkennen kann, wer entscheidet und warum.',
    'Responsivität': 'Dass die Politik auf die Wünsche der Bürger reagiert.',
    'Öffentlichkeit': 'Dass über eine Frage öffentlich gesprochen wird und alle es mitbekommen können.',
    'Politischer Wettbewerb': 'Dass verschiedene Vorschläge eine faire Chance haben, gehört zu werden.',
    'Entscheidungsqualität': 'Wie gut eine Entscheidung durchdacht ist.',
    'Problemlösungsfähigkeit': 'Ob die Politik ein Problem wirklich löst.',
    'Regierungsfähigkeit': 'Ob die Politik noch entscheiden und handeln kann.',
    'Umsetzbarkeit': 'Ob sich eine Entscheidung praktisch machen lässt – rechtlich, finanziell, organisatorisch.',
    'Gemeinwohlorientierung': 'Ob eine Entscheidung allen nützt und nicht nur einer Gruppe.',
    'Gemeinwohl': 'Was allen nützt, nicht nur einer einzelnen Gruppe.',

    # --- Argumentieren ---
    'Argument': 'Eine Aussage mit Begründung. Eine bloße Meinung ist noch kein Argument.',
    'Behauptung': 'Was du sagst oder forderst. Der Kern deiner Aussage.',
    'Begründung': 'Warum deine Behauptung stimmen soll. Das „weil".',
    'Beleg': 'Eine Zahl, eine Studie oder ein Beispiel, das deine Begründung stützt.',
    'Erwiderung': 'Deine Antwort auf ein Argument der Gegenseite.',
    'Gegenargument': 'Ein Argument, das gegen deine Position spricht.',
    'Position': 'Der Standpunkt, den du vertrittst.',
    'Debatte': 'Ein Streitgespräch über eine Frage. Beide Seiten kommen zu Wort.',
    'Sachurteil': 'Eine Feststellung, die man nachprüfen kann.',
    'Werturteil': 'Eine Bewertung. Dafür brauchst du einen Maßstab.',
    'Fishbowl': 'Eine Diskussionsform: Innen sitzen die, die reden. Außen sitzen die, die zuhören und beobachten.',
}

# Unregelmaessige Formen, die die Endungsregel unten nicht erwischt.
# Form -> Eintrag im GLOSSAR.
ALIASE = {
    'Kriterien': 'Kriterium',
    'Quoren': 'Quorum',
    'Voten': 'Votum',
    'Referenden': 'Referendum',
    'Volksbegehren': 'Volksbegehren',
    'Gesetzentwuerfe': 'Gesetzentwurf',
    'Gesetzentwürfe': 'Gesetzentwurf',
    'Vetos': 'Veto',
}

# Endungen, die im Deutschen an einen Begriff treten koennen
_ENDUNGEN = r'(?:en|em|es|er|e|n|s)?'

# Lange Begriffe zuerst, damit "Politische Gleichheit" vor "Gleichheit" greift
_SUCHWOERTER = sorted(set(GLOSSAR) | set(ALIASE), key=len, reverse=True)
_MUSTER = re.compile(
    r'\b(' + '|'.join(re.escape(b) for b in _SUCHWOERTER) + r')' + _ENDUNGEN + r'\b',
    re.IGNORECASE,
)


def _treffer_zu_begriff(gefunden: str) -> str:
    """Das gefundene Wort auf den Glossareintrag zurueckfuehren."""
    klein = gefunden.lower()
    for form, begriff in ALIASE.items():
        if klein == form.lower():
            return begriff
    for begriff in _SUCHWOERTER:
        if klein == begriff.lower() and begriff in GLOSSAR:
            return begriff
    return ''


def markiere(text: str) -> str:
    """Glossarwoerter in einem Text als aufklappbare Erklaerung auszeichnen.

    Jeder Begriff wird nur beim ERSTEN Vorkommen markiert - sonst stehen in
    einem Satz drei gleiche Blasen.
    Gibt HTML zurueck; muss mit unsafe_allow_html gerendert werden.
    """
    if not text:
        return ''
    schon_da = set()

    def ersetze(m):
        begriff = _treffer_zu_begriff(m.group(1))
        if not begriff or begriff in schon_da:
            return m.group(0)
        schon_da.add(begriff)
        return (f'<details class="gl"><summary>{m.group(0)}</summary>'
                f'<span class="gl-text">{GLOSSAR[begriff]}</span></details>')

    return _MUSTER.sub(ersetze, text)


def enthaltene_begriffe(text: str) -> list:
    """Welche Glossarbegriffe kommen in diesem Text vor?"""
    if not text:
        return []
    gefunden, gesehen = [], set()
    for m in _MUSTER.finditer(text):
        begriff = _treffer_zu_begriff(m.group(1))
        if begriff and begriff not in gesehen:
            gesehen.add(begriff)
            gefunden.append(begriff)
    return gefunden
