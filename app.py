import os, json, html, tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title='Diskussions-Analysator', page_icon='🗣️', layout='wide')

COLORS = {
    'Behauptung': '#ffe066',   # gelb
    'Begründung': '#8ce99a',   # grün
    'Beleg': '#74c0fc',        # blau
}

SYSTEM_PROMPT = '''
Du analysierst deutschsprachige politische Diskussionen für Unterrichtszwecke.
WICHTIG:
1. Übernimm Argumentteile ausschließlich als wörtliche Zitate aus dem gelieferten Transkript. Nicht paraphrasieren, nicht sprachlich verbessern.
2. Ordne jeden erkennbaren argumentativen Beitrag PRO, KONTRA oder UNKLAR zur angegebenen Streitfrage zu.
3. Zerlege den Beitrag, soweit vorhanden, in Behauptung, Begründung und Beleg/Beispiel.
4. Wenn ein Bestandteil nicht vorhanden ist, gib einen leeren String zurück.
5. Schneide Füllwörter am Rand nur dann ab, wenn dadurch der Wortlaut des eigentlichen Arguments nicht verändert wird.
6. Erfinde niemals Belege oder Begründungen.
7. Ein Beitrag kann mehrere eigenständige Argumente enthalten; trenne diese dann.
8. speaker darf leer bleiben, wenn der Sprecher aus dem Transkript nicht hervorgeht.
9. quote_full enthält die zusammenhängende Originalpassage, aus der die Bestandteile stammen.
10. Ordne jedes Argument zusätzlich einem oder mehreren Demokratiequalitäts-Kriterien zu, wenn der inhaltliche Zusammenhang tatsächlich erkennbar ist. Verwende ausschließlich diese Begriffe:
INPUT: Partizipation, politische Gleichheit, Responsivität, Öffentlichkeit, Transparenz, Wettbewerb.
OUTPUT: Entscheidungsqualität, Problemlösungsfähigkeit, Gemeinwohlorientierung, Regierungsfähigkeit, Umsetzbarkeit.
11. Mehrfachzuordnungen sind erlaubt. Erzwinge keine Zuordnung; wenn kein Kriterium passt, gib eine leere Liste zurück.
12. Liefere valides JSON gemäß dem vorgegebenen Schema.
'''

SCHEMA = {
    'type': 'object',
    'properties': {
        'arguments': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'side': {'type': 'string', 'enum': ['PRO', 'KONTRA', 'UNKLAR']},
                    'speaker': {'type': 'string'},
                    'quote_full': {'type': 'string'},
                    'claim': {'type': 'string'},
                    'reason': {'type': 'string'},
                    'evidence': {'type': 'string'},
                    'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
                    'democracy_criteria': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                            'enum': [
                                'Partizipation', 'politische Gleichheit', 'Responsivität',
                                'Öffentlichkeit', 'Transparenz', 'Wettbewerb',
                                'Entscheidungsqualität', 'Problemlösungsfähigkeit',
                                'Gemeinwohlorientierung', 'Regierungsfähigkeit', 'Umsetzbarkeit'
                            ]
                        },
                        'uniqueItems': True
                    }
                },
                'required': ['side','speaker','quote_full','claim','reason','evidence','confidence','democracy_criteria'],
                'additionalProperties': False
            }
        }
    },
    'required': ['arguments'],
    'additionalProperties': False
}


def client_from_key(key: str):
    return OpenAI(api_key=key)


def transcribe_audio(client: OpenAI, uploaded_file):
    suffix = Path(uploaded_file.name).suffix or '.wav'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name
    try:
        with open(tmp_path, 'rb') as f:
            result = client.audio.transcriptions.create(
                model='gpt-4o-transcribe',
                file=f,
                language='de'
            )
        return result.text
    finally:
        try: os.unlink(tmp_path)
        except OSError: pass


def analyze_transcript(client: OpenAI, question: str, transcript: str):
    response = client.responses.create(
        model='gpt-5-mini',
        instructions=SYSTEM_PROMPT,
        input=f'Streitfrage: {question}\n\nTRANSKRIPT:\n{transcript}',
        text={
            'format': {
                'type': 'json_schema',
                'name': 'discussion_arguments',
                'schema': SCHEMA,
                'strict': True
            }
        }
    )
    return json.loads(response.output_text)['arguments']


def mark_text(text: str, claim: str, reason: str, evidence: str):
    # conservative, exact-substring highlighting; longest first to reduce overlaps
    escaped = html.escape(text)
    parts = [('Behauptung', claim), ('Begründung', reason), ('Beleg', evidence)]
    parts = [(label, p) for label, p in parts if p]
    parts.sort(key=lambda x: len(x[1]), reverse=True)
    for label, part in parts:
        ep = html.escape(part)
        escaped = escaped.replace(ep, f'<mark style="background:{COLORS[label]};padding:2px 3px;border-radius:3px">{ep}</mark>', 1)
    return escaped


