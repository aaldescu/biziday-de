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
        # Fetch the feed using requests
        response = requests.get(rss_url)
        response.raise_for_status()  # Check for HTTP errors

        # Parse the feed content with feedparser
        feed = feedparser.parse(response.content)
        articles = [{"title": entry.title, "description": entry.description} for entry in feed.entries]
        return articles

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching the RSS feed: {e}")
        return []

# Function to translate the text using OpenAI GPT (gpt-4o-mini model)
def translate_text(text, level):
    # Build the prompt dynamically based on the language level selected
    if level == 'A1':
        prompt = f"Please translate the following text into German using A1 level vocabulary: {text}"
    elif level == 'A2':
        prompt = f"Please translate the following text into German using A2 level vocabulary: {text}"
    elif level == 'B1':
        prompt = f"Please translate the following text into German using B1 level vocabulary: {text}"
    else:
        return "No level selected."

    try:
        # Using OpenAI client with gpt-4o-mini model to create chat completion
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a German teacher and your goal is to teach me German. My native language is Romanian, and I am proficient in English."},
                {"role": "user", "content": prompt}
            ]
        )
        # Access the translated content properly
        translated_text = completion.choices[0].message.content.strip()
        return translated_text
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit app setup
st.title("News Article Translation App")

# Fetch articles from the RSS feed using requests
articles = fetch_rss_articles()

# Show total number of articles and the current article index
total_articles = len(articles)
if total_articles == 0:
    st.write("No articles found in the RSS feed.")
else:
    st.write(f"Total articles: {total_articles}")

    # Session state to track the current article index
    if 'article_index' not in st.session_state:
        st.session_state.article_index = 0

    # Buttons to switch between articles
    if st.button("Previous Article"):
        if st.session_state.article_index > 0:
            st.session_state.article_index -= 1
    if st.button("Next Article"):
        if st.session_state.article_index < total_articles - 1:
            st.session_state.article_index += 1

    # Display current article index
    current_article_index = st.session_state.article_index + 1
    st.write(f"Reading article {current_article_index} of {total_articles}")

    # Get current article
    current_article = articles[st.session_state.article_index]
    original_title = current_article['title']
    original_description = current_article['description']

    # Show original title and description
    st.subheader("Original Article")
    st.write(f"**Title:** {original_title}")
    st.write(f"**Description:** {original_description}")

    # Select level (A1, A2, B1) for translation
    level = st.radio("Select Translation Level", options=['', 'A1', 'A2', 'B1'], index=0, horizontal=True, help="Please select a translation level.")
    
    if level == '':
        st.write("Please select a translation level to continue.")
    else:
        # Translate title and description based on the selected level
        if st.button("Translate"):
            st.subheader(f"Translated Article (Level {level})")

            # Translated title
            translated_title = translate_text(original_title, level)
            st.write(f"**Translated Title:** {translated_title}")

            # Translated description
            translated_description = translate_text(original_description, level)
            st.write(f"**Translated Description:** {translated_description}")
