"""Feste Inhalte aus dem Materialpool-Vault.

Die IDs (P1-P10, K1-K9) sind die Schnittstelle zur KI und zur Wissensbasis.
Bei Aenderungen am Vault muessen sie stabil bleiben.
"""

TECHNIKEN = {
    'anders deuten': {
        'emoji': '🔄',
        'leitfrage': 'Kann man dieselbe Information auch anders verstehen?',
        'erklaerung': (
            'Du nimmst dieselbe Tatsache und zeigst, dass man sie auch anders '
            'verstehen kann. Du bestreitest das Argument nicht – du drehst die '
            'Bedeutung.'
        ),
        'beispiel': (
            'Ein Quorum schützt vor kleinen aktiven Gruppen – man kann es aber '
            'auch so deuten, dass es eine Mehrheit der Abstimmenden ausbremst.'
        ),
    },
    'einschraenken': {
        'emoji': '✂️',
        'leitfrage': 'Wann stimmt das Argument – und wann nicht?',
        'erklaerung': (
            'Du gibst zu, dass das Argument stimmt – aber nur unter bestimmten '
            'Bedingungen. Du nennst die Grenze.'
        ),
        'beispiel': 'Debatten können Wissen erhöhen, aber nicht bei allen gleich.',
    },
    'entkraeften': {
        'emoji': '🎯',
        'leitfrage': 'Warum überzeugt das Argument nicht vollständig?',
        'erklaerung': (
            'Du zeigst eine echte Schwachstelle: Der Beleg passt nicht, die '
            'Begründung trägt nicht, oder die Folgerung stimmt so nicht. '
            'Widersprechen allein reicht nicht.'
        ),
        'beispiel': 'Transparenz zeigt viel Geld, beseitigt seinen Einfluss aber nicht.',
    },
    'gewichten': {
        'emoji': '⚖️',
        'leitfrage': 'Welches Argument ist nach einem Kriterium wichtiger?',
        'erklaerung': (
            'Du erkennst das Argument an – und stellst ein anderes daneben, das '
            'nach einem Kriterium schwerer wiegt. Beide Seiten kommen vor.'
        ),
        'beispiel': (
            'Mehr Beteiligung ist wichtig – aber eine gut durchdachte '
            'Entscheidung wiegt hier schwerer.'
        ),
    },
}

# Anzeigename -> interner Schluessel (Umlaute nur in der Anzeige)
TECHNIK_LABEL = {
    'Anders deuten': 'anders deuten',
    'Einschränken': 'einschraenken',
    'Entkräften': 'entkraeften',
    'Gewichten': 'gewichten',
}
TECHNIK_ANZEIGE = {v: k for k, v in TECHNIK_LABEL.items()}

ROLLEN = {
    'ohne Rolle': [],
    'AfD': ['Partizipation', 'Responsivität'],
    'Mehr Demokratie e. V.': ['Öffentlichkeit', 'Transparenz'],
    'CDU': ['Entscheidungsqualität', 'Regierungsfähigkeit'],
    'Sozialverband': ['Politische Gleichheit', 'Gemeinwohlorientierung'],
    'Moderationsteam': [],
}

VAULT = 'https://publish.obsidian.md/volksentscheide-recherche/'


def vault_url(pfad: str) -> str:
    """Vollstaendige Adresse einer Seite im veroeffentlichten Materialpool.

    Geprueft 2026-09-14: Einzelseiten funktionieren, ORDNER nicht -
    .../02_ARGUMENTE gibt "This page does not exist". Als Sammeleinstieg
    dient deshalb 00_START/00_LEITFRAGE.
    """
    return VAULT + pfad


# Feste Einstiegsseiten im Materialpool
POOL_SEITEN = {
    'techniken': ('Die vier Techniken', '03_BEZUEGE/Argumente_kontern'),
    'kriterien': ('Alle Kriterien und Argumente', '00_START/00_LEITFRAGE'),
    'ausgestaltung': ('Bessere Regeln als Erwiderung',
                      '03_BEZUEGE/Auf_die_Ausgestaltung_kommt_es_an'),
    'gutes_argument': ('Was ist ein gutes Argument?',
                       '00_START/01_WAS_IST_EIN_GUTES_ARGUMENT'),
}