def render_argument(arg, idx):
    side = arg['side']
    border = {'PRO':'#2f9e44','KONTRA':'#e03131','UNKLAR':'#868e96'}[side]
    speaker = f" · {html.escape(arg['speaker'])}" if arg.get('speaker') else ''
    marked = mark_text(arg['quote_full'], arg['claim'], arg['reason'], arg['evidence'])
    st.markdown(f'''<div style="border-left:6px solid {border};padding:10px 14px;margin:8px 0 16px;background:#fafafa;border-radius:5px">
    <div style="font-weight:700;margin-bottom:7px">{idx}. {side}{speaker}</div>
    <div style="font-size:1.05rem;line-height:1.65">„{marked}“</div>
    <div style="font-size:.82rem;color:#666;margin-top:7px">Erkennungssicherheit: {arg['confidence']:.0%}</div>
    </div>''', unsafe_allow_html=True)


def export_txt(question, transcript, args, include_internal=False):
    """Plain-text export that remains readable in any text editor.

    Real background colors are not available in TXT, so the same semantic
    highlighting is represented by colored-square markers.
    """
    lines = [
        'DISKUSSIONSANALYSE',
        '=' * 72,
        f'Streitfrage: {question}',
        '',
        'Legende: 🟨 Behauptung | 🟩 Begründung | 🟦 Beleg/Beispiel',
        '',
    ]

    for side in ('PRO', 'KONTRA', 'UNKLAR'):
        selected = [a for a in args if a.get('side') == side]
        if not selected:
            continue
        lines.extend([side, '-' * len(side)])
        for i, a in enumerate(selected, 1):
            speaker = f" – {a.get('speaker')}" if a.get('speaker') else ''
            lines.append(f'{i}. {side}{speaker}')
            lines.append(f"   Wortlaut: „{a.get('quote_full','')}“")
            if a.get('claim'):
                lines.append(f"   🟨 Behauptung: {a['claim']}")
            if a.get('reason'):
                lines.append(f"   🟩 Begründung: {a['reason']}")
            if a.get('evidence'):
                lines.append(f"   🟦 Beleg/Beispiel: {a['evidence']}")
            lines.append(f"   Erkennungssicherheit: {a.get('confidence',0):.0%}")
            if include_internal:
                criteria = ', '.join(a.get('democracy_criteria', [])) or 'keine Zuordnung'
                lines.append(f'   [INTERN] Demokratie-Kriterien: {criteria}')
            lines.append('')

    lines.extend(['', 'VOLLSTÄNDIGES TRANSKRIPT', '-' * 72, transcript or ''])
    return '\n'.join(lines)


def export_html(question, transcript, args):
    cards = []
    for i,a in enumerate(args,1):
        marked = mark_text(a['quote_full'], a['claim'], a['reason'], a['evidence'])
        cards.append(f'''<section class="card {a['side'].lower()}"><h3>{i}. {a['side']} {html.escape(a['speaker'])}</h3><p>„{marked}“</p></section>''')
    return f'''<!doctype html><html lang="de"><meta charset="utf-8"><title>Diskussionsanalyse</title>
<style>body{{font-family:Arial,sans-serif;max-width:1000px;margin:40px auto;line-height:1.55}}.card{{padding:12px 16px;margin:14px 0;background:#fafafa;border-left:6px solid #888}}.pro{{border-color:#2f9e44}}.kontra{{border-color:#e03131}}.unklar{{border-color:#868e96}}mark{{padding:2px 3px;border-radius:3px}}</style>
<h1>Diskussionsanalyse</h1><p><b>Streitfrage:</b> {html.escape(question)}</p>
<p><mark style="background:{COLORS['Behauptung']}">Behauptung</mark> <mark style="background:{COLORS['Begründung']}">Begründung</mark> <mark style="background:{COLORS['Beleg']}">Beleg/Beispiel</mark></p>
{''.join(cards)}<hr><h2>Vollständiges Transkript</h2><pre style="white-space:pre-wrap">{html.escape(transcript)}</pre></html>'''

st.title('🗣️ Diskussions-Analysator')
st.caption('Audio → Transkript → Pro/Contra → Behauptung / Begründung / Beleg im Wortlaut · Kriterienzuordnung intern')

with st.sidebar:
    st.subheader('Einstellungen')
    api_key = os.getenv('OPENAI_API_KEY','')
    try:
        api_key = st.secrets.get('OPENAI_API_KEY', api_key)
    except Exception:
        pass
    st.info('Web-Version: Der API-Key wird zentral als Server-Secret hinterlegt und muss auf Handy/PC nicht eingegeben werden.')
    st.markdown('**Farben**  \n🟨 Behauptung  \n🟩 Begründung  \n🟦 Beleg/Beispiel')

