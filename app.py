import streamlit as st
import requests
import chess.pgn
import io
import urllib.parse

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Olimpiada Szachowa OBS Overlay", layout="wide")

# --- BAZA KODÓW KRAJÓW DO FLAG (FLAGCDN) ---
ISO_CODES = {
    "poland": "pl", "polska": "pl", "pol": "pl",
    "sudan": "sd", "sud": "sd",
    "usa": "us", "united states": "us",
    "india": "in", "ind": "in",
    "uzbekistan": "uz", "uzb": "uz",
    "china": "cn", "chn": "cn",
    "armenia": "am", "arm": "am",
    "germany": "de", "ger": "de",
    "ukraine": "ua", "ukr": "ua",
    "azerbaijan": "az", "aze": "az",
    "spain": "es", "esp": "es",
    "france": "fr", "fra": "fr",
    "netherlands": "nl", "ned": "nl",
    "england": "gb-eng", "eng": "gb-eng",
    "hungary": "hu", "hun": "hu",
    "norway": "no", "nor": "no",
    "israel": "il", "isr": "il",
    "georgia": "ge", "geo": "ge",
    "serbia": "rs", "srb": "rs",
    "turkey": "tr", "tur": "tr",
    "romania": "ro", "rou": "ro",
    "greece": "gr", "gre": "gr",
    "italy": "it", "ita": "it",
    "czech republic": "cz", "cze": "cz",
    "slovakia": "sk", "svk": "sk",
    "kazakhstan": "kz", "kaz": "kz",
    "vietnam": "vn", "vie": "vn",
    "brazil": "br", "bra": "br",
    "argentina": "ar", "arg": "ar"
}

def get_flag_img(country_name):
    if not country_name:
        return ""
    
    name_clean = country_name.lower().strip()
    
    # Obsługa dwuliterowych lub trzyliterowych skrótów z PGN
    if len(name_clean) == 2:
        code = name_clean
    else:
        code = ISO_CODES.get(name_clean)
        
    if code:
        # Zabezpieczenie onerror ukrywa ikonę zamiast pokazywać uszkodzony obrazek
        return f'<img src="https://flagcdn.com/w40/{code}.png" onerror="this.style.display=\'none\'" style="vertical-align: middle; margin: 0 8px; height: 22px; border-radius: 3px; display: inline-block;">'
    return ""

# --- STYLE CSS (OBS Overlay) ---
st.markdown("""
    <style>
    .stApp, .main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
    }
    
    footer {visibility: hidden;}
    
    .obs-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Arial', sans-serif;
        color: #D3AF37 !important;
        font-size: 24px;
        margin-top: 10px;
        table-layout: fixed;
    }
    
    .header-row th {
        border-bottom: 3px solid #D3AF37;
        padding: 10px 4px;
        vertical-align: middle;
    }
    
    .country-header {
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .score-header {
        text-align: center;
        background-color: rgba(211, 175, 55, 0.12);
        border-radius: 6px;
        padding: 6px;
    }
    
    .score-title {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.85;
        margin-bottom: 2px;
        font-weight: normal;
    }
    
    .score-val {
        font-size: 32px;
        font-weight: bold;
    }
    
    .obs-table td {
        border-bottom: 1px solid rgba(211, 175, 55, 0.25);
        padding: 10px 6px;
        vertical-align: middle;
    }
    
    .color-col {
        width: 6%;
        text-align: center;
        font-size: 20px;
    }
    
    .player-left {
        width: 34%;
        text-align: left;
    }
    
    .score-col {
        width: 20%;
        text-align: center;
        font-weight: bold;
        font-size: 26px;
    }
    
    .player-right {
        width: 34%;
        text-align: right;
    }
    
    .live-dot {
        height: 16px;
        width: 16px;
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
country_search = st.sidebar.text_input("2. Wyszukaj kraj (np. Poland)")

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
                    left_player, left_elo, left_color = g['White'], g['WhiteElo'], "⚪"
                    right_player, right_elo, right_color = g['Black'], g['BlackElo'], "⚫"
                    
                    if g['Result'] == '1-0': board_score = "1 - 0"
                    elif g['Result'] == '0-1': board_score = "0 - 1"
                    elif g['Result'] in ['1/2-1/2', '0.5-0.5', '½-½']: board_score = "½ - ½"
                    else: board_score = "<div class='live-dot'></div>"
                else:
                    left_player, left_elo, left_color = g['Black'], g['BlackElo'], "⚫"
                    right_player, right_elo, right_color = g['White'], g['WhiteElo'], "⚪"
                    
                    if g['Result'] == '1-0': board_score = "0 - 1"
                    elif g['Result'] == '0-1': board_score = "1 - 0"
                    elif g['Result'] in ['1/2-1/2', '0.5-0.5', '½-½']: board_score = "½ - ½"
                    else: board_score = "<div class='live-dot'></div>"
                
                left_str = f"{left_player} <small>({left_elo})</small>" if left_elo else left_player
                right_str = f"{right_player} <small>({right_elo})</small>" if right_elo else right_player
                
                rows_html += f"<tr><td class='color-col'>{left_color}</td><td class='player-left'>{left_str}</td><td class='score-col'>{board_score}</td><td class='player-right'>{right_str}</td><td class='color-col'>{right_color}</td></tr>"
            
            # Nagłówek ze statycznymi szerokościami kolumn i opisem wyniku
            html_table = f"""<table class='obs-table'>
                <tr class='header-row'>
                    <th colspan='2' class='country-header'>{get_flag_img(left_country)} {left_country}</th>
                    <th class='score-header'>
                        <div class='score-title'>Aktualny wynik meczu</div>
                        <div class='score-val'>{score_str}</div>
                    </th>
                    <th colspan='2' class='country-header'>{right_country} {get_flag_img(right_country)}</th>
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
