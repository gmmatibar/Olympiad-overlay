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
    code = name_clean if len(name_clean) == 2 else ISO_CODES.get(name_clean)
    if code:
        return f'<img src="https://flagcdn.com/w40/{code}.png" onerror="this.style.display=\'none\'" style="vertical-align: middle; margin: 0 8px; height: 22px; border-radius: 2px; display: inline-block;">'
    return ""

def shorten_name(name):
    if not name:
        return ""
    # Skracanie imienia tylko wtedy, gdy nazwisko i imię przekraczają 20 znaków
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
    
    /* Sztywny układ tabeli z włączonymi pionowymi liniami siatki */
    .obs-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Arial', sans-serif;
        color: #D3AF37 !important;
        font-size: 22px;
        margin-top: 5px;
        table-layout: fixed !important;
    }
    
    /* Wiersz górny: Aktualny wynik meczu */
    .title-row th {
        text-align: center;
        font-size: 14px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 6px 0 2px 0;
        opacity: 0.9;
        border-bottom: 1px solid rgba(211, 175, 55, 0.25);
    }
    
    /* Puste narożniki nagłówka dla zachowania kolumn z kropkami */
    .country-edge {
        border-bottom: 3px solid #D3AF37;
    }
    
    /* Nagłówki Państw nad nazwiskami */
    .country-left-header {
        text-align: left;
        font-size: 26px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 10px 0 10px 16px;
        border-bottom: 3px solid #D3AF37;
        vertical-align: middle;
    }
    
    .country-right-header {
        text-align: right;
        font-size: 26px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 10px 16px 10px 0;
        border-bottom: 3px solid #D3AF37;
        vertical-align: middle;
    }
    
    /* Główny wynik meczu w tej samej kolumnie co wyniki partii */
    .match-score-cell {
        text-align: center;
        font-size: 30px;
        font-weight: bold;
        padding: 10px 0;
        border-bottom: 3px solid #D3AF37;
        background-color: rgba(211, 175, 55, 0.15);
        vertical-align: middle;
        border-left: 1px solid rgba(211, 175, 55, 0.25);
        border-right: 1px solid rgba(211, 175, 55, 0.25);
    }
    
    /* Wiersze z wynikami */
    .obs-table td {
        border-bottom: 1px solid rgba(211, 175, 55, 0.25);
        padding: 12px 0;
        vertical-align: middle;
    }
    
    /* Wąskie kolumny kulek kolorów */
    .color-col {
        text-align: center;
        font-size: 18px;
    }
    
    .player-left {
        text-align: left;
        padding-left: 16px !important;
        padding-right: 8px !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        border-right: 1px solid rgba(211, 175, 55, 0.25);
    }
    
    .score-col {
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        border-right: 1px solid rgba(211, 175, 55, 0.25);
    }
    
    .player-right {
        text-align: right;
        padding-right: 16px !important;
        padding-left: 8px !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
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
            
            # Bezpośrednie wykorzystanie 5 kolumn we wszystkich wierszach tabeli
            html_table = f"""<table class='obs-table'>
                <colgroup>
                    <col style='width: 35px;'>
                    <col style='width: auto;'>
                    <col style='width: 130px;'>
                    <col style='width: auto;'>
                    <col style='width: 35px;'>
                </colgroup>
                <tr class='title-row'>
                    <th colspan='5'>Aktualny wynik meczu</th>
                </tr>
                <tr>
                    <th class='country-edge'></th>
                    <th class='country-left-header'>{get_flag_img(left_country)} {left_country}</th>
                    <th class='match-score-cell'>{score_str}</th>
                    <th class='country-right-header'>{right_country} {get_flag_img(right_country)}</th>
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
