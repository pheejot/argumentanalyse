import os, json, html, re, tempfile
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
   Die Zuordnung muss EINDEUTIG und ÜBERSCHNEIDUNGSFREI sein: jede Textstelle gehört zu HÖCHSTENS EINER Kategorie,
   kein Wort darf gleichzeitig in zwei Teilen stehen. Jeder Teil ist ein zusammenhängendes wörtliches Teilstück von quote_full.
4. Wenn ein Bestandteil nicht vorhanden ist, gib einen leeren String zurück.
5. Schneide Füllwörter am Rand nur dann ab, wenn dadurch der Wortlaut des eigentlichen Arguments nicht verändert wird.
6. Erfinde niemals Belege oder Begründungen.
7. Ein Beitrag kann mehrere eigenständige Argumente enthalten; trenne diese dann.
8. Jedes eigenständige Argument darf nur EINMAL vorkommen. Gib inhaltlich gleiche Argumente nicht mehrfach aus.
9. Gib die Argumente in CHRONOLOGISCHER Reihenfolge ihres Auftretens im Transkript aus.
10. speaker darf leer bleiben, wenn der Sprecher aus dem Transkript nicht hervorgeht.
11. quote_full enthält die zusammenhängende Originalpassage, aus der die Bestandteile stammen.
12. Ordne jedes Argument zusätzlich einem oder mehreren Demokratiequalitäts-Kriterien zu, wenn der inhaltliche Zusammenhang tatsächlich erkennbar ist. Verwende ausschließlich diese Begriffe:
INPUT: Partizipation, politische Gleichheit, Responsivität, Öffentlichkeit, Transparenz, Wettbewerb.
OUTPUT: Entscheidungsqualität, Problemlösungsfähigkeit, Gemeinwohlorientierung, Regierungsfähigkeit, Umsetzbarkeit.
13. Mehrfachzuordnungen sind erlaubt. Erzwinge keine Zuordnung; wenn kein Kriterium passt, gib eine leere Liste zurück.
14. Liefere valides JSON gemäß dem vorgegebenen Schema.
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
                        }
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


# ---------------------------------------------------------------------------
# TESTMODUS – Beispiel-Diskussion (Argumentkette)
# Diese Beispiel-Diskussion wird im Testmodus ohne Mikrofon und ohne
# Transkriptionskosten direkt analysiert. Zum Ersetzen durch einen eigenen
# Schlagabtausch einfach die Segmente unten austauschen: pro Redebeitrag ein
# Eintrag mit 'start'/'end' (Sekunden, für die mm:ss-Anzeige) und 'text'.
# ---------------------------------------------------------------------------
SAMPLE_QUESTION = 'Sollten in Deutschland bundesweite Volksentscheide eingeführt werden?'
SAMPLE_SEGMENTS = [
    {'start': 0.0,   'end': 19.0,  'text': 'Frau Berger: Bundesweite Volksentscheide sollten eingeführt werden, weil sie die Bürgerinnen und Bürger direkt an wichtigen Entscheidungen beteiligen. In der Schweiz zeigt sich seit Jahrzehnten, dass regelmäßige Abstimmungen die politische Beteiligung stärken.'},
    {'start': 20.0,  'end': 41.0,  'text': 'Herr Klein: Ich halte bundesweite Volksentscheide für riskant, weil komplexe Gesetzesfragen sich nicht auf ein einfaches Ja oder Nein reduzieren lassen. Beim Brexit-Referendum in Großbritannien führte genau diese Verkürzung zu jahrelanger Unsicherheit.'},
    {'start': 42.0,  'end': 64.0,  'text': 'Frau Berger: Das Risiko lässt sich begrenzen, wenn hohe Beteiligungsquoren und eine klare rechtliche Vorprüfung gelten. Studien der OECD zeigen, dass gut ausgestaltete Beteiligungsverfahren die Qualität politischer Entscheidungen sogar erhöhen können.'},
    {'start': 65.0,  'end': 88.0,  'text': 'Herr Klein: Trotzdem droht die Gefahr, dass finanzstarke Gruppen die Kampagnen dominieren, denn wer mehr Geld hat, erreicht mehr Menschen. In mehreren US-Bundesstaaten haben teure Kampagnen die Ergebnisse von Volksabstimmungen stark beeinflusst.'},
    {'start': 89.0,  'end': 106.0, 'text': 'Frau Berger: Gerade deshalb braucht es verbindliche Transparenzregeln für die Kampagnenfinanzierung, damit alle Seiten fair gehört werden.'},
    {'start': 107.0, 'end': 123.0, 'text': 'Moderatorin: Man muss das sicher differenziert sehen, es gibt nachvollziehbare Gründe auf beiden Seiten.'},
]
SAMPLE_TRANSCRIPT = '\n'.join(s['text'] for s in SAMPLE_SEGMENTS)
TEST_MODE = 'Testmodus (Beispiel-Diskussion)'


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
    """Änderung 2: mm:ss aus dem Audio, sonst laufende Nummer (#pos)."""
    return fmt_mmss(arg['time_sec']) if arg.get('time_sec') is not None else f'#{pos}'


