import streamlit as st
import requests
import feedparser
import openai
import hashlib
import sqlite3
from streamlit_cookies_manager import EncryptedCookieManager

# Initialize OpenAI client
openai.api_key = st.secrets["openai"]["api_key"]

# Initialize connection to SQLite database
def init_db():
    conn = sqlite3.connect('user_db.sqlite')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# Initialize Cookies Manager
cookies = EncryptedCookieManager(
    prefix="your_prefix_name",  # Replace with your preferred prefix
    password=st.secrets["cookies"]["password"],  # Replace with a strong password
)

if not cookies.ready():
    st.stop()

# User Authentication Functions
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def add_user(username, password):
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, make_hashes(password)))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("Utilizatorul există deja.")

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    data = c.fetchone()
    if data and check_hashes(password, data[1]):
        cookies.set("username", username)
        return True
    return False

def is_logged_in():
    return cookies.get("username") is not None

# News Translation Functions
def fetch_rss_articles(rss_url):
    try:
        response = requests.get(rss_url)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        articles = [{"title": entry.title, "description": entry.description} for entry in feed.entries]
        return articles
    except requests.exceptions.RequestException as e:
        st.error(f"Eroare la preluarea feed-ului RSS: {e}")
        return []

def translate_text(text, level):
    prompt = f"Esti un profesor de germana , tradu-mi si rescrie textul cu cuvinte adaptate pentru nivel de germana {level}: {text}"

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Esti un profesor de germana care vrea sa ma invete germana."},
                {"role": "user", "content": prompt}
            ]
        )
        translated_text = completion.choices[0].message['content'].strip()
        return translated_text
    except Exception as e:
        st.error(f"Eroare: {str(e)}")
        return ""

# Main App
def main():
    cookies.load()
    st.title("Aplicație de exersat germana cu știri din România")

    menu = ["Acasă", "Autentificare", "Înregistrare"]
    choice = st.sidebar.selectbox("Meniu", menu)

    if choice == "Acasă":
        st.subheader("Bine ați venit!")
        st.write("Vă rugăm să vă autentificați pentru a accesa traducerea știrilor.")

    elif choice == "Autentificare":
        st.sidebar.subheader("Autentificare")

        username = st.sidebar.text_input("Nume utilizator")
        password = st.sidebar.text_input("Parolă", type='password')

        if st.sidebar.button("Autentificare"):
            if login_user(username, password):
                cookies.save()
                st.success(f"Autentificat ca {username}")
                st.experimental_rerun()
            else:
                st.warning("Autentificare eșuată")

    elif choice == "Înregistrare":
        st.subheader("Creați un cont nou")

        new_user = st.text_input("Nume utilizator")
        new_password = st.text_input("Parolă", type='password')

        if st.button("Înregistrare"):
            add_user(new_user, new_password)
            st.success("Cont creat cu succes!")
            st.info("Mergeți la pagina de autentificare pentru a vă conecta")

    # Main app logic (only accessible when logged in)
    if is_logged_in():
        st.sidebar.success(f"Autentificat ca: {cookies.get('username')}")
        if st.sidebar.button("Deconectare"):
            cookies.delete("username")
            cookies.save()
            st.experimental_rerun()

        # News Translation App Logic
        st.sidebar.header("Opțiuni")

        # Source selector in sidebar
        source = st.sidebar.radio("Selectați Sursa de Știri", options=['Biziday', 'Profit.ro'], index=0)

        # Dictionary to map source names to URLs
        source_urls = {
            'Biziday': "https://www.biziday.ro/feed/",
            'Profit.ro': "https://www.profit.ro/rss"
        }

        # Level selector in sidebar
        level = st.sidebar.radio("Selectați Nivelul de Traducere", options=['Începător', 'Intermediar', 'Avansat'], index=0, help="Vă rugăm să selectați un nivel de traducere.")

        # Fetch articles from the selected RSS feed
        articles = fetch_rss_articles(source_urls[source])

        # Show total number of articles and the current article index
        total_articles = len(articles)
        if total_articles == 0:
            st.write("Nu s-au găsit articole în feed-ul RSS.")
        else:
            st.sidebar.write(f"Total articole: {total_articles}")

            # Session state to track the current article index
            if 'article_index' not in st.session_state:
                st.session_state.article_index = 0

            # Buttons to switch between articles in sidebar
            if st.sidebar.button("Articolul Anterior"):
                if st.session_state.article_index > 0:
                    st.session_state.article_index -= 1
            if st.sidebar.button("Articolul Următor"):
                if st.session_state.article_index < total_articles - 1:
                    st.session_state.article_index += 1

            # Display current article index in sidebar
            current_article_index = st.session_state.article_index + 1
            st.sidebar.write(f"Citirea articolului {current_article_index} din {total_articles}")

            # Get current article
            current_article = articles[st.session_state.article_index]
            original_title = current_article['title']
            original_description = current_article['description']

            # Translate button in sidebar
            if st.sidebar.button("Traducere"):
                st.subheader(f"Articol Tradus (Nivel: {level})")

                # Translated title
                translated_title = translate_text(original_title, level)
                st.write(f"**Titlu Tradus:** {translated_title}")

                # Translated description
                translated_description = translate_text(original_description, level)
                st.write(f"**Descriere Tradusă:** {translated_description}")

                # Option to display original article parts
                show_original = st.sidebar.checkbox("Afișează articolul original")
                if show_original:
                    st.subheader("Articol Original")
                    st.write(f"**Titlu:** {original_title}")
                    st.write(f"**Descriere:** {original_description}")
            else:
                st.write("Apăsați butonul 'Traducere' din bara laterală pentru a vedea articolul tradus.")

if __name__ == '__main__':
    main()