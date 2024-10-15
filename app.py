import streamlit as st
import requests
import feedparser
from openai import OpenAI

# Initialize the OpenAI client using the key from Streamlit secrets
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Function to fetch the RSS feed using requests and parse it with feedparser
def fetch_rss_articles():
    rss_url = "https://www.biziday.ro/feed/"
    
    try:
        response = requests.get(rss_url)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        articles = [{"title": entry.title, "description": entry.description} for entry in feed.entries]
        return articles
    except requests.exceptions.RequestException as e:
        st.error(f"Eroare la preluarea feed-ului RSS: {e}")
        return []

# Function to translate the text using OpenAI GPT (gpt-4o-mini model)
def translate_text(text, level):
    prompt = f"Esti un profesor de germana , tradu-mi si rescrie textul cu cuvinte adaptate pentru nivel de germana {level}: {text}"

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Esti un profesor de germana care vrea sa ma invete germana."},
                {"role": "user", "content": prompt}
            ]
        )
        translated_text = completion.choices[0].message.content.strip()
        return translated_text
    except Exception as e:
        return f"Eroare: {str(e)}"

# Streamlit app setup
st.title("Aplicație de Traducere a Știrilor")

# Updated level selector with new options
level = st.radio("Selectați Nivelul de Traducere", options=['Începător', 'Intermediar', 'Avansat'], index=0, horizontal=True, help="Vă rugăm să selectați un nivel de traducere.")

# Fetch articles from the RSS feed
articles = fetch_rss_articles()

# Show total number of articles and the current article index
total_articles = len(articles)
if total_articles == 0:
    st.write("Nu s-au găsit articole în feed-ul RSS.")
else:
    st.write(f"Total articole: {total_articles}")

    # Session state to track the current article index
    if 'article_index' not in st.session_state:
        st.session_state.article_index = 0

    # Buttons to switch between articles
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Articolul Anterior"):
            if st.session_state.article_index > 0:
                st.session_state.article_index -= 1
    with col2:
        if st.button("Articolul Următor"):
            if st.session_state.article_index < total_articles - 1:
                st.session_state.article_index += 1

    # Display current article index
    current_article_index = st.session_state.article_index + 1
    st.write(f"Citirea articolului {current_article_index} din {total_articles}")

    # Get current article
    current_article = articles[st.session_state.article_index]
    original_title = current_article['title']
    original_description = current_article['description']

    # Translate title and description
    if st.button("Traducere"):
        st.subheader(f"Articol Tradus (Nivel: {level})")

        # Translated title
        translated_title = translate_text(original_title, level)
        st.write(f"**Titlu Tradus:** {translated_title}")

        # Translated description
        translated_description = translate_text(original_description, level)
        st.write(f"**Descriere Tradusă:** {translated_description}")

        # Option to display original article
        show_original = st.checkbox("Afișează articolul original")
        if show_original:
            st.subheader("Articol Original")
            st.write(f"**Titlu:** {original_title}")
            st.write(f"**Descriere:** {original_description}")
    else:
        st.write("Apăsați butonul 'Traducere' pentru a vedea articolul tradus.")