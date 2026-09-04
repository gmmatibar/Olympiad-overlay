import streamlit as st
import requests
import chess.pgn
import io
import urllib.parse

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Olimpiada Szachowa OBS Overlay", layout="wide")

# --- STYLE CSS (Przezroczystość, złoty kolor, animacja) ---
st.markdown("""
    <style>
    /* Wymuszenie przezroczystości dla OBS */
    .stApp, .main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
    }
    
    /* Ukrycie standardowych elementów UI Streamlit w samej transmisji (opcjonalne) */
    footer {visibility: hidden;}
    
    /* Stylizacja tabeli wyników */
    .obs-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Arial', sans-serif;
        color: #D3AF37 !important;
        font-size: 26px; /* Zwiększona czcionka dla czytelności na streamie */
        margin-top: 20px;
    }
    .obs-table th {
        border-bottom: 3px solid #D3AF37;
        padding: 15px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .obs-table td {
        border-bottom: 1px solid rgba(211, 175, 55, 0.3);
        padding: 15px;
        text-align: center;
    }
    
    /* Pulsująca kropka dla trwających partii */
    .live-dot {
        height: 18px;
        width: 18px;
        background-color: #ff3333; /* Czerwony kolor akcentujący "NA ŻYWO" */
        border-radius: 50%;
        display: inline-block;
        animation: blink 1.5s infinite;
        vertical-align: middle;
        margin-right: 8px;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.2; }
        100% { opacity: 1; }
    }
    
    /* Panel boczny zostawiamy nieprzezroczysty, żeby łatwo było go obsługiwać */
    [data-testid="stSidebar"] {
        background-color: rgba(30, 30, 30, 0.95) !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNKCJE POBIERAJĄCE DANE ---
@st.cache_data(ttl=30) # Odświeża dane co 30 sekund
def fetch_lichess_data(url):
    try:
        # Parsowanie URL, aby wyciągnąć ID rundy z linku Lichess
        parsed_url = urllib.parse.urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) == 0:
            return []
            
        round_id = path_parts[-1]
        # Usuwamy ewentualny hashtag (np. #teams)
        if '#' in round_id:
            round_id = round_id.split('#')[0]
            
        api_url = f"https://lichess.org/api/broadcast/round/{round_id}.pgn"
        response = requests.get(api_url)
        
        if response.status_code != 200:
            return []
            
        pgn_text = response.text
        pgn_io = io.StringIO(pgn_text)
        
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
    except Exception as e:
        st.sidebar.error(f"Wystąpił błąd podczas pobierania: {e}")
        return []

# --- PANEL BOCZNY (INTERFEJS STEROWANIA) ---
st.sidebar.title("Kreator Nakładki OBS")
st.sidebar.markdown("Skonfiguruj tabelę wyników dla swojej transmisji.")

broadcast_url = st.sidebar.text_input(
    "1. Link do transmisji Lichess", 
    placeholder="np. https://lichess.org/broadcast/.../XJ8g9CkA"
)

country_search = st.sidebar.text_input("2. Wyszukaj kraj (np. Poland)")

if st.sidebar.button("Odśwież dane manualnie"):
    st.cache_data.clear()

# --- GŁÓWNA LOGIKA I WYŚWIETLANIE ---
if broadcast_url and country_search:
    games = fetch_lichess_data(broadcast_url)
    
    if not games:
        st.warning("Nie znaleziono partii. Sprawdź poprawność linku do rundy.")
    else:
        # Filtrowanie partii po wyszukiwanej frazie (sprawdza nazwy zawodników i tagi drużyn)
        search_term = country_search.lower()
        filtered_games = [
            g for g in games 
            if search_term in g['WhiteTeam'].lower() 
            or search_term in g['BlackTeam'].lower()
            or search_term in g['White'].lower()
            or search_term in g['Black'].lower()
        ]
        
        if not filtered_games:
            st.info(f"Brak partii dla wpisanej frazy: {country_search}")
        else:
            # Tworzenie kodu HTML dla tabeli
            html_table = "<table class='obs-table'>"
            html_table += "<tr><th>Białe (⚪)</th><th>Status / Wynik</th><th>Czarne (⚫)</th></tr>"
            
            for g in filtered_games:
                white_player = f"{g['White']} <small>({g['WhiteElo']})</small>" if g['WhiteElo'] else g['White']
                black_player = f"{g['Black']} <small>({g['BlackElo']})</small>" if g['BlackElo'] else g['Black']
                
                # Znak graficzny dla trwającej partii
                if g['Result'] == "*":
                    result_display = "<div class='live-dot'></div> W toku"
                else:
                    result_display = f"<strong>{g['Result']}</strong>"
                
                html_table += f"<tr><td>{white_player}</td><td>{result_display}</td><td>{black_player}</td></tr>"
                
            html_table += "</table>"
            
            # Wstrzyknięcie tabeli do aplikacji
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Instrukcja dla Ciebie z przypomnieniem
            st.sidebar.success("Nakładka gotowa! Ukryj ten panel (strzałką w lewym górnym rogu) przed pokazaniem źródła w OBS.")
else:
    if not broadcast_url:
        st.info("👈 Wpisz adres URL transmisji Lichess w panelu bocznym.")
    elif not country_search:
        st.info("👈 Wpisz nazwę kraju, aby przefiltrować partie.")