def transcribe_audio(client: OpenAI, uploaded_file):
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
        head = _norm(a.get('quote_full'))[:22].lower()
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


def render_argument(arg, idx):
    side = arg['side']
    border = {'PRO':'#2f9e44','KONTRA':'#e03131','UNKLAR':'#868e96'}[side]
    speaker = f" · {html.escape(arg['speaker'])}" if arg.get('speaker') else ''
    marked = mark_text(arg['quote_full'], arg['claim'], arg['reason'], arg['evidence'])
    st.markdown(f'''<div style="border-left:6px solid {border};padding:10px 14px;margin:8px 0 16px;background:#fafafa;border-radius:5px">
    <div style="font-weight:700;margin-bottom:7px">[{time_label(arg, idx)}] {idx}. {side}{speaker}</div>
    <div style="font-size:1.05rem;line-height:1.65">„{marked}“</div>
    <div style="font-size:.82rem;color:#666;margin-top:7px">Erkennungssicherheit: {arg['confidence']:.0%}</div>
    </div>''', unsafe_allow_html=True)


CHAT_CSS = '''<style>
.da-wrap{max-width:1150px;margin:4px auto 2px}
.da-head{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:8px;position:sticky;top:0;z-index:2}
.da-h{font-weight:800;padding:6px 10px;border-radius:7px;text-align:center;color:#fff;font-size:1rem}
.da-h.pro{background:#2f9e44}
.da-h.kontra{background:#e03131}
.da-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:7px 0;align-items:start}
.da-cell{display:flex}
.da-cell.left{justify-content:flex-start}
.da-cell.right{justify-content:flex-end}
.da-cell.mid{grid-column:1 / span 2;justify-content:center}
.da-bubble{max-width:94%;padding:9px 13px;border-radius:14px;line-height:1.5;box-shadow:0 1px 3px rgba(0,0,0,.10)}
.da-bubble.pro{background:#eef9f1;border:1px solid #2f9e44;border-bottom-left-radius:4px}
.da-bubble.kontra{background:#fdecec;border:1px solid #e03131;border-bottom-right-radius:4px}
.da-bubble.unklar{background:#f1f3f5;border:1px solid #adb5bd;max-width:70%;text-align:center}
.da-meta{font-size:.76rem;color:#5a5a5a;font-weight:700;margin-bottom:3px}
.da-q{font-size:1.02rem}
.da-conf{font-size:.72rem;color:#8a8a8a;margin-top:5px}
.da-wrap mark{padding:2px 3px;border-radius:3px}
</style>'''