question = st.text_input('Streitfrage', value='Sollten in Deutschland bundesweite Volksentscheide eingeführt werden?')
mode = st.radio('Eingabe', ['Live-Mikrofon', 'Audio hochladen', 'Vorhandenes Transkript einfügen'], horizontal=True)

transcript_input = ''
uploaded = None
live_audio = None

if mode == 'Live-Mikrofon':
    st.subheader('🎙️ Live-Diskussion')
    st.caption('Nimm jeweils einen kurzen Diskussionsabschnitt auf. Nach dem Verarbeiten wächst die PRO-/KONTRA-Ansicht automatisch weiter.')
    live_audio = st.audio_input('Nächsten Diskussionsabschnitt aufnehmen')
    lc1, lc2 = st.columns([2,1])
    process_live = lc1.button('Abschnitt live auswerten', type='primary', use_container_width=True)
    clear_live = lc2.button('Live-Sitzung leeren', use_container_width=True)
    if clear_live:
        for key in ['live_transcript','live_arguments','live_question']:
            st.session_state.pop(key, None)
        st.rerun()

    if process_live:
        if not api_key:
            st.error('Bitte einen OpenAI API-Key eingeben.')
            st.stop()
        if live_audio is None:
            st.error('Bitte zuerst einen Diskussionsabschnitt aufnehmen.')
            st.stop()
        client = client_from_key(api_key)
        try:
            with st.spinner('Live-Abschnitt wird transkribiert …'):
                chunk_text = transcribe_audio(client, live_audio)
            with st.spinner('Neue Argumente werden einsortiert …'):
                chunk_args = analyze_transcript(client, question, chunk_text)
            previous_t = st.session_state.get('live_transcript','')
            previous_a = st.session_state.get('live_arguments',[])
            st.session_state['live_transcript'] = (previous_t + ('\n' if previous_t else '') + chunk_text).strip()
            st.session_state['live_arguments'] = previous_a + chunk_args
            st.session_state['live_question'] = question
            st.success(f'{len(chunk_args)} Argument(e) aus diesem Abschnitt ergänzt.')
        except Exception as e:
            st.error(f'Fehler: {e}')

    if st.session_state.get('live_arguments'):
        live_args = st.session_state['live_arguments']
        live_t = st.session_state.get('live_transcript','')
        live_q = st.session_state.get('live_question', question)
        pro_live = [a for a in live_args if a['side']=='PRO']
        kontra_live = [a for a in live_args if a['side']=='KONTRA']
        unclear_live = [a for a in live_args if a['side']=='UNKLAR']

        st.markdown('### Laufende Argumentübersicht')
        m1,m2,m3 = st.columns(3)
        m1.metric('PRO', len(pro_live)); m2.metric('KONTRA', len(kontra_live)); m3.metric('UNKLAR', len(unclear_live))
        col_pro, col_kontra = st.columns(2)
        with col_pro:
            st.markdown('#### ✅ PRO')
            for i,a in enumerate(pro_live,1): render_argument(a,i)
        with col_kontra:
            st.markdown('#### ❌ KONTRA')
            for i,a in enumerate(kontra_live,1): render_argument(a,i)
        if unclear_live:
            with st.expander('Unklare Beiträge', expanded=False):
                for i,a in enumerate(unclear_live,1): render_argument(a,i)

        with st.expander('Interne Live-Analyse: Demokratie-Kriterien', expanded=False):
            crit_rows=[]
            for i,a in enumerate(live_args,1):
                crit_rows.append({'Nr.':i,'Seite':a['side'],'Argument im Wortlaut':a['quote_full'],'Demokratiekriterien':', '.join(a.get('democracy_criteria',[]))})
            st.dataframe(pd.DataFrame(crit_rows), use_container_width=True, hide_index=True)

        live_rows=[]
        for a in live_args:
            live_rows.append({'Seite':a['side'],'Sprecher':a['speaker'],'Argument im Wortlaut':a['quote_full'],'Behauptung':a['claim'],'Begründung':a['reason'],'Beleg/Beispiel':a['evidence'],'Sicherheit':a['confidence'],'Demokratiekriterien (intern)':', '.join(a.get('democracy_criteria',[]))})
        live_df=pd.DataFrame(live_rows)
        csv_live=live_df.to_csv(index=False).encode('utf-8-sig')
        report_live=export_html(live_q, live_t, live_args).encode('utf-8')
        txt_live=export_txt(live_q, live_t, live_args, include_internal=False).encode('utf-8-sig')
        e1,e2,e3=st.columns(3)
        e1.download_button('Live-Ergebnis als TXT', txt_live, 'diskussionsanalyse_live.txt', 'text/plain', use_container_width=True)
        e2.download_button('Live-Ergebnis als HTML', report_live, 'diskussionsanalyse_live.html', 'text/html', use_container_width=True)
        e3.download_button('Live-Daten als CSV', csv_live, 'argumente_live.csv', 'text/csv', use_container_width=True)