# Kriterienname -> Dateiname im Vault (Umlaute dort umschrieben)
KRITERIEN_PFAD = {
    'Partizipation': '01_KRITERIEN/Partizipation',
    'Politische Gleichheit': '01_KRITERIEN/Politische_Gleichheit',
    'Transparenz': '01_KRITERIEN/Transparenz',
    'Responsivität': '01_KRITERIEN/Responsivitaet',
    'Öffentlichkeit': '01_KRITERIEN/Oeffentlichkeit',
    'Politischer Wettbewerb': '01_KRITERIEN/Politischer_Wettbewerb',
    'Entscheidungsqualität': '01_KRITERIEN/Entscheidungsqualitaet',
    'Problemlösungsfähigkeit': '01_KRITERIEN/Problemloesungsfaehigkeit',
    'Regierungsfähigkeit': '01_KRITERIEN/Regierungsfaehigkeit',
    'Umsetzbarkeit': '01_KRITERIEN/Umsetzbarkeit',
    'Gemeinwohlorientierung': '01_KRITERIEN/Gemeinwohlorientierung',
}

# Die 19 Argumente. "pfad" = Seite im Materialpool, "gegen" = Gegenstrang
# (eine Argument-ID, oder ein Vault-Pfad, wo es kein Pool-Argument gibt).
ARGUMENTE = [
    {'id': 'P1', 'seite': 'pro', 'titel': 'Mehr direkte Mitentscheidung',
     'behauptung': 'Bundesweite Volksentscheide stärken die Beteiligung.',
     'begruendung': 'Bürger wählen dann nicht nur Parteien. Sie entscheiden auch '
                    'selbst über konkrete Sachfragen und haben zwischen Wahlen '
                    'direkten Einfluss.',
     'pfad': '02_ARGUMENTE/PRO_Mehr_direkte_Mitentscheidung', 'gegen': 'K8'},
    {'id': 'P2', 'seite': 'pro', 'titel': 'Mitentscheidung kann Akzeptanz stärken',
     'behauptung': 'Wer mitentscheiden kann, akzeptiert politische Entscheidungen eher.',
     'begruendung': 'Ein faires Verfahren zeigt: Meine Stimme wurde gezählt. Das '
                    'kann auch dann wichtig sein, wenn die eigene Seite verliert.',
     'pfad': '02_ARGUMENTE/PRO_Akzeptanz_und_Vertrauen', 'gegen': 'K7'},
    {'id': 'P3', 'seite': 'pro', 'titel': 'Volksentscheide fördern öffentliche Debatten',
     'behauptung': 'Vor Volksentscheiden wird öffentlich über Sachfragen gesprochen.',
     'begruendung': 'Initiativen, Parteien, Medien und Bürger erklären ihre '
                    'Position. Eine konkrete Abstimmungsfrage schafft Aufmerksamkeit.',
     'pfad': '02_ARGUMENTE/PRO_Oeffentliche_Debatte', 'gegen': 'K9'},
    {'id': 'P4', 'seite': 'pro', 'titel': 'Klare Informationen und Regeln sind möglich',
     'behauptung': 'Volksentscheide können transparent und fair gestaltet werden.',
     'begruendung': 'Der Staat kann die Frage prüfen, Pro und Kontra erklären und '
                    'Kampagnengelder offenlegen.',
     'pfad': '02_ARGUMENTE/PRO_Klare_Information_und_Regeln', 'gegen': 'K3'},
    {'id': 'P5', 'seite': 'pro', 'titel': 'Bürger können eigene Fehler korrigieren',
     'behauptung': 'Direkte Demokratie kann eigene Entscheidungen später wieder korrigieren.',
     'begruendung': 'Wenn Bürger selbst abstimmen dürfen, können sie eine frühere '
                    'Entscheidung mit einer neuen Abstimmung ändern.',
     'pfad': '02_ARGUMENTE/PRO_Fehler_koennen_korrigiert_werden', 'gegen': 'K4'},
    {'id': 'P6', 'seite': 'pro', 'titel': 'Bürgerinteressen kommen auf die Agenda',
     'behauptung': 'Volksinitiativen zwingen Politik, Bürgerinteressen ernst zu nehmen.',
     'begruendung': 'Mit genügend Unterschriften können Bürger ein Thema auf die '
                    'Tagesordnung bringen. Parlament und Regierung müssen darauf reagieren.',
     'pfad': '02_ARGUMENTE/PRO_Buergerinteressen_auf_die_Agenda', 'gegen': 'K3'},
    {'id': 'P7', 'seite': 'pro', 'titel': 'Bürger können das Parlament kontrollieren',
     'behauptung': 'Ein Referendum gibt Bürgern ein wirksames Veto.',
     'begruendung': 'Bürger könnten ein beschlossenes Gesetz stoppen. Regierung und '
                    'Parlament müssten deshalb früher erklären und Kompromisse suchen.',
     'pfad': '02_ARGUMENTE/PRO_Parlament_kontrollieren', 'gegen': 'K1'},
    {'id': 'P8', 'seite': 'pro', 'titel': 'Die Drohung einer Abstimmung fördert Kompromisse',
     'behauptung': 'Direkte Demokratie kann Parlamente zu früheren Kompromissen bewegen.',
     'begruendung': 'Wenn Bürger ein Gesetz später stoppen können, bezieht das '
                    'Parlament betroffene Gruppen eher vorher ein.',
     'pfad': '02_ARGUMENTE/PRO_Kompromisse_vor_der_Abstimmung', 'gegen': 'K1'},
    {'id': 'P9', 'seite': 'pro', 'titel': 'Mehr echte Alternativen im Wettbewerb',
     'behauptung': 'Volksentscheide geben einzelnen Vorschlägen eine faire Chance.',
     'begruendung': 'Parteien bündeln viele Themen zu einem Programm. Eine '
                    'Volksinitiative löst eine einzelne Sachfrage heraus – auch ohne '
                    'große Partei dahinter.',
     'pfad': '02_ARGUMENTE/PRO_Mehr_Alternativen_im_Wettbewerb', 'gegen': 'K3'},
    {'id': 'P10', 'seite': 'pro', 'titel': 'Die Agenda wird etwas gleichberechtigter',
     'behauptung': 'Volksinitiativen können Themen mittlerer Gruppen besser aufgreifen.',
     'begruendung': 'Parlamente reagieren oft stärker auf gut vernetzte und '
                    'wohlhabende Gruppen. Eine Initiative eröffnet einen zusätzlichen Weg.',
     'pfad': '02_ARGUMENTE/PRO_Agenda_etwas_gleichberechtigter', 'gegen': 'K8'},

    {'id': 'K1', 'seite': 'kontra', 'titel': 'Häufige Vetos können Politik blockieren',
     'behauptung': 'Viele Referenden können Regieren langsamer und unsicherer machen.',
     'begruendung': 'Beschlossene Gesetze könnten wieder gestoppt werden. Regierung '
                    'und Parlament planen dann weniger sicher.',
     'pfad': '02_ARGUMENTE/KONTRA_Blockaden_und_Unsicherheit', 'gegen': 'P8'},
    {'id': 'K2', 'seite': 'kontra', 'titel': 'Volksentscheide können Demagogen nützen',
     'behauptung': 'Laute Stimmungsmacher und einfache Parolen können zu viel Einfluss bekommen.',
     'begruendung': 'Emotionale Kampagnen wirken vor großem Publikum stark. Eine '
                    'ruhige, sachliche Abwägung tritt dann leicht zurück.',
     'pfad': '02_ARGUMENTE/KONTRA_Demagogen_und_Manipulation', 'gegen': 'P4'},
    {'id': 'K3', 'seite': 'kontra', 'titel': 'Geld beeinflusst Abstimmungskampagnen',
     'behauptung': 'Finanzstarke Gruppen können die öffentliche Debatte dominieren.',
     'begruendung': 'Teure Werbung erreicht viele Menschen. Schwächere Gruppen '
                    'können ihre Gründe weniger sichtbar machen.',
     'pfad': '02_ARGUMENTE/KONTRA_Geld_beeinflusst_Kampagnen', 'gegen': 'P4'},
    {'id': 'K4', 'seite': 'kontra', 'titel': 'Komplexe Fragen werden auf Ja oder Nein verkürzt',
     'behauptung': 'Eine Ja-Nein-Abstimmung kann schwierige Probleme zu stark vereinfachen.',
     'begruendung': 'Im Parlament kann ein Entwurf beraten und verändert werden. Auf '
                    'dem Stimmzettel gibt es nur Zustimmung oder Ablehnung.',
     'pfad': '02_ARGUMENTE/KONTRA_Komplexe_Fragen_werden_vereinfacht', 'gegen': 'P4'},
    {'id': 'K5', 'seite': 'kontra', 'titel': 'Mehrheiten können Minderheiten überstimmen',
     'behauptung': 'Volksentscheide können Interessen von Minderheiten gefährden.',
     'begruendung': 'Eine Mehrheit entscheidet auch über Fragen, die vor allem eine '
                    'kleine Gruppe betreffen. Die Mehrheit spürt die Nachteile '
                    'vielleicht nicht selbst.',
     'pfad': '02_ARGUMENTE/KONTRA_Minderheiten_koennen_verlieren',
     'gegen': '05_KONTEXT/Schutzregeln_fuer_faire_Abstimmungen'},
    {'id': 'K6', 'seite': 'kontra', 'titel': 'Ein Ergebnis löst die Umsetzung nicht',
     'behauptung': 'Ein erfolgreiches Votum ist noch keine umsetzbare Lösung.',
     'begruendung': 'Nach der Abstimmung bleiben Rechtsfragen, Kosten und '
                    'Zuständigkeiten. Eine einfache Forderung kann viele schwierige '
                    'Entscheidungen auslösen.',
     'pfad': '02_ARGUMENTE/KONTRA_Umsetzung_bleibt_kompliziert', 'gegen': 'P6'},
    {'id': 'K7', 'seite': 'kontra', 'titel': 'Vertrauen wächst nicht automatisch',
     'behauptung': 'Volksentscheide lösen Unzufriedenheit mit Demokratie nicht automatisch.',
     'begruendung': 'Vertrauen hängt auch von fairen Ergebnissen und glaubwürdiger '
                    'Politik ab. Wer oft verliert, kann sogar enttäuschter werden.',
     'pfad': '02_ARGUMENTE/KONTRA_Vertrauen_waechst_nicht_automatisch', 'gegen': 'P2'},
    {'id': 'K8', 'seite': 'kontra', 'titel': 'Vor allem Bessergestellte stimmen ab',
     'behauptung': 'Häufige Abstimmungen können politische Ungleichheit vergrößern.',
     'begruendung': 'Menschen mit mehr Bildung, Zeit und politischem Interesse '
                    'beteiligen sich häufiger. Gleiche Stimmzettel führen dann nicht '
                    'zu gleichem Einfluss.',
     'pfad': '02_ARGUMENTE/KONTRA_Vor_allem_Bessergestellte_stimmen_ab', 'gegen': 'P1'},
    {'id': 'K9', 'seite': 'kontra', 'titel': 'Wissen und Information sind ungleich verteilt',
     'behauptung': 'Nicht alle Bürger können komplexe Vorlagen gleich gut prüfen.',
     'begruendung': 'Politische Entscheidungen brauchen Zeit, Fachwissen und '
                    'verständliche Informationen. Die sind ungleich verteilt.',
     'pfad': '02_ARGUMENTE/KONTRA_Wissen_ist_ungleich_verteilt', 'gegen': 'P3'},
]

ARGUMENT_NACH_ID = {a['id']: a for a in ARGUMENTE}


def argument_text(arg_id: str) -> str:
    """Der Wortlaut, der als Ausgangsargument an die KI geht."""
    a = ARGUMENT_NACH_ID[arg_id]
    return f"{a['behauptung']} {a['begruendung']}"


def gegenstrang(arg_id: str):
    """(Beschriftung, Vault-Pfad) des Gegenstrangs - oder None."""
    a = ARGUMENT_NACH_ID.get(arg_id)
    if not a or not a.get('gegen'):
        return None
    gegen = a['gegen']
    if gegen in ARGUMENT_NACH_ID:
        return ARGUMENT_NACH_ID[gegen]['titel'], ARGUMENT_NACH_ID[gegen]['pfad']
    return 'Schutzregeln für faire Abstimmungen', gegen
