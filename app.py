import os, json, html, re, tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title='Diskussions-Analysator', page_icon='🗣️', layout='wide')

COLORS = {
    'Behauptung': '#ffe066',   # gelb
    'Begründung': '#8ce99a',   # grün
    'Beleg': '#74c0fc',        # blau  (= Beleg / Beispiel / Kontext)
}
SIDE_FILL = {'PRO': '#d3f9d8', 'KONTRA': '#ffe3e3', 'UNKLAR': '#f1f3f5'}
SIDE_BORDER = {'PRO': '#2f9e44', 'KONTRA': '#e03131', 'UNKLAR': '#868e96'}

SYSTEM_PROMPT = '''
Du analysierst deutschsprachige politische Diskussionen für Unterrichtszwecke und
zerlegst sie nach der Argument-Landkarte (Behauptung – Begründung – Beleg/Beispiel/Kontext – Kriterium).

REGELN:
1. Übernimm Argumentteile ausschließlich als WÖRTLICHE Zitate aus dem gelieferten Transkript. Nicht paraphrasieren, nicht sprachlich verbessern.
2. Ordne jeden erkennbaren argumentativen Beitrag PRO, KONTRA oder UNKLAR zur Streitfrage zu.
3. Zerlege den Beitrag in Behauptung (claim), Begründung (reason) und Beleg/Beispiel/Kontext (evidence).
   Diese drei Teile müssen EINDEUTIG und ÜBERSCHNEIDUNGSFREI sein: jede Textstelle gehört zu HÖCHSTENS EINER Kategorie,
   kein Wort darf gleichzeitig in zwei Teilen stehen. Jeder Teil ist ein zusammenhängendes wörtliches Teilstück von quote_full.
4. Wenn ein Bestandteil nicht vorhanden ist, gib einen leeren String zurück. Erfinde niemals Belege oder Begründungen.
5. JEDES eigenständige Argument darf nur EINMAL vorkommen. Gib Dopplungen (inhaltlich gleiche Argumente) nicht mehrfach aus.
6. Gib die Argumente in CHRONOLOGISCHER Reihenfolge ihres Auftretens im Transkript aus.
7. Bestimme für jeden Beitrag "role_in_strand":
   - "Argument": ein eigenständiges Argument, das eine Position stützt.
   - "Gegenargument": ein Einwand, der sich gegen ein FRÜHERES Argument richtet.
   - "Erwiderung": eine Antwort, die einen früheren Einwand entkräftet.
8. Bestimme "responds_to": die laufende Nummer (1-basiert, in Ausgabereihenfolge) des FRÜHEREN Beitrags, auf den sich dieser Beitrag bezieht.
   Bei einem eigenständigen Argument ohne Bezug: 0. Verweise nur auf kleinere Nummern (frühere Beiträge).
9. Ein Beitrag kann mehrere eigenständige Argumente enthalten; trenne diese dann in mehrere Einträge.
10. speaker darf leer bleiben, wenn der Sprecher nicht hervorgeht. quote_full = zusammenhängende Originalpassage, aus der die Teile stammen.
11. Ordne jedes Argument zusätzlich einem oder mehreren Demokratiequalitäts-Kriterien zu, wenn der Zusammenhang klar erkennbar ist. Nur diese Begriffe:
    INPUT: Partizipation, politische Gleichheit, Responsivität, Öffentlichkeit, Transparenz, Wettbewerb.
    OUTPUT: Entscheidungsqualität, Problemlösungsfähigkeit, Gemeinwohlorientierung, Regierungsfähigkeit, Umsetzbarkeit.
    Erzwinge keine Zuordnung; wenn kein Kriterium passt, gib eine leere Liste zurück.
12. Liefere valides JSON gemäß Schema.
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
                    'role_in_strand': {'type': 'string', 'enum': ['Argument', 'Gegenargument', 'Erwiderung']},
                    'responds_to': {'type': 'integer'},
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
                        }
                    }
                },
                'required': ['side', 'speaker', 'quote_full', 'claim', 'reason', 'evidence',
                             'role_in_strand', 'responds_to', 'confidence', 'democracy_criteria'],
                'additionalProperties': False
            }
        }
    },
    'required': ['arguments'],
    'additionalProperties': False
}


# ------------------------------------------------------------------ helpers
def client_from_key(key: str):
    return OpenAI(api_key=key)


def _norm(s: str) -> str:
    return re.sub(r'\s+', ' ', (s or '')).strip()


def fmt_mmss(sec) -> str:
    try:
        sec = int(round(float(sec)))
    except (TypeError, ValueError):
        return ''
    return f'{sec // 60:02d}:{sec % 60:02d}'


def time_label(arg, pos) -> str:
    """mm:ss wenn Audio-Zeitstempel vorliegt, sonst laufende Nummer (#pos)."""
    return fmt_mmss(arg['time_sec']) if arg.get('time_sec') is not None else f'#{pos}'


def transcribe_with_timestamps(client: OpenAI, uploaded_file):
    """Transkribiert mit Segment-Zeitstempeln (whisper-1, verbose_json).
    Rückgabe: (text, segments) mit segments = [{'start','end','text'}, ...]."""
    suffix = Path(uploaded_file.name).suffix or '.wav'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name
    try:
        with open(tmp_path, 'rb') as f:
            result = client.audio.transcriptions.create(
                model='whisper-1',
                file=f,
                language='de',
                response_format='verbose_json',
                timestamp_granularities=['segment'],
            )
        text = getattr(result, 'text', '') or ''
        segs = []
        for s in (getattr(result, 'segments', None) or []):
            if isinstance(s, dict):
                segs.append({'start': s.get('start', 0.0), 'end': s.get('end', 0.0), 'text': s.get('text', '')})
            else:
                segs.append({'start': getattr(s, 'start', 0.0), 'end': getattr(s, 'end', 0.0), 'text': getattr(s, 'text', '')})
        return text, segs
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def prior_summary(args) -> str:
    return '\n'.join(f'{i}: {_norm(a.get("claim") or a.get("quote_full"))[:70]}' for i, a in enumerate(args, 1))


def analyze_transcript(client: OpenAI, question: str, transcript: str, start_number: int = 1, prior: str = ''):
    extra = ''
    if start_number > 1:
        extra = (f'\n\nHINWEIS: Dies ist ein Folgeabschnitt. Nummeriere neue Beiträge fortlaufend ab {start_number}. '
                 f'Bereits erfasste frühere Beiträge (Nummer: Kurzform), auf die sich "responds_to" beziehen darf:\n{prior}')
    response = client.responses.create(
        model='gpt-5-mini',
        instructions=SYSTEM_PROMPT,
        input=f'Streitfrage: {question}\n\nTRANSKRIPT:\n{transcript}{extra}',
        text={'format': {'type': 'json_schema', 'name': 'discussion_arguments', 'schema': SCHEMA, 'strict': True}}
    )
    return json.loads(response.output_text)['arguments']


def dedupe_args(args):
    """Änderung 1: jedes Argument nur einmal (erstes Vorkommen gewinnt)."""
    seen, out = set(), []
    for a in args:
        key = _norm(a.get('quote_full')).lower() or _norm(a.get('claim')).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def assign_time_markers(args, segments, offset_sec: float = 0.0):
    """Änderung 2: mm:ss-Zeitmarker aus den Audio-Segmenten (best effort)."""
    for a in args:
        tsec = None
        q = _norm(a.get('quote_full'))
        head = q[:22].lower()
        if segments and head:
            for seg in segments:
                if head in _norm(seg.get('text')).lower():
                    tsec = float(seg.get('start', 0.0)) + offset_sec
                    break
        a['time_sec'] = tsec
    return args


def mark_text(text: str, claim: str, reason: str, evidence: str):
    """Änderung 3: eindeutige, ÜBERSCHNEIDUNGSFREIE Markierung.
    Jede Kategorie belegt einen eigenen, nicht überlappenden Textbereich."""
    spans, used = [], []
    for label, part in [('Behauptung', claim), ('Begründung', reason), ('Beleg', evidence)]:
        if not part:
            continue
        start = 0
        while True:
            idx = text.find(part, start)
            if idx < 0:
                break
            end = idx + len(part)
            if all(end <= s0 or idx >= e0 for s0, e0 in used):
                spans.append((idx, end, label))
                used.append((idx, end))
                break
            start = idx + 1
    spans.sort()
    out, pos = [], 0
    for s, e, label in spans:
        out.append(html.escape(text[pos:s]))
        out.append(f'<mark style="background:{COLORS[label]};padding:2px 3px;border-radius:3px">{html.escape(text[s:e])}</mark>')
        pos = e
    out.append(html.escape(text[pos:]))
    return ''.join(out)


def _dot_esc(s: str) -> str:
    return (s or '').replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')


def build_dot(question: str, args):
    """Änderung 4: top-down verzweigte Argument-Mindmap (Graphviz, rankdir=TB)."""
    L = ['digraph G {', 'rankdir=TB;', 'bgcolor="transparent";',
         'node [shape=box style="rounded,filled" fontname="Arial" fontsize=10 margin="0.14,0.08"];',
         'edge [fontname="Arial" fontsize=9 arrowsize=0.7 color="#868e96"];',
         f'root [label="{_dot_esc(question[:70])}" shape=oval fillcolor="#e9ecef" fontsize=11];']
    n = len(args)
    for i, a in enumerate(args, 1):
        marker = time_label(a, i)
        claim = _dot_esc((a.get('claim') or a.get('quote_full') or '')[:58])
        role = a.get('role_in_strand', '') or 'Argument'
        L.append(f'n{i} [label="[{marker}] {a.get("side","")} · {role}\\n{claim}" '
                 f'fillcolor="{SIDE_FILL.get(a.get("side"), "#f1f3f5")}"];')
    for i, a in enumerate(args, 1):
        rt = a.get('responds_to') or 0
        if isinstance(rt, int) and 1 <= rt <= n and rt < i:
            L.append(f'n{rt} -> n{i} [label="{_dot_esc(a.get("role_in_strand",""))}"];')
        else:
            L.append(f'root -> n{i};')
    L.append('}')
    return '\n'.join(L)


def render_argument(arg, idx):
    side = arg['side']
    border = SIDE_BORDER[side]
    marker = time_label(arg, idx)
    role = arg.get('role_in_strand', '') or 'Argument'
    speaker = f" · {html.escape(arg['speaker'])}" if arg.get('speaker') else ''
    marked = mark_text(arg['quote_full'], arg['claim'], arg['reason'], arg['evidence'])
    st.markdown(f'''<div style="border-left:6px solid {border};padding:10px 14px;margin:8px 0 16px;background:#fafafa;border-radius:5px">
    <div style="font-weight:700;margin-bottom:7px">[{marker}] {idx}. {side} · {role}{speaker}</div>
    <div style="font-size:1.05rem;line-height:1.65">„{marked}“</div>
    <div style="font-size:.82rem;color:#666;margin-top:7px">Erkennungssicherheit: {arg['confidence']:.0%}</div>
    </div>''', unsafe_allow_html=True)


def render_results(q, transcript, args, key_prefix=''):
    if not args:
        st.info('Es wurden noch keine Argumente erkannt.')
        return
    pro = [a for a in args if a['side'] == 'PRO']
    kontra = [a for a in args if a['side'] == 'KONTRA']
    unclear = [a for a in args if a['side'] == 'UNKLAR']

    c1, c2, c3 = st.columns(3)
    c1.metric('Pro-Argumente', len(pro))
    c2.metric('Kontra-Argumente', len(kontra))
    c3.metric('Unklar', len(unclear))

    st.markdown('### 🌳 Argument-Mindmap (oben → unten)')
    st.caption('Streitfrage oben, darunter verzweigen die Argumente; Kanten zeigen Gegenargument- und Erwiderungs-Stränge.')
    st.graphviz_chart(build_dot(q, args), use_container_width=True)

    st.markdown('### ⏱️ Chronologischer Verlauf')
    for i, a in enumerate(args, 1):
        render_argument(a, i)

    with st.expander('Interne Analyse: Demokratie-Kriterien anzeigen', expanded=False):
        rows = []
        for i, a in enumerate(args, 1):
            rows.append({'Nr.': i, 'Zeit': time_label(a, i), 'Seite': a['side'],
                         'Rolle': a.get('role_in_strand', ''),
                         'Argument im Wortlaut': a['quote_full'],
                         'Demokratiekriterien': ', '.join(a.get('democracy_criteria', []))})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    d1, d2, d3 = st.columns(3)
    txt = export_txt(q, transcript, args).encode('utf-8-sig')
    report = export_html(q, transcript, args).encode('utf-8')
    csv = export_csv(args)
    d1.download_button('TXT herunterladen', txt, f'diskussionsanalyse{key_prefix}.txt', 'text/plain', use_container_width=True, key=f'txt{key_prefix}')
    d2.download_button('Farbige HTML-Auswertung', report, f'diskussionsanalyse{key_prefix}.html', 'text/html', use_container_width=True, key=f'html{key_prefix}')
    d3.download_button('CSV-Daten herunterladen', csv, f'argumente{key_prefix}.csv', 'text/csv', use_container_width=True, key=f'csv{key_prefix}')


def export_csv(args):
    rows = []
    for i, a in enumerate(args, 1):
        rows.append({
            'Nr.': i, 'Zeit': time_label(a, i), 'Seite': a['side'], 'Rolle': a.get('role_in_strand', ''),
            'bezieht_sich_auf': a.get('responds_to', 0), 'Sprecher': a.get('speaker', ''),
            'Argument im Wortlaut': a['quote_full'], 'Behauptung': a['claim'], 'Begründung': a['reason'],
            'Beleg/Beispiel/Kontext': a['evidence'], 'Sicherheit': a['confidence'],
            'Demokratiekriterien (intern)': ', '.join(a.get('democracy_criteria', []))
        })
    return pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig')


def export_txt(question, transcript, args, include_internal=False):
    lines = ['DISKUSSIONSANALYSE', '=' * 72, f'Streitfrage: {question}', '',
             'Legende: 🟨 Behauptung | 🟩 Begründung | 🟦 Beleg/Beispiel/Kontext', '',
             'CHRONOLOGISCHER VERLAUF', '-' * 72]
    for i, a in enumerate(args, 1):
        speaker = f" – {a.get('speaker')}" if a.get('speaker') else ''
        rt = a.get('responds_to', 0)
        bezug = f' (bezieht sich auf #{rt})' if isinstance(rt, int) and rt > 0 else ''
        lines.append(f"[{time_label(a, i)}] {i}. {a['side']} · {a.get('role_in_strand','')}{speaker}{bezug}")
        lines.append(f"   Wortlaut: „{a.get('quote_full','')}“")
        if a.get('claim'):
            lines.append(f"   🟨 Behauptung: {a['claim']}")
        if a.get('reason'):
            lines.append(f"   🟩 Begründung: {a['reason']}")
        if a.get('evidence'):
            lines.append(f"   🟦 Beleg/Beispiel/Kontext: {a['evidence']}")
        lines.append(f"   Erkennungssicherheit: {a.get('confidence',0):.0%}")
        if include_internal:
            lines.append(f"   [INTERN] Kriterien: {', '.join(a.get('democracy_criteria', [])) or 'keine'}")
        lines.append('')
    lines += ['', 'VOLLSTÄNDIGES TRANSKRIPT', '-' * 72, transcript or '']
    return '\n'.join(lines)


def export_html(question, transcript, args):
    cards = []
    for i, a in enumerate(args, 1):
        marked = mark_text(a['quote_full'], a['claim'], a['reason'], a['evidence'])
        cards.append(f'''<section class="card {a['side'].lower()}"><h3>[{time_label(a,i)}] {i}. {a['side']} · {html.escape(a.get('role_in_strand',''))} {html.escape(a.get('speaker',''))}</h3><p>„{marked}“</p></section>''')
    return f'''<!doctype html><html lang="de"><meta charset="utf-8"><title>Diskussionsanalyse</title>
