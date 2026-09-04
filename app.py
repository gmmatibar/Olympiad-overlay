import streamlit as st
import requests
import chess.pgn
import io
import urllib.parse

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Olimpiada Szachowa OBS Overlay", layout="wide")

# --- BAZA KODÓW KRAJÓW DO FLAG (FIDE / IOC / ANGIELSKIE / POLSKIE) ---
ISO_CODES = {
    # Kody 3-literowe FIDE / MOK
    "pol": "pl", "ger": "de", "fra": "fr", "esp": "es", "ita": "it", "ukr": "ua",
    "usa": "us", "chn": "cn", "ind": "in", "uzb": "uz", "cze": "cz", "svk": "sk",
    "hun": "hu", "rou": "ro", "srb": "rs", "cro": "hr", "slo": "si", "gre": "gr",
    "tur": "tr", "isr": "il", "egy": "eg", "rsa": "za", "bra": "br", "chi": "cl",
    "col": "co", "mex": "mx", "cub": "cu", "can": "ca", "kor": "kr", "jpn": "jp",
    "kaz": "kz", "mgl": "mn", "vie": "vn", "phi": "ph", "ina": "id", "sgp": "sg",
    "sud": "sd", "nor": "no", "swe": "se", "fin": "fi", "den": "dk", "eng": "gb-eng",
    "sco": "gb-scot", "wal": "gb-wales", "iri": "ir", "irq": "iq", "syr": "sy",
    "arm": "am", "aze": "az", "geo": "ge", "mda": "md", "ltu": "lt", "lat": "lv",
    "est": "ee", "blr": "by", "bul": "bg", "mkd": "mk", "mne": "me", "bih": "ba",
    "ned": "nl", "por": "pt", "aut": "at", "sui": "ch", "bel": "be", "dza": "dz",
    "arg": "ar", "aus": "au", "ban": "bd", "mya": "mm", "kos": "xk", "per": "pe",
    "ven": "ve", "ecu": "ec", "bol": "bo", "par": "py", "uru": "uy", "nzl": "nz",
    
    # Nazwy pełne (Angielskie i Polskie)
    "poland": "pl", "polska": "pl", "germany": "de", "niemcy": "de",
    "france": "fr", "francja": "fr", "spain": "es", "hiszpania": "es",
    "italy": "it", "włochy": "it", "ukraine": "ua", "ukraina": "ua",
    "united states": "us", "stany zjednoczone": "us",
    "china": "cn", "chiny": "cn", "india": "in", "indie": "in",
    "uzbekistan": "uz", "czech republic": "cz", "czechia": "cz", "czechy": "cz",
    "slovakia": "sk", "słowacja": "sk", "hungary": "hu", "węgry": "hu",
    "romania": "ro", "rumunia": "ro", "serbia": "rs", "croatia": "hr", "chorwacja": "hr",
    "slovenia": "si", "słowenia": "si", "greece": "gr", "grecja": "gr",
    "turkey": "tr", "turcja": "tr", "israel": "il", "izrael": "il",
    "sudan": "sd", "norway": "no", "norwegia": "no", "sweden": "se", "szwecja": "se",
    "finland": "fi", "finlandia": "fi", "denmark": "dk", "dania": "dk",
    "england": "gb-eng", "anglia": "gb-eng", "armenia": "am", "azerbaijan": "az", "azerbejdżan": "az",
    "georgia": "ge", "gruzja": "ge", "netherlands": "nl", "holandia": "nl",
    "kazakhstan": "kz", "kazachstan": "kz", "brazil": "br", "brazylia": "br",
    "argentina": "ar", "argentyna": "ar", "peru": "pe"
}

def get_flag_img(country_name):
    if not country_name:
        return ""
    name_clean = country_name.lower().strip()
    code = name_clean if len(name_clean) == 2 else ISO_CODES.get(name_clean)
    if code:
        return f'<img src="https://flagcdn.com/w40/{code}.png" onerror="this.style.display=\'none\'" style="vertical-align: middle; margin: 0 6px; height: 20px; border-radius: 2px; display: inline-block;">'
    return ""

def shorten_name(name):
    if not name:
        return ""
    if len(name) > 20 and ',' in name:
        parts = name.split(',', 1)
        surname = parts[0].strip()
        firstname = parts[1].strip()
        if firstname:
            return f"{surname}, {firstname[0].upper()}."
        return surname
    return name

