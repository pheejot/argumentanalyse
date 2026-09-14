"""Diskussionstrainer - vier Techniken zum Kontern.

Selbstlernangebot zwischen B03 Teil 2 und der Fishbowl in B04.
Ablauf: Rolle -> Technik -> Ausgangsargument -> Erwiderung -> Ampel-Feedback
-> Ueberarbeiten -> Musterantwort -> naechste Uebung oder Abschluss.

Es wird nichts gespeichert. Kein Serverspeicher, keine Lehreruebersicht.
"""

import os
from datetime import date, datetime

import streamlit as st

import trainer
from glossar import markiere
from argumente import (ARGUMENTE, ARGUMENT_NACH_ID, KRITERIEN_PFAD, POOL_SEITEN,
                       ROLLEN, TECHNIKEN, TECHNIK_ANZEIGE, TECHNIK_LABEL,
                       argument_text, gegenstrang, vault_url)

LEITFRAGE = 'Sollten in Deutschland bundesweite Volksentscheide eingeführt werden?'
SITZUNGSLIMIT = 16          # KI-Antworten pro Schuelersitzung (inkl. Hilfe)
TAGESGRENZE = 400           # KI-Antworten pro Tag fuer die gesamte App

st.set_page_config(page_title='Diskussionstrainer', page_icon='🗣️', layout='centered')