elif mode == 'Audio hochladen':
    uploaded = st.file_uploader('Audio-Datei', type=['mp3','wav','m4a','mp4','mpeg','webm'])
else:
    transcript_input = st.text_area('Transkript', height=260, placeholder='Diskussion hier einfügen …')

if mode != 'Live-Mikrofon' and st.button('Analysieren', type='primary', use_container_width=True):
    if not api_key:
        st.error('Bitte einen OpenAI API-Key eingeben.')
        st.stop()
    if mode == 'Audio hochladen' and uploaded is None:
        st.error('Bitte zuerst eine Audio-Datei hochladen.')
        st.stop()
    if mode == 'Vorhandenes Transkript einfügen' and not transcript_input.strip():
        st.error('Bitte ein Transkript einfügen.')
        st.stop()

    client = client_from_key(api_key)
    try:
        if mode == 'Audio hochladen':
            with st.spinner('Audio wird transkribiert …'):
                transcript = transcribe_audio(client, uploaded)
        else:
            transcript = transcript_input

        with st.spinner('Argumente werden analysiert …'):
            arguments = analyze_transcript(client, question, transcript)

        st.session_state['transcript'] = transcript
        st.session_state['arguments'] = arguments
        st.session_state['question'] = question
    except Exception as e:
        st.error(f'Fehler: {e}')

if 'arguments' in st.session_state:
    arguments = st.session_state['arguments']
    transcript = st.session_state['transcript']
    q = st.session_state['question']

    pro = [a for a in arguments if a['side']=='PRO']
    kontra = [a for a in arguments if a['side']=='KONTRA']
    unclear = [a for a in arguments if a['side']=='UNKLAR']

    c1,c2,c3 = st.columns(3)
    c1.metric('Pro-Argumente', len(pro)); c2.metric('Kontra-Argumente', len(kontra)); c3.metric('Unklar', len(unclear))

    tab1, tab2, tab3, tab4 = st.tabs(['PRO', 'KONTRA', 'UNKLAR', 'Transkript'])
    with tab1:
        for i,a in enumerate(pro,1): render_argument(a,i)
    with tab2:
        for i,a in enumerate(kontra,1): render_argument(a,i)
    with tab3:
        for i,a in enumerate(unclear,1): render_argument(a,i)
    with tab4:
        st.text_area('Vollständiges Transkript', transcript, height=400)

    # Interne Kriterienzuordnung: standardmäßig ausgeblendet.
    # Sie kann bei Bedarf zur Kontrolle eingeblendet werden, ohne die Schüleransicht zu überladen.
    with st.expander('Interne Analyse: Demokratie-Kriterien anzeigen', expanded=False):
        criteria_rows = []
        for i, a in enumerate(arguments, 1):
            criteria_rows.append({
                'Nr.': i,
                'Seite': a['side'],
                'Argument im Wortlaut': a['quote_full'],
                'Demokratiekriterien': ', '.join(a.get('democracy_criteria', []))
            })
        st.dataframe(pd.DataFrame(criteria_rows), use_container_width=True, hide_index=True)

    rows = []
    for a in arguments:
        rows.append({
            'Seite': a['side'], 'Sprecher': a['speaker'], 'Argument im Wortlaut': a['quote_full'],
            'Behauptung': a['claim'], 'Begründung': a['reason'], 'Beleg/Beispiel': a['evidence'],
            'Sicherheit': a['confidence'],
            'Demokratiekriterien (intern)': ', '.join(a.get('democracy_criteria', []))
        })
    df = pd.DataFrame(rows)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    report = export_html(q, transcript, arguments).encode('utf-8')
    txt = export_txt(q, transcript, arguments, include_internal=False).encode('utf-8-sig')
    d1,d2,d3 = st.columns(3)
    d1.download_button('TXT herunterladen', txt, 'diskussionsanalyse.txt', 'text/plain', use_container_width=True)
    d2.download_button('Farbige HTML-Auswertung', report, 'diskussionsanalyse.html', 'text/html', use_container_width=True)
    d3.download_button('CSV-Daten herunterladen', csv, 'argumente.csv', 'text/csv', use_container_width=True)

st.divider()
st.caption('Hinweis: Automatische Transkription und Argumenterkennung können Fehler enthalten. Für Bewertung oder Benotung sollte das Ergebnis gegen die Aufnahme geprüft werden.')