def render_chat_columns(args):
    """Chronologische Chat-Ansicht (nach Vorbild eines Zwei-Spalten-Chats):
    PRO links, KONTRA rechts, UNKLAR mittig. Jedes Argument ist eine Zeile;
    die Gegenspalte bleibt leer, sodass sichtbar wird, welches Argument zeitlich
    zuerst gefallen ist. Reihenfolge = chronologisch (wie in args geliefert)."""
    parts = [CHAT_CSS, '<div class="da-wrap">',
             '<div class="da-head"><div class="da-h pro">✅ PRO</div><div class="da-h kontra">❌ KONTRA</div></div>']
    for i, a in enumerate(args, 1):
        side = a.get('side', 'UNKLAR')
        cls = {'PRO': 'pro', 'KONTRA': 'kontra'}.get(side, 'unklar')
        marked = mark_text(a.get('quote_full', ''), a.get('claim', ''), a.get('reason', ''), a.get('evidence', ''))
        spk = f" · {html.escape(a['speaker'])}" if a.get('speaker') else ''
        meta = f"[{time_label(a, i)}]{spk}"
        bubble = (f'<div class="da-bubble {cls}"><div class="da-meta">{meta}</div>'
                  f'<div class="da-q">„{marked}“</div>'
                  f'<div class="da-conf">Sicherheit: {a.get("confidence", 0):.0%}</div></div>')
        if side == 'PRO':
            parts.append(f'<div class="da-row"><div class="da-cell left">{bubble}</div><div class="da-cell right"></div></div>')
        elif side == 'KONTRA':
            parts.append(f'<div class="da-row"><div class="da-cell left"></div><div class="da-cell right">{bubble}</div></div>')
        else:
            parts.append(f'<div class="da-row"><div class="da-cell mid">{bubble}</div></div>')
    parts.append('</div>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


def export_txt(question, transcript, args, include_internal=False):
    """Plain-text export that remains readable in any text editor."""
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
            lines.append(f"[{time_label(a, i)}] {i}. {side}{speaker}")
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
    for i, a in enumerate(args, 1):
        marked = mark_text(a['quote_full'], a['claim'], a['reason'], a['evidence'])
        cards.append(f'''<section class="card {a['side'].lower()}"><h3>[{time_label(a,i)}] {i}. {a['side']} {html.escape(a['speaker'])}</h3><p>„{marked}“</p></section>''')
    return f'''<!doctype html><html lang="de"><meta charset="utf-8"><title>Diskussionsanalyse</title>
<style>body{{font-family:Arial,sans-serif;max-width:1000px;margin:40px auto;line-height:1.55}}.card{{padding:12px 16px;margin:14px 0;background:#fafafa;border-left:6px solid #888}}.pro{{border-color:#2f9e44}}.kontra{{border-color:#e03131}}.unklar{{border-color:#868e96}}mark{{padding:2px 3px;border-radius:3px}}</style>
<h1>Diskussionsanalyse</h1><p><b>Streitfrage:</b> {html.escape(question)}</p>
<p><mark style="background:{COLORS['Behauptung']}">Behauptung</mark> <mark style="background:{COLORS['Begründung']}">Begründung</mark> <mark style="background:{COLORS['Beleg']}">Beleg/Beispiel</mark></p>
{''.join(cards)}<hr><h2>Vollständiges Transkript</h2><pre style="white-space:pre-wrap">{html.escape(transcript)}</pre></html>'''


st.title('🗣️ Diskussions-Analysator')
st.caption('Audio → Transkript → Pro/Contra → Behauptung / Begründung / Beleg im Wortlaut, chronologisch mit Zeitmarker · Kriterienzuordnung intern')

with st.sidebar:
    st.subheader('Einstellungen')
    api_key = os.getenv('OPENAI_API_KEY','')
    try:
        api_key = st.secrets.get('OPENAI_API_KEY', api_key)
    except Exception:
        pass
    st.info('Web-Version: Der API-Key wird zentral als Server-Secret hinterlegt und muss auf Handy/PC nicht eingegeben werden.')
    st.markdown('**Farben**  \n🟨 Behauptung  \n🟩 Begründung  \n🟦 Beleg/Beispiel')
    st.caption('Zeitmarker = mm:ss aus dem Audio; bei eingefügtem Transkript stattdessen laufende Nummer (#).')

question = st.text_input('Streitfrage', value='Sollten in Deutschland bundesweite Volksentscheide eingeführt werden?')
mode = st.radio('Eingabe', ['Live-Mikrofon', 'Audio hochladen', 'Vorhandenes Transkript einfügen', TEST_MODE], horizontal=True)

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
        for key in ['live_transcript','live_arguments','live_question','live_offset']:
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
                chunk_text, segs = transcribe_audio(client, live_audio)
            with st.spinner('Neue Argumente werden einsortiert …'):
                chunk_args = analyze_transcript(client, question, chunk_text)
            offset = st.session_state.get('live_offset', 0.0)
            assign_time_markers(chunk_args, segs, offset_sec=offset)
            previous_t = st.session_state.get('live_transcript','')
            previous_a = st.session_state.get('live_arguments',[])
            st.session_state['live_transcript'] = (previous_t + ('\n' if previous_t else '') + chunk_text).strip()
            st.session_state['live_arguments'] = dedupe_args(previous_a + chunk_args)
            st.session_state['live_question'] = question
            st.session_state['live_offset'] = offset + max([s['end'] for s in segs], default=0.0)
            st.success(f'{len(chunk_args)} Argument(e) aus diesem Abschnitt verarbeitet.')
        except Exception as e:
            st.error(f'Fehler: {e}')

    if st.session_state.get('live_arguments'):
        live_args = st.session_state['live_arguments']
        live_t = st.session_state.get('live_transcript','')
        live_q = st.session_state.get('live_question', question)
        pro_live = [a for a in live_args if a['side']=='PRO']
        kontra_live = [a for a in live_args if a['side']=='KONTRA']
        unclear_live = [a for a in live_args if a['side']=='UNKLAR']

        st.markdown('### Laufender Verlauf (PRO ↔ KONTRA)')
        m1,m2,m3 = st.columns(3)
        m1.metric('PRO', len(pro_live)); m2.metric('KONTRA', len(kontra_live)); m3.metric('UNKLAR', len(unclear_live))
        render_chat_columns(live_args)

        with st.expander('Interne Live-Analyse: Demokratie-Kriterien', expanded=False):
            crit_rows=[]
            for i,a in enumerate(live_args,1):
                crit_rows.append({'Zeit':time_label(a,i),'Seite':a['side'],'Argument im Wortlaut':a['quote_full'],'Demokratiekriterien':', '.join(a.get('democracy_criteria',[]))})
            st.dataframe(pd.DataFrame(crit_rows), use_container_width=True, hide_index=True)

        live_rows=[]
        for i,a in enumerate(live_args,1):
            live_rows.append({'Zeit':time_label(a,i),'Seite':a['side'],'Sprecher':a['speaker'],'Argument im Wortlaut':a['quote_full'],'Behauptung':a['claim'],'Begründung':a['reason'],'Beleg/Beispiel':a['evidence'],'Sicherheit':a['confidence'],'Demokratiekriterien (intern)':', '.join(a.get('democracy_criteria',[]))})
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
elif mode == 'Vorhandenes Transkript einfügen':
    transcript_input = st.text_area('Transkript', height=260, placeholder='Diskussion hier einfügen …')
else:  # Testmodus
    st.subheader('🧪 Testmodus – Beispiel-Diskussion')
    st.caption('Läuft ohne Mikrofon und ohne Transkriptionskosten: Eine hinterlegte Beispiel-Argumentkette wird direkt analysiert. '
               'Ideal, um Darstellung, PRO/KONTRA, Farbmarkierung und die chronologische Zeitreihenfolge zu prüfen. '
               'Es fallen nur die minimalen Kosten der Analyse an; die Streitfrage wird für den Test automatisch auf das Beispiel gesetzt.')
    st.text_area('Beispiel-Transkript (nur zur Ansicht)', SAMPLE_TRANSCRIPT, height=220, disabled=True)

_btn_label = 'Beispiel-Diskussion auswerten' if mode == TEST_MODE else 'Analysieren'
if mode != 'Live-Mikrofon' and st.button(_btn_label, type='primary', use_container_width=True):
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
        segs = []
        active_question = question
        if mode == 'Audio hochladen':
            with st.spinner('Audio wird transkribiert …'):
                transcript, segs = transcribe_audio(client, uploaded)
        elif mode == TEST_MODE:
            transcript = SAMPLE_TRANSCRIPT
            segs = SAMPLE_SEGMENTS
            active_question = SAMPLE_QUESTION
        else:
            transcript = transcript_input

        with st.spinner('Argumente werden analysiert …'):
            arguments = analyze_transcript(client, active_question, transcript)
        assign_time_markers(arguments, segs, offset_sec=0.0)
        arguments = dedupe_args(arguments)

        st.session_state['transcript'] = transcript
        st.session_state['arguments'] = arguments
        st.session_state['question'] = active_question
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

    st.markdown('### Chronologischer Verlauf (PRO ↔ KONTRA)')
    st.caption('Chat-Ansicht: jedes Argument in einer eigenen Zeile, die Gegenspalte bleibt leer – so ist erkennbar, welches Argument zeitlich zuerst gefallen ist.')
    render_chat_columns(arguments)
    with st.expander('Vollständiges Transkript anzeigen', expanded=False):
        st.text_area('Vollständiges Transkript', transcript, height=400, label_visibility='collapsed')

    with st.expander('Interne Analyse: Demokratie-Kriterien anzeigen', expanded=False):
        criteria_rows = []
        for i, a in enumerate(arguments, 1):
            criteria_rows.append({
                'Zeit': time_label(a, i),
                'Seite': a['side'],
                'Argument im Wortlaut': a['quote_full'],
                'Demokratiekriterien': ', '.join(a.get('democracy_criteria', []))
            })
        st.dataframe(pd.DataFrame(criteria_rows), use_container_width=True, hide_index=True)

    rows = []
    for i, a in enumerate(arguments, 1):
        rows.append({
            'Zeit': time_label(a, i),
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