# ---------------------------------------------------------------------------
# Darstellung
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 44rem; }
      .stButton > button {
          width: 100%; padding: .95rem 1rem; font-size: 1.12rem;
          font-weight: 600; border-radius: 12px; margin-bottom: .35rem;
      }
      textarea { font-size: 1.1rem !important; line-height: 1.5 !important; }
      .karte {
          border: 1px solid #D9E2F3; background: #F2F5FA; border-radius: 12px;
          padding: .9rem 1.1rem; margin: .6rem 0;
      }
      .karte .label {
          font-size: .78rem; letter-spacing: .06em; text-transform: uppercase;
          color: #5A6B85; margin-bottom: .3rem;
      }
      .karte .inhalt { font-size: 1.05rem; line-height: 1.5; color: #0F2C5C; }
      .ampel {
          display: flex; align-items: center; gap: .7rem;
          padding: .6rem .8rem; border-radius: 10px; margin-bottom: .4rem;
          background: #F7F9FC; border: 1px solid #E3E9F3;
      }
      .punkt { width: 1.15rem; height: 1.15rem; border-radius: 50%; flex: none; }
      .ampel .name { font-weight: 600; min-width: 8.5rem; color: #0F2C5C; }
      .ampel .wert { color: #5A6B85; font-size: .95rem; }
      .schrittzeile { color: #5A6B85; font-size: .85rem; margin-bottom: .2rem; }

      /* Verweise in den Materialpool - sehen aus wie Knoepfe, oeffnen aber
         einen neuen Tab, damit die Trainer-Sitzung erhalten bleibt. */
      a.poollink {
          display: block; text-decoration: none; text-align: left;
          border: 1px solid #4C94D8; background: #FFFFFF; color: #1F4E79;
          border-radius: 10px; padding: .7rem .9rem; margin-bottom: .4rem;
          font-weight: 600; font-size: 1.02rem; line-height: 1.35;
      }
      a.poollink:hover { background: #E3EDF9; }
      a.poollink .extern { float: right; color: #5A6B85; font-weight: 400; }

      /* Glossar: angetipptes Wort klappt eine Erklaerung auf.
         <details> ist ein natives HTML-Element - funktioniert auf dem iPad
         ohne JavaScript und ohne Hover. */
      /* inline-block statt inline: Chrome erzwingt hinter einem <details>
         sonst einen Zeilenumbruch, auch wenn die Zeile noch Platz hat.
         Beim Aufklappen wird daraus ein Block, damit die Erklaerung die
         volle Breite bekommt. */
      details.gl { display: inline-block; vertical-align: baseline; }
      details.gl[open] { display: block; margin: .15rem 0 .1rem 0; }
      details.gl > summary {
          display: inline; cursor: pointer; list-style: none;
          color: #1F4E79; font-weight: 600;
          border-bottom: 2px dotted #4C94D8;
      }
      details.gl > summary::-webkit-details-marker { display: none; }
      details.gl > summary::marker { content: ''; }
      /* kleines Fragezeichen: zeigt, dass man tippen kann */
      details.gl > summary::after {
          content: '?'; font-size: .62em; font-weight: 700;
          vertical-align: super; margin-left: .12em; color: #4C94D8;
      }
      details.gl[open] > summary { background: #E3EDF9; }
      details.gl[open] > summary::after { content: '×'; font-size: .8em;
          vertical-align: baseline; color: #5A6B85; }
      /* Im zugeklappten Zustand darf die Erklaerung KEINEN Platz belegen -
         sonst bricht der Satz an jedem Glossarwort um. */
      .gl-text { display: none; }
      details.gl[open] > .gl-text {
          display: block; margin: .25rem 0 .3rem 1.1rem;
          padding: .45rem .7rem;
          background: #FFFFFF; border-left: 4px solid #4C94D8;
          border-radius: 0 6px 6px 0;
          font-size: .93rem; line-height: 1.4; color: #3A4A63; font-weight: 400;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

FARBE = {'gruen': '#2E7D32', 'gelb': '#F0A202', 'rot': '#C62828'}
WORT = {'gruen': 'passt', 'gelb': 'geht noch besser', 'rot': 'hier ansetzen'}


def karte(label: str, inhalt: str, glossar: bool = True):
    """Karte mit Label. Glossarwoerter werden automatisch antippbar."""
    text = markiere(inhalt) if glossar else inhalt
    st.markdown(
        f'<div class="karte"><div class="label">{label}</div>'
        f'<div class="inhalt">{text}</div></div>',
        unsafe_allow_html=True,
    )


def satz(inhalt: str, praefix: str = ''):
    """Fliesstext mit antippbaren Glossarwoertern."""
    if not inhalt:
        return
    st.markdown(f'<div class="inhalt">{praefix}{markiere(inhalt)}</div>',
                unsafe_allow_html=True)


def poollink(beschriftung: str, pfad: str):
    """Ein Verweis in den Materialpool. Oeffnet IMMER einen neuen Tab -
    sonst verlaesst der Schueler den Trainer und seine Sitzung ist weg."""
    st.markdown(
        f'<a class="poollink" href="{vault_url(pfad)}" target="_blank" '
        f'rel="noopener">{beschriftung}<span class="extern">↗</span></a>',
        unsafe_allow_html=True,
    )


def materialpool_block(arg_id: str = ''):
    """Aufklappbarer Bereich mit Verweisen in den Materialpool."""
    with st.expander('📖 Im Materialpool nachschlagen'):
        if arg_id and arg_id in ARGUMENT_NACH_ID:
            poollink('Dieses Argument im Materialpool',
                     ARGUMENT_NACH_ID[arg_id]['pfad'])
            gegen = gegenstrang(arg_id)
            if gegen:
                poollink(f'Was die Gegenseite sagt: {gegen[0]}', gegen[1])
        for schluessel in ('techniken', 'kriterien', 'ausgestaltung'):
            beschriftung, pfad = POOL_SEITEN[schluessel]
            poollink(beschriftung, pfad)
        st.caption('Öffnet sich in einem neuen Tab. Der Trainer bleibt offen – '
                   'wechsle einfach zurück, deine Antwort ist noch da.')


def ampel(name: str, wert: str):
    if not wert:
        return
    st.markdown(
        f'<div class="ampel">'
        f'<span class="punkt" style="background:{FARBE.get(wert, "#999")}"></span>'
        f'<span class="name">{name}</span>'
        f'<span class="wert">{WORT.get(wert, "")}</span></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Zugang, Limits
# ---------------------------------------------------------------------------

def secret(name: str, standard: str = '') -> str:
    try:
        return str(st.secrets.get(name, os.getenv(name, standard)))
    except Exception:
        return os.getenv(name, standard)


@st.cache_resource
def tageszaehler() -> dict:
    """Gemeinsamer Zaehler fuer alle Sitzungen.

    Achtung: Streamlit Community Cloud startet den Container bei Inaktivitaet
    neu; dann faengt der Zaehler wieder bei null an. Als Missbrauchsbremse
    reicht das, als Abrechnung nicht.
    """
    return {'tag': date.today(), 'anzahl': 0}


def freigabe_offen() -> tuple:
    """(offen, meldung) - Fenster kommt aus den Secrets, Format JJJJ-MM-TT."""
    start, ende = secret('FREIGABE_START'), secret('FREIGABE_ENDE')
    heute = date.today()
    try:
        if start and heute < datetime.strptime(start, '%Y-%m-%d').date():
            return False, f'Der Trainer ist ab dem {_de(start)} freigeschaltet.'
        if ende and heute > datetime.strptime(ende, '%Y-%m-%d').date():
            return False, f'Der Trainer war bis zum {_de(ende)} freigeschaltet.'
    except ValueError:
        return True, ''      # unlesbares Datum sperrt niemanden aus
    return True, ''


def _de(iso: str) -> str:
    j, m, t = iso.split('-')
    return f'{t}.{m}.{j}'


def budget_frei() -> tuple:
    z = tageszaehler()
    if z['tag'] != date.today():
        z['tag'], z['anzahl'] = date.today(), 0
    if z['anzahl'] >= TAGESGRENZE:
        return False, ('Der Trainer hat heute sein Tageslimit erreicht. '
                       'Bitte morgen noch einmal versuchen.')
    if st.session_state.ki_aufrufe >= SITZUNGSLIMIT:
        return False, (f'Du hast die {SITZUNGSLIMIT} Rückmeldungen dieser Sitzung '
                       'aufgebraucht. Schließe jetzt ab - deine Ergebnisse bleiben '
                       'erhalten.')
    return True, ''


def zaehle():
    tageszaehler()['anzahl'] += 1
    st.session_state.ki_aufrufe += 1


# ---------------------------------------------------------------------------
# Zustand
# ---------------------------------------------------------------------------

STARTWERTE = {
    'freigeschaltet': False,
    'schritt': 'rolle',
    'rolle': 'ohne Rolle',
    'technik': '',
    'ausgangsargument': '',
    'herkunft': '',
    'erwiderung': '',
    'ueberarbeitung': '',
    'fb': None,
    'fb2': None,
    'hilfestufe': 0,
    'hilfe': None,
    'erwiderung_feld': '',
    'muster': None,
    'bilanz': None,
    'ki_aufrufe': 0,
    'geuebt': [],
    'durchgaenge': [],
    'fehler': '',
}

for k, v in STARTWERTE.items():
    if k not in st.session_state:
        st.session_state[k] = v.copy() if isinstance(v, (list, dict)) else v


def gehe_zu(schritt: str):
    st.session_state.schritt = schritt
    st.rerun()


def sichere_durchgang():
    """Die fertige Uebung in die Liste fuer den Abschluss uebernehmen."""
    beste = st.session_state.ueberarbeitung or st.session_state.erwiderung
    if not beste:
        return
    letztes_fb = st.session_state.fb2 or st.session_state.fb or {}
    st.session_state.durchgaenge.append({
        'technik': st.session_state.technik,
        'argument': st.session_state.ausgangsargument,
        'erwiderung': beste,
        'kriterium': letztes_fb.get('genanntes_kriterium', ''),
    })
    if st.session_state.technik not in st.session_state.geuebt:
        st.session_state.geuebt.append(st.session_state.technik)


def neue_uebung(technik_behalten: bool, ziel: str = ''):
    """Durchgang sichern, Felder leeren und weitergehen."""
    sichere_durchgang()
    for k in ('ausgangsargument', 'herkunft', 'erwiderung', 'ueberarbeitung',
              'erwiderung_feld'):
        st.session_state[k] = ''
    st.session_state.pop('ueberarbeitung_feld', None)
    for k in ('fb', 'fb2', 'muster', 'hilfe'):
        st.session_state[k] = None
    st.session_state.hilfestufe = 0
    if not technik_behalten:
        st.session_state.technik = ''
    gehe_zu(ziel or ('argument' if technik_behalten else 'technik'))


def ki_client():
    """None, wenn kein Schluessel hinterlegt ist."""
    key = secret('OPENAI_API_KEY')
    return trainer.client_from_key(key) if key else None


def rufe_ki(funktion, *args):
    """KI-Aufruf mit Limitpruefung und verstaendlicher Fehlermeldung.

    Der Client wird ausserhalb des try geholt: st.stop() und st.rerun() werfen
    in Streamlit gewoehnliche Exceptions und wuerden hier sonst als
    Netzwerkfehler durchgehen.
    """
    frei, meldung = budget_frei()
    if not frei:
        st.session_state.fehler = meldung
        return None
    client = ki_client()
    if client is None:
        st.session_state.fehler = ('Der Trainer ist noch nicht fertig '
                                   'eingerichtet. Bitte die Lehrkraft ansprechen.')
        return None
    try:
        ergebnis = funktion(client, *args)
    except Exception:
        st.session_state.fehler = ('Die Rückmeldung hat gerade nicht geklappt. '
                                   'Versuche es noch einmal.')
        return None
    zaehle()
    st.session_state.fehler = ''
    return ergebnis


# ---------------------------------------------------------------------------
# Kopfbereich
# ---------------------------------------------------------------------------

SCHRITTE = {'rolle': 1, 'technik': 2, 'argument': 3, 'erwiderung': 4,
            'feedback': 5, 'muster': 6, 'abschluss': 7}


def kopf(titel: str):
    nr = SCHRITTE.get(st.session_state.schritt)
    if nr:
        st.markdown(f'<div class="schrittzeile">Schritt {nr} von 7</div>',
                    unsafe_allow_html=True)
    st.subheader(titel)


def rollenhinweis():
    """Leitkriterien im Hauptbereich - auf dem iPad ist die Seitenleiste zu."""
    rolle = st.session_state.rolle
    if rolle and rolle != 'ohne Rolle' and ROLLEN[rolle]:
        st.caption(f'**{rolle}** · Leitkriterien: {" · ".join(ROLLEN[rolle])}. '
                   'Du darfst auch andere Kriterien nennen.')


def restanzeige():
    rest = max(SITZUNGSLIMIT - st.session_state.ki_aufrufe, 0)
    if rest <= 4:
        st.caption(f'Noch {rest} Rückmeldungen in dieser Sitzung.')


def seitenleiste():
    with st.sidebar:
        st.markdown('### Diskussionstrainer')
        st.caption(LEITFRAGE)
        rolle = st.session_state.rolle
        if rolle and rolle != 'ohne Rolle':
            st.markdown(f'**Deine Rolle:** {rolle}')
            if ROLLEN[rolle]:
                st.markdown('**Deine Leitkriterien**')
                for k in ROLLEN[rolle]:
                    st.markdown(f'- {k}')
                st.caption('Du darfst auch andere Kriterien nennen. '
                           'Das wird nicht schlechter bewertet.')
        if st.session_state.technik:
            st.markdown(f'**Technik:** {TECHNIK_ANZEIGE[st.session_state.technik]}')
        rest = SITZUNGSLIMIT - st.session_state.ki_aufrufe
        st.caption(f'Noch {max(rest, 0)} Rückmeldungen in dieser Sitzung.')


# ---------------------------------------------------------------------------
# Zugang
# ---------------------------------------------------------------------------

offen, meldung = freigabe_offen()
if not offen:
    st.title('Diskussionstrainer')
    st.info(meldung)
    st.stop()

erwarteter_code = secret('KLASSENCODE')
if erwarteter_code and not st.session_state.freigeschaltet:
    st.title('Diskussionstrainer')
    st.write('Gib den Code ein, der auf deiner Rollenkarte steht.')
    eingabe = st.text_input('Code', label_visibility='collapsed')
    if st.button('Weiter', type='primary', use_container_width=True):
        if eingabe.strip().lower() == erwarteter_code.strip().lower():
            st.session_state.freigeschaltet = True
            st.rerun()
        else:
            st.error('Der Code stimmt nicht.')
    st.caption('Schreibe hier keine Namen und keine persönlichen Angaben hinein. '
               'Deine Texte werden nicht gespeichert.')
    st.stop()

seitenleiste()

if st.session_state.fehler:
    st.warning(st.session_state.fehler)


# ---------------------------------------------------------------------------
# Schritt 1 - Rolle
# ---------------------------------------------------------------------------

if st.session_state.schritt == 'rolle':
    st.title('Diskussionstrainer')
    st.write('Du übst hier, auf ein Argument der Gegenseite zu antworten. '
             'Das brauchst du in der Diskussion.')
    satz('Wörter mit einer gepunkteten Linie kannst du antippen. Dann erscheint '
         'eine kurze Erklärung – zum Beispiel bei Votum oder Quorum.')
    kopf('🙋 Welche Rolle hast du in der Diskussion?')
    st.caption('Deine Rolle wird nur angezeigt. Sie wird nicht bewertet.')
    for name in ROLLEN:
        beschriftung = 'Ich habe noch keine Rolle' if name == 'ohne Rolle' else name
        if st.button(beschriftung, key=f'rolle_{name}', use_container_width=True):
            st.session_state.rolle = name
            gehe_zu('technik')
    st.caption('Schreibe im Trainer keine Namen und keine persönlichen Angaben. '
               'Deine Texte werden nicht gespeichert.')


# ---------------------------------------------------------------------------
# Schritt 2 - Technik
# ---------------------------------------------------------------------------

elif st.session_state.schritt == 'technik':
    kopf('🛠️ Welche Technik willst du üben?')
    rollenhinweis()
    for anzeige, schluessel in TECHNIK_LABEL.items():
        if st.button(f"{TECHNIKEN[schluessel]['emoji']}  {anzeige}",
                     key=f'tech_{schluessel}', use_container_width=True):
            st.session_state.technik = schluessel
            gehe_zu('argument')
    with st.expander('🛠️ Was bedeuten die vier Techniken?'):
        for anzeige, schluessel in TECHNIK_LABEL.items():
            t = TECHNIKEN[schluessel]
            st.markdown(f'{t["emoji"]} **{anzeige}** – {t["leitfrage"]}')
            st.caption(t['erklaerung'])


# ---------------------------------------------------------------------------
# Schritt 3 - Ausgangsargument
# ---------------------------------------------------------------------------

elif st.session_state.schritt == 'argument':
    t = TECHNIKEN[st.session_state.technik]
    kopf(f"{t['emoji']} {TECHNIK_ANZEIGE[st.session_state.technik]}")
    karte('So geht das', t['erklaerung'])
    karte('💡 Beispiel', t['beispiel'])

    st.markdown('---')
    st.markdown('#### Auf welches Argument willst du antworten?')

    tab_selbst, tab_pool = st.tabs(['Selbst schreiben', 'Aus dem Materialpool'])

    with tab_selbst:
        st.write('Nenne ein Argument für oder gegen bundesweite Volksentscheide. '
                 'Schreibe möglichst auch dazu, warum jemand das so sieht.')
        eigenes = st.text_area('Argument', height=130, max_chars=600,
                               label_visibility='collapsed',
                               placeholder='Zum Beispiel: Volksentscheide bringen …')
        if st.button('Weiter mit diesem Argument', type='primary', key='eig_weiter', use_container_width=True):
            if eigenes.strip():
                st.session_state.ausgangsargument = eigenes.strip()
                st.session_state.herkunft = 'eigene Eingabe'
                gehe_zu('erwiderung')
            else:
                st.error('Schreibe zuerst ein Argument.')

    with tab_pool:
        st.write('Wähle ein Argument aus dem Materialpool.')
        seite = st.radio('Seite', ['pro', 'kontra'], horizontal=True,
                         format_func=lambda s: '➕ Pro Volksentscheide'
                         if s == 'pro' else '➖ Kontra Volksentscheide')
        auswahl = [a for a in ARGUMENTE if a['seite'] == seite]
        gewaehlt = st.radio(
            'Argument',
            [a['id'] for a in auswahl],
            format_func=lambda i: ARGUMENT_NACH_ID[i]['titel'],
            label_visibility='collapsed',
        )
        karte('💬 Das Argument', argument_text(gewaehlt))
        if st.button('Weiter mit diesem Argument', type='primary', key='pool_weiter', use_container_width=True):
            st.session_state.ausgangsargument = argument_text(gewaehlt)
            st.session_state.herkunft = gewaehlt
            gehe_zu('erwiderung')

    st.markdown('---')
    if st.button('Andere Technik wählen', use_container_width=True):
        gehe_zu('technik')


# ---------------------------------------------------------------------------
# Schritt 4 - Erwiderung
# ---------------------------------------------------------------------------

elif st.session_state.schritt == 'erwiderung':
    t = TECHNIKEN[st.session_state.technik]
    kopf('✍️ Schreibe deine Erwiderung')
    karte('💬 Das Ausgangsargument', st.session_state.ausgangsargument)
    karte(f"{t['emoji']} Deine Technik: " + TECHNIK_ANZEIGE[st.session_state.technik],
          t['leitfrage'])

    st.write('Antworte auf dieses Argument mit deiner Technik. '
             'Ein bis zwei Sätze reichen. Begründe, warum du das so siehst.')
    rollenhinweis()
    restanzeige()

    # Gestufte Hilfe auf Abruf - vor dem Schreiben
    h = st.session_state.hilfe
    if h:
        karte('💡 Tipp' if h['stufe'] == 1
              else '✍️ So könnte eine Erwiderung aussehen', h['inhalt'])
        if h.get('hinweis'):
            satz(h['hinweis'])

    stufe = st.session_state.hilfestufe
    if stufe < 2:
        beschriftung = ('💡 Ich brauche einen Tipp' if stufe == 0
                        else '🆘 Ich komme immer noch nicht weiter')
        if st.button(beschriftung, key='hilfe_btn', use_container_width=True):
            with st.spinner('Einen Moment …'):
                neu_h = rufe_ki(trainer.hilfe,
                                TECHNIK_ANZEIGE[st.session_state.technik],
                                st.session_state.ausgangsargument,
                                st.session_state.herkunft,
                                stufe + 1)
            if neu_h:
                st.session_state.hilfe = neu_h
                st.session_state.hilfestufe = stufe + 1
            st.rerun()

    # Das Feld braucht einen Key, sonst geht der getippte Text beim
    # Hilfe-Knopf verloren.
    text = st.text_area('Erwiderung', height=150, max_chars=700,
                        label_visibility='collapsed', key='erwiderung_feld',
                        placeholder='Deine Antwort in ein bis zwei Sätzen …')

    with st.expander('✍️ Satzanfänge, wenn du nicht weiterkommst'):
        st.markdown(
            '- Behauptung: „Das gilt allerdings nur, wenn …"\n'
            '- Begründung: „Denn …"\n'
            '- Beleg: „Ein Beispiel dafür ist …"\n'
            '- Kriterium: „Für die politische Gleichheit bedeutet das …"'
        )
        st.caption('Du musst nicht alle vier verwenden. Die Begründung ist das '
                   'Wichtigste.')

    materialpool_block(st.session_state.herkunft)

    if st.button('🚦 Rückmeldung holen', type='primary', use_container_width=True):
        if len(text.strip()) < 15:
            st.error('Schreibe noch etwas mehr – mindestens einen ganzen Satz.')
        else:
            st.session_state.erwiderung = text.strip()
            with st.spinner('Ich lese deine Antwort …'):
                fb = rufe_ki(trainer.feedback,
                             TECHNIK_ANZEIGE[st.session_state.technik],
                             st.session_state.ausgangsargument,
                             st.session_state.herkunft,
                             st.session_state.rolle,
                             False, '', st.session_state.erwiderung,
                             ['keine', 'Tipp', 'Formulierung'][st.session_state.hilfestufe])
            if fb:
                st.session_state.fb = fb
                gehe_zu('feedback')
            else:
                st.rerun()

    if st.button('Anderes Argument wählen', use_container_width=True):
        gehe_zu('argument')


# ---------------------------------------------------------------------------
# Schritt 5 - Feedback und Ueberarbeitung
# ---------------------------------------------------------------------------

elif st.session_state.schritt == 'feedback':
    fb = st.session_state.fb2 or st.session_state.fb
    zweite_runde = st.session_state.fb2 is not None
    kopf('🚦 Deine Rückmeldung')

    if fb.get('verstaendnisfrage'):
        karte('❓ Eine Frage an dich', fb['verstaendnisfrage'])
        st.write('Schreibe dein Argument noch einmal etwas deutlicher.')
        if st.button('Argument überarbeiten', type='primary', use_container_width=True):
            gehe_zu('argument')
        st.stop()

    karte('💬 Das Ausgangsargument', st.session_state.ausgangsargument)
    karte('✍️ Deine Erwiderung',
          st.session_state.ueberarbeitung or st.session_state.erwiderung)

    if fb.get('veraenderung'):
        karte('✅ Was sich verbessert hat', fb['veraenderung'])

    if not fb.get('technik_passt', True) and fb.get('technik_hinweis'):
        karte('🛠️ Zu deiner Technik', fb['technik_hinweis'])

    ampel('Bezug zum Argument', fb.get('ampel_bezug', ''))
    ampel('Technik', fb.get('ampel_technik', ''))
    ampel('Argumentqualität', fb.get('ampel_qualitaet', ''))

    if fb.get('lob'):
        satz(fb['lob'])

    vorschlaege = [h for h in (fb.get('hinweis_1'), fb.get('hinweis_2')) if h]
    if vorschlaege:
        st.markdown('#### 🔧 So machst du es besser')
        for i, v in enumerate(vorschlaege, 1):
            satz(v, praefix=f'<b>{i}.</b> ')

    if fb.get('formulierungshilfe'):
        karte('✍️ Fang so an und schreib selbst weiter', fb['formulierungshilfe'])

    for beleg in fb.get('ungepruefte_belege', []):
        st.caption(f'Diesen Beleg konnte ich im Materialpool nicht finden: {beleg}')

    krit = fb.get('genanntes_kriterium', '')
    if krit and krit in KRITERIEN_PFAD:
        poollink(f'Mehr zum Kriterium {krit}', KRITERIEN_PFAD[krit])

    materialpool_block(st.session_state.herkunft)

    st.markdown('---')

    if not zweite_runde:
        st.markdown('#### Überarbeite deine Erwiderung')
        st.session_state.setdefault('ueberarbeitung_feld',
                                    st.session_state.erwiderung)
        neu = st.text_area('Überarbeitung', height=150, max_chars=700,
                           label_visibility='collapsed',
                           key='ueberarbeitung_feld')
        if st.button('🔁 Überarbeitung prüfen lassen', type='primary', use_container_width=True):
            if neu.strip() == st.session_state.erwiderung:
                st.error('Ändere zuerst etwas an deinem Text.')
            elif len(neu.strip()) < 15:
                st.error('Schreibe noch etwas mehr.')
            else:
                st.session_state.ueberarbeitung = neu.strip()
                with st.spinner('Ich vergleiche beide Fassungen …'):
                    fb2 = rufe_ki(trainer.feedback,
                                  TECHNIK_ANZEIGE[st.session_state.technik],
                                  st.session_state.ausgangsargument,
                                  st.session_state.herkunft,
                                  st.session_state.rolle,
                                  True, st.session_state.erwiderung,
                                  st.session_state.ueberarbeitung,
                                  ['keine', 'Tipp', 'Formulierung'][st.session_state.hilfestufe])
                if fb2:
                    st.session_state.fb2 = fb2
                st.rerun()
        st.caption('Du kannst auch ohne Überarbeitung weitermachen.')
        if st.button('Weiter ohne Überarbeitung', use_container_width=True):
            gehe_zu('muster')
    else:
        if st.button('💡 Musterantwort ansehen', type='primary', use_container_width=True):
            gehe_zu('muster')
        if st.button('▶️ Nächste Übung', use_container_width=True):
            neue_uebung(technik_behalten=True)
        if st.button('🏁 Fertig – zur Lernbilanz', use_container_width=True):
            neue_uebung(technik_behalten=True, ziel='abschluss')


# ---------------------------------------------------------------------------
# Schritt 6 - Musterantwort
# ---------------------------------------------------------------------------

elif st.session_state.schritt == 'muster':
    kopf('💡 Eine mögliche Musterantwort')
    if st.session_state.muster is None:
        with st.spinner('Ich schreibe eine Musterantwort …'):
            m = rufe_ki(trainer.musterantwort,
                        TECHNIK_ANZEIGE[st.session_state.technik],
                        st.session_state.ausgangsargument,
                        st.session_state.herkunft,
                        st.session_state.ueberarbeitung or st.session_state.erwiderung)
        if m:
            st.session_state.muster = m
        else:
            if st.button('Weiter', use_container_width=True):
                gehe_zu('abschluss')
            st.stop()

    m = st.session_state.muster
    karte('✍️ Deine Fassung',
          st.session_state.ueberarbeitung or st.session_state.erwiderung)
    karte('💡 Musterantwort', m['musterantwort'])
    satz(m['warum'])
    satz(m['im_vergleich'])
    st.caption('Das ist eine mögliche gute Lösung, nicht die einzig richtige. '
               f'Grundlage: {m["quelle"]}')

    st.markdown('---')
    if st.button('▶️ Gleiche Technik noch einmal üben', type='primary', use_container_width=True):
        neue_uebung(technik_behalten=True)
    if st.button('🛠️ Technik wechseln', use_container_width=True):
        neue_uebung(technik_behalten=False)
    if st.button('Fertig – zur Lernbilanz', use_container_width=True):
        neue_uebung(technik_behalten=True, ziel='abschluss')


# ---------------------------------------------------------------------------
# Schritt 7 - Abschluss
# ---------------------------------------------------------------------------

elif st.session_state.schritt == 'abschluss':
    kopf('🎓 Deine Lernbilanz')
    durchgaenge = st.session_state.durchgaenge
    if not durchgaenge:
        st.write('Du hast noch keine Erwiderung fertig geübt.')
        if st.button('Zurück zur Übung', type='primary', use_container_width=True):
            gehe_zu('technik')
        st.stop()

    st.write('Welche Erwiderung war deine beste? Die nimmst du mit in die Diskussion.')
    index = st.radio(
        'Beste Erwiderung',
        list(range(len(durchgaenge))),
        format_func=lambda i: durchgaenge[i]['erwiderung'][:90]
        + ('…' if len(durchgaenge[i]['erwiderung']) > 90 else ''),
        label_visibility='collapsed',
    )
    beste = durchgaenge[index]

    # Wechselt die Auswahl, passt die alte Bilanz nicht mehr dazu.
    if st.session_state.get('bilanz_index') != index:
        st.session_state.bilanz = None
        st.session_state.bilanz_index = index

    if st.session_state.bilanz is None:
        if st.button('Lernbilanz erstellen', type='primary', use_container_width=True):
            with st.spinner('Einen Moment …'):
                b = rufe_ki(trainer.lernbilanz,
                            [TECHNIK_ANZEIGE[t] for t in st.session_state.geuebt],
                            beste['erwiderung'], beste['argument'],
                            TECHNIK_ANZEIGE[beste['technik']],
                            beste['kriterium'], st.session_state.rolle)
            if b:
                st.session_state.bilanz = b
            st.rerun()
    else:
        b = st.session_state.bilanz
        karte('⭐ Das kannst du schon', b['staerke'])
        karte('👉 Daran denkst du in der Diskussion', b['naechster_schritt'])
        karte('🧠 Merksatz', b['merksatz'])

    st.markdown('---')
    st.markdown('#### 📋 Für deine Rollenkarte')
    st.write('Tippe oben rechts im Kasten auf das Kopiersymbol, oder mache ein '
             'Bildschirmfoto.')

    zeilen = [
        'DISKUSSIONSTRAINER – MEIN ERGEBNIS',
        '',
        f'Argument der Gegenseite: {beste["argument"]}',
        f'Meine Technik: {TECHNIK_ANZEIGE[beste["technik"]]}',
        f'Meine Erwiderung: {beste["erwiderung"]}',
    ]
    if beste['kriterium']:
        zeilen.append(f'Kriterium: {beste["kriterium"]}')
    if st.session_state.bilanz:
        zeilen += ['', f'Merksatz: {st.session_state.bilanz["merksatz"]}',
                   f'Nächster Schritt: {st.session_state.bilanz["naechster_schritt"]}']
    st.code('\n'.join(zeilen), language=None)

    st.markdown('---')
    if st.button('Noch eine Übung machen', use_container_width=True):
        st.session_state.bilanz = None
        gehe_zu('technik')