<style>body{{font-family:Arial,sans-serif;max-width:1000px;margin:40px auto;line-height:1.55}}.card{{padding:12px 16px;margin:14px 0;background:#fafafa;border-left:6px solid #888}}.pro{{border-color:#2f9e44}}.kontra{{border-color:#e03131}}.unklar{{border-color:#868e96}}mark{{padding:2px 3px;border-radius:3px}}</style>
<h1>Diskussionsanalyse</h1><p><b>Streitfrage:</b> {html.escape(question)}</p>
<p><mark style="background:{COLORS['Behauptung']}">Behauptung</mark> <mark style="background:{COLORS['Begründung']}">Begründung</mark> <mark style="background:{COLORS['Beleg']}">Beleg/Beispiel/Kontext</mark></p>
{''.join(cards)}<hr><h2>Vollständiges Transkript</h2><pre style="white-space:pre-wrap">{html.escape(transcript)}</pre></html>'''


# ------------------------------------------------------------------ UI
st.title('🗣️ Diskussions-Analysator')
st.caption('Audio → Transkript → chronologische Argument-Mindmap (Behauptung / Begründung / Beleg-Beispiel-Kontext) mit Zeitmarker · Kriterienzuordnung intern')

with st.sidebar:
    st.subheader('Einstellungen')
    api_key = os.getenv('OPENAI_API_KEY', '')
    try:
        api_key = st.secrets.get('OPENAI_API_KEY', api_key)
    except Exception:
        pass
    st.info('Web-Version: Der API-Key wird zentral als Server-Secret hinterlegt und muss auf Handy/PC nicht eingegeben werden.')
    st.markdown('**Farben**  \n🟨 Behauptung  \n🟩 Begründung  \n🟦 Beleg/Beispiel/Kontext')
    st.caption('Zeitmarker = mm:ss aus dem Audio (bei eingefügtem Transkript stattdessen laufende Nummer #).')

question = st.text_input('Streitfrage', value='Sollten in Deutschland bundesweite Volksentscheide eingeführt werden?')
mode = st.radio('Eingabe', ['Live-Mikrofon', 'Audio hochladen', 'Vorhandenes Transkript einfügen'], horizontal=True)

transcript_input = ''
uploaded = None
live_audio = None

if mode == 'Live-Mikrofon':
    st.subheader('🎙️ Live-Diskussion')
    st.caption('Nimm jeweils einen kurzen Diskussionsabschnitt auf. Die Mindmap wächst chronologisch weiter.')
    live_audio = st.audio_input('Nächsten Diskussionsabschnitt aufnehmen')
    lc1, lc2 = st.columns([2, 1])
    process_live = lc1.button('Abschnitt live auswerten', type='primary', use_container_width=True)
    clear_live = lc2.button('Live-Sitzung leeren', use_container_width=True)
    if clear_live:
        for key in ['live_transcript', 'live_arguments', 'live_question', 'live_offset']:
            st.session_state.pop(key, None)
        st.rerun()

    if process_live:
        if not api_key:
            st.error('Bitte einen OpenAI API-Key hinterlegen.')
            st.stop()
        if live_audio is None:
            st.error('Bitte zuerst einen Diskussionsabschnitt aufnehmen.')
            st.stop()
        client = client_from_key(api_key)
        try:
            with st.spinner('Live-Abschnitt wird transkribiert …'):
                chunk_text, segs = transcribe_with_timestamps(client, live_audio)
            existing = st.session_state.get('live_arguments', [])
            offset = st.session_state.get('live_offset', 0.0)
            with st.spinner('Neue Argumente werden einsortiert …'):
                chunk_args = analyze_transcript(client, question, chunk_text,
                                                start_number=len(existing) + 1, prior=prior_summary(existing))
            assign_time_markers(chunk_args, segs, offset_sec=offset)
            combined = dedupe_args(existing + chunk_args)
            previous_t = st.session_state.get('live_transcript', '')
            st.session_state['live_transcript'] = (previous_t + ('\n' if previous_t else '') + chunk_text).strip()
            st.session_state['live_arguments'] = combined
            st.session_state['live_question'] = question
            st.session_state['live_offset'] = offset + max([s['end'] for s in segs], default=0.0)
            st.success(f'{len(combined) - len(existing)} neue(s) Argument(e) ergänzt.')
        except Exception as e:
            st.error(f'Fehler: {e}')

    if st.session_state.get('live_arguments'):
        render_results(st.session_state['live_question'],
                       st.session_state.get('live_transcript', ''),
                       st.session_state['live_arguments'], key_prefix='_live')

elif mode == 'Audio hochladen':
    uploaded = st.file_uploader('Audio-Datei', type=['mp3', 'wav', 'm4a', 'mp4', 'mpeg', 'webm'])
else:
    transcript_input = st.text_area('Transkript', height=260, placeholder='Diskussion hier einfügen …')

if mode != 'Live-Mikrofon' and st.button('Analysieren', type='primary', use_container_width=True):
    if not api_key:
        st.error('Bitte einen OpenAI API-Key hinterlegen.')
        st.stop()
    if mode == 'Audio hochladen' and uploaded is None:
        st.error('Bitte zuerst eine Audio-Datei hochladen.')
        st.stop()
    if mode == 'Vorhandenes Transkript einfügen' and not transcript_input.strip():
        st.error('Bitte ein Transkript einfügen.')
        st.stop()

    client = client_from_key(api_key)
    try:
        segs = []
        if mode == 'Audio hochladen':
            with st.spinner('Audio wird transkribiert …'):
                transcript, segs = transcribe_with_timestamps(client, uploaded)
        else:
            transcript = transcript_input

        with st.spinner('Argumente werden analysiert …'):
            arguments = analyze_transcript(client, question, transcript)
        assign_time_markers(arguments, segs, offset_sec=0.0)
        arguments = dedupe_args(arguments)

        st.session_state['transcript'] = transcript
        st.session_state['arguments'] = arguments
        st.session_state['question'] = question
    except Exception as e:
        st.error(f'Fehler: {e}')

if mode != 'Live-Mikrofon' and 'arguments' in st.session_state:
    render_results(st.session_state['question'],
                   st.session_state['transcript'],
                   st.session_state['arguments'], key_prefix='')

st.divider()
st.caption('Hinweis: Automatische Transkription und Argumenterkennung können Fehler enthalten. '
           'Die automatische Verknüpfung zu Gegenargument-/Erwiderungs-Strängen ist eine Näherung und sollte gegen die Aufnahme geprüft werden.')
