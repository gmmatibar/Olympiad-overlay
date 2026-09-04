import streamlit as st
import requests
import chess.pgn
import io
import urllib.parse

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Olimpiada Szachowa OBS Overlay", layout="wide")

# --- BAZA FLAG DLA REPREZENTACJI ---
COUNTRY_FLAGS = {
    "poland": "🇵🇱", "polska": "🇵🇱",
    "usa": "🇺🇸", "united states": "🇺🇸",
    "india": "🇮🇳", "uzbekistan": "🇺🇿",
    "china": "🇨🇳", "armenia": "🇦🇲",
    "germany": "🇩🇪", "ukraine": "🇺🇦",
    "azerbaijan": "🇦🇿", "spain": "🇪🇸",
    "france": "🇫🇷", "netherlands": "🇳🇱",
    "england": "🇬🇧", "hungary": "🇭🇺",
    "norway": "🇳🇴", "israel": "🇮🇱",
    "georgia": "🇬🇪", "serbia": "🇷🇸",
    "turkey": "🇹🇷", "romania": "🇷🇴",
    "greece": "🇬🇷", "italy": "🇮🇹",
    "czech republic": "🇨🇿", "slovakia": "🇸🇰",
    "kazakhstan": "🇰🇿", "vietnam": "🇻🇳",
    "brazil": "🇧🇷", "argentina": "🇦🇷"
}

def get_flag(country_name):
    if not country_name:
        return "🏳️"
    name_clean = country_name.lower().strip()
    return COUNTRY_FLAGS.get(name_clean, "🏳️")

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
    }
    
    /* Nagłówek Meczu */
    .header-row th {
        border-bottom: 3px solid #D3AF37;
        padding: 12px;
        font-size: 32px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .country-left {
        text-align: left;
        width: 40%;
    }
    
    .match-score {
        text-align: center;
        width: 20%;
        font-size: 36px;
        background-color: rgba(211, 175, 55, 0.15);
        border-radius: 8px;
    }
    
    .country-right {
        text-align: right;
        width: 40%;
    }
    
    /* Wiersze Zawodników */
    .obs-table td {
        border-bottom: 1px solid rgba(211, 175, 55, 0.25);
        padding: 12px 8px;
    }
    
    .color-col {
        width: 5%;
        text-align: center;
        font-size: 20px;
    }
    
    .player-left {
        width: 35%;
        text-align: left;
    }
    
    .score-col {
        width: 20%;
        text-align: center;
        font-weight: bold;
        font-size: 26px;
    }
    
    .player-right {
        width: 35%;
        text-align: right;
    }
    
    /* Animowana kropka trwającej partii */
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

# --- POBIERANIE DANE Z LICHESS ---
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

# --- PRETWORZENIE I WYŚWIETLENIE MECZU ---
if broadcast_url and country_search:
    games = fetch_lichess_data(broadcast_url)
    
    if games:
        search_term = country_search.lower()
        
        # Filtrowanie partii należących do szukanego meczu
        filtered_games = [
            g for g in games 
            if search_term in g['WhiteTeam'].lower() 
            or search_term in g['BlackTeam'].lower()
            or search_term in g['White'].lower()
            or search_term in g['Black'].lower()
        ]
        
        if filtered_games:
            # Pierwsza szachownica wyznacza układy stron
            board1 = filtered_games[0]
            left_country = board1['WhiteTeam']
            right_country = board1['BlackTeam']
            
            # Pobranie kompletnych partii tego meczu
            match_games = [
                g for g in games 
                if (g['WhiteTeam'] == left_country and g['BlackTeam'] == right_country) or
                   (g['WhiteTeam'] == right_country and g['BlackTeam'] == left_country)
            ]
            
            # Zliczanie wyników meczu (tylko ukończone partie)
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
            
            # Budowa Tabeli HTML
            html_table = f"""
            <table class='obs-table'>
                <tr class='header-row'>
                    <th colspan='2' class='country-left'>{get_flag(left_country)} {left_country}</th>
                    <th class='match-score'>{score_str}</th>
                    <th colspan='2' class='country-right'>{right_country} {get_flag(right_country)}</th>
                </tr>
            """
            
            for g in match_games:
                # Przypisanie zawodników do stałych kolumn (Lewy vs Prawy Kraj)
                if g['WhiteTeam'] == left_country:
                    left_player = g['White']
                    left_elo = g['WhiteElo']
                    left_color = "⚪"
                    
                    right_player = g['Black']
                    right_elo = g['BlackElo']
                    right_color = "⚫"
                    
                    if g['Result'] == '1-0': board_score = "1 - 0"
                    elif g['Result'] == '0-1': board_score = "0 - 1"
                    elif g['Result'] in ['1/2-1/2', '0.5-0.5', '½-½']: board_score = "½ - ½"
                    else: board_score = "<div class='live-dot'></div>"
                else:
                    left_player = g['Black']
                    left_elo = g['BlackElo']
                    left_color = "⚫"
                    
                    right_player = g['White']
                    right_elo = g['WhiteElo']
                    right_color = "⚪"
                    
                    if g['Result'] == '1-0': board_score = "0 - 1"
                    elif g['Result'] == '0-1': board_score = "1 - 0"
                    elif g['Result'] in ['1/2-1/2', '0.5-0.5', '½-½']: board_score = "½ - ½"
                    else: board_score = "<div class='live-dot'></div>"
                
                left_str = f"{left_player} <small>({left_elo})</small>" if left_elo else left_player
                right_str = f"{right_player} <small>({right_elo})</small>" if right_elo else right_player
                
                html_table += f"""
                <tr>
                    <td class='color-col'>{left_color}</td>
                    <td class='player-left'>{left_str}</td>
                    <td class='score-col'>{board_score}</td>
                    <td class='player-right'>{right_str}</td>
                    <td class='color-col'>{right_color}</td>
                </tr>
                """
                
            html_table += "</table>"
            st.markdown(html_table, unsafe_allow_html=True)
            st.sidebar.success("Tabela zaktualizowana!")
        else:
            st.info(f"Brak meczu dla frazy: {country_search}")
    else:
        st.warning("Nie udało się pobrać danych z tego linku.")
else:
    st.info("👈 Wpisz link do transmisji oraz nazwę kraju w panelu bocznym.")