# --- STYLE CSS (OBS Overlay) ---
st.markdown("""
    <style>
    .stApp, .main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
    }
    
    footer {visibility: hidden;}
    
    .obs-table {
        width: 100% !important;
        border-collapse: collapse !important;
        font-family: 'Arial', sans-serif !important;
        color: #D3AF37 !important;
        font-size: 22px !important;
        margin-top: 5px !important;
        table-layout: fixed !important;
    }
    
    .title-row th {
        text-align: center !important;
        font-size: 14px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        padding: 6px 0 2px 0 !important;
        opacity: 0.9 !important;
        border-bottom: 1px solid rgba(211, 175, 55, 0.25) !important;
    }
    
    .country-edge {
        border-bottom: 3px solid #D3AF37 !important;
    }
    
    .country-left-header {
        text-align: left !important;
        font-size: 26px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        padding: 10px 0 10px 16px !important;
        border-bottom: 3px solid #D3AF37 !important;
        vertical-align: middle !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    .country-right-header {
        text-align: right !important;
        font-size: 26px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        padding: 10px 16px 10px 0 !important;
        border-bottom: 3px solid #D3AF37 !important;
        vertical-align: middle !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    .match-score-cell {
        text-align: center !important;
        font-size: 28px !important;
        font-weight: bold !important;
        padding: 10px 0 !important;
        border-bottom: 3px solid #D3AF37 !important;
        background-color: rgba(211, 175, 55, 0.15) !important;
        vertical-align: middle !important;
        border-left: 1px solid rgba(211, 175, 55, 0.25) !important;
        border-right: 1px solid rgba(211, 175, 55, 0.25) !important;
        white-space: nowrap !important;
    }
    
    .obs-table td {
        border-bottom: 1px solid rgba(211, 175, 55, 0.25) !important;
        padding: 12px 0 !important;
        vertical-align: middle !important;
    }
    
    .color-col {
        text-align: center !important;
        font-size: 18px !important;
    }
    
    .player-left {
        text-align: left !important;
        padding-left: 16px !important;
        padding-right: 8px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        border-right: 1px solid rgba(211, 175, 55, 0.25) !important;
    }
    
    .score-col {
        text-align: center !important;
        font-weight: bold !important;
        font-size: 24px !important;
        border-right: 1px solid rgba(211, 175, 55, 0.25) !important;
        white-space: nowrap !important;
    }
    
    .player-right {
        text-align: right !important;
        padding-right: 16px !important;
        padding-left: 8px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    .live-dot {
        height: 14px;
        width: 14px;
        background-color: #ff3333;
        border-radius: 50%;
        display: inline-block;
        animation: blink 1.5s infinite;
        vertical-align: middle;
    }
    
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.2; }
        100% { opacity: 1; }
    }
    
    [data-testid="stSidebar"] {
        background-color: rgba(30, 30, 30, 0.95) !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- POBIERANIE DANYCH ---
@st.cache_data(ttl=15)
def fetch_lichess_data(url):
    try:
        parsed_url = urllib.parse.urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if not path_parts:
            return []
            
        round_id = path_parts[-1].split('#')[0]
        api_url = f"https://lichess.org/api/broadcast/round/{round_id}.pgn"
        response = requests.get(api_url)
        
        if response.status_code != 200:
            return []
            
        pgn_io = io.StringIO(response.text)
        games = []
        
        while True:
            headers = chess.pgn.read_headers(pgn_io)
            if headers is None:
                break
                
            games.append({
                "White": headers.get("White", "Nieznany"),
                "Black": headers.get("Black", "Nieznany"),
                "WhiteElo": headers.get("WhiteElo", ""),
                "BlackElo": headers.get("BlackElo", ""),
                "WhiteTeam": headers.get("WhiteTeam", ""),
                "BlackTeam": headers.get("BlackTeam", ""),
                "Result": headers.get("Result", "*")
            })
        return games
    except Exception:
        return []

# --- PANEL BOCZNY ---
st.sidebar.title("Kreator Nakładki OBS")
broadcast_url = st.sidebar.text_input("1. Link do transmisji Lichess", placeholder="https://lichess.org/broadcast/.../XJ8g9CkA")
country_search = st.sidebar.text_input("2. Wyszukaj kraj (np. Peru)")

if st.sidebar.button("Odśwież dane"):
    st.cache_data.clear()

# --- LOGIKA WYŚWIETLANIA ---
if broadcast_url and country_search:
    games = fetch_lichess_data(broadcast_url)
    
    if games:
        search_term = country_search.lower()
        
        filtered_games = [
            g for g in games 
            if search_term in g['WhiteTeam'].lower() 
            or search_term in g['BlackTeam'].lower()
            or search_term in g['White'].lower()
            or search_term in g['Black'].lower()
        ]
        
        if filtered_games:
            board1 = filtered_games[0]
            left_country = board1['WhiteTeam']
            right_country = board1['BlackTeam']
            
            match_games = [
                g for g in games 
                if (g['WhiteTeam'] == left_country and g['BlackTeam'] == right_country) or
                   (g['WhiteTeam'] == right_country and g['BlackTeam'] == left_country)
            ]
            
            left_score = 0.0
            right_score = 0.0
            
            for g in match_games:
                res = g['Result']
                if res == '1-0':
                    if g['WhiteTeam'] == left_country: left_score += 1.0
                    else: right_score += 1.0
                elif res == '0-1':
                    if g['WhiteTeam'] == left_country: right_score += 1.0
                    else: left_score += 1.0
                elif res in ['1/2-1/2', '0.5-0.5', '½-½']:
                    left_score += 0.5
                    right_score += 0.5
            
            def fmt_score(s):
                return str(int(s)) if s.is_integer() else str(s)
                
            score_str = f"{fmt_score(left_score)} - {fmt_score(right_score)}"
            
            rows_html = ""
            for g in match_games:
                if g['WhiteTeam'] == left_country:
                    left_player = shorten_name(g['White'])
                    left_elo = g['WhiteElo']
                    left_color = "⚪"
                    
                    right_player = shorten_name(g['Black'])
                    right_elo = g['BlackElo']
                    right_color = "⚫"
                    
                    if g['Result'] == '1-0': board_score = "1 - 0"
                    elif g['Result'] == '0-1': board_score = "0 - 1"
                    elif g['Result'] in ['1/2-1/2', '0.5-0.5', '½-½']: board_score = "½ - ½"
                    else: board_score = "<div class='live-dot'></div>"
                else:
                    left_player = shorten_name(g['Black'])
                    left_elo = g['BlackElo']
                    left_color = "⚫"
                    
                    right_player = shorten_name(g['White'])
                    right_elo = g['WhiteElo']
                    right_color = "⚪"
                    
                    if g['Result'] == '1-0': board_score = "0 - 1"
                    elif g['Result'] == '0-1': board_score = "1 - 0"
                    elif g['Result'] in ['1/2-1/2', '0.5-0.5', '½-½']: board_score = "½ - ½"
                    else: board_score = "<div class='live-dot'></div>"
                
                left_str = f"{left_player} <small>({left_elo})</small>" if left_elo else left_player
                right_str = f"{right_player} <small>({right_elo})</small>" if right_elo else right_player
                
                rows_html += f"<tr><td class='color-col'>{left_color}</td><td class='player-left'>{left_str}</td><td class='score-col'>{board_score}</td><td class='player-right'>{right_str}</td><td class='color-col'>{right_color}</td></tr>"
            
            # Wymuszona ścisła siatka HTML dla 100% symetrii
            html_table = f"""<table class='obs-table'>
                <colgroup>
                    <col style='width: 45px;'>
                    <col style='width: calc(50% - 125px);'>
                    <col style='width: 160px;'>
                    <col style='width: calc(50% - 125px);'>
                    <col style='width: 45px;'>
                </colgroup>
                <tr class='title-row'>
                    <th colspan='5'>Aktualny wynik meczu</th>
                </tr>
                <tr>
                    <th class='country-edge'></th>
                    <th class='country-left-header' style='text-align: left !important;'>{left_country} {get_flag_img(left_country)}</th>
                    <th class='match-score-cell' style='text-align: center !important;'>{score_str}</th>
                    <th class='country-right-header' style='text-align: right !important;'>{get_flag_img(right_country)} {right_country}</th>
                    <th class='country-edge'></th>
                </tr>
                {rows_html}
            </table>"""
            
            st.markdown(html_table, unsafe_allow_html=True)
            st.sidebar.success("Tabela zaktualizowana!")
        else:
            st.info(f"Brak meczu dla frazy: {country_search}")
    else:
        st.warning("Nie udało się pobrać danych.")
else:
    st.info("👈 Wpisz link do transmisji oraz nazwę kraju w panelu bocznym.")
