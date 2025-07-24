import streamlit as st
import pandas as pd
import requests
import pickle
from difflib import get_close_matches
import html

import os

try:
    import gdown
except ImportError:
    os.system("pip install gdown")
    import gdown

def download_from_drive(file_id, output_path):
    if not os.path.exists(output_path):
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output_path, quiet=False)

# Load data
anime_df = pd.read_csv("anime.csv") 
anime_df["name"] = anime_df["name"].apply(html.unescape)
anime_df["genre"] = anime_df["genre"].fillna("").apply(html.unescape)

download_from_drive("1Q_0FZCFK1dpLzCbcHoP4GE2TfrSwTNGI", "cos_sim_df.pkl")
cos_sim_df = pickle.load(open("cos_sim_df.pkl", "rb"))

download_from_drive("1kuRuDocAFmN8v1Sd2r-kS2mSXlepNuEm", "pivot_table.pkl")
pivot_table = pickle.load(open("pivot_table.pkl", "rb"))

download_from_drive("1uXZcvA33nxhVm5kL_Xg1hNo-P1i_ErBg", "rating.csv")
rating_df = pd.read_csv("rating.csv")

anime_names = anime_df["name"].dropna().unique().tolist()

top_100_df = pd.read_csv("top_100_df.csv")
top_100_df["name"] = top_100_df["name"].apply(html.unescape)

# --- Streamlit Config ---
st.set_page_config(page_title="🎌 Anime Recommender", layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: #ff4b4b;'>🎌 Anime Recommendation System</h1>",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        .anime-card:hover {
            background-color: #f0f2f6;
            transition: background-color 0.3s ease;
        }
        .stTextInput>div>div>input {
            border-radius: 10px;
            padding: 10px;
        }
        .stButton>button {
            border-radius: 10px;
            padding: 0.5em 2em;
            background-color: #add8e6;  /* 🌤 Light Blue */
            color: black;
            font-weight: bold;
            border: 1px solid #8ab6d6;
        }
        .stButton>button:hover {
            background-color: #cbe7f6;  /* Softer on hover */
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExa3FjMWY4OGllN2FyMmpwMHB1a2V2Yzd2dTNhdG56ODZhc2Fhc2Z0biZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/C3brYLms1bhv2/giphy.gif", use_container_width=True)
    st.markdown("### 🔍 How it works")
    st.markdown("Enter any anime title. We'll find the most similar anime based on collaborative filtering.")
    st.markdown("Made with ❤️ using Streamlit and Jikan API.")
    st.markdown("Creator: _Sukrat Singh_")

# --- Anime Image Fetching ---
@st.cache_data(show_spinner=False)
def fetch_image(anime_title):
    try:
        url = f"https://api.jikan.moe/v4/anime?q={anime_title}&limit=1"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data["data"]:
            return data["data"][0]["images"]["jpg"]["large_image_url"]
        else:
            return None
    except:
        return None

# --- Recommend Function ---
def recommend(anime_name, top_n=15):
    anime_name = anime_name.strip()

    if anime_name not in cos_sim_df.columns:
        close_match = get_close_matches(anime_name, cos_sim_df.columns, n=1)
        if close_match:
            anime_name = close_match[0]
        else:
            return f"'{anime_name}' not found in anime list.", None

    similar_animes = cos_sim_df[anime_name].sort_values(ascending=False).iloc[1:top_n+1]
    result_df = pd.DataFrame({
        "Recommended Anime": similar_animes.index,
        "Similarity Score": similar_animes.values
    })
    return anime_name, result_df



tab1, tab2 = st.tabs(["🎯 Recommendations", "📈 Top 100 Anime"])

with tab1:
    # --- Input Section ---
    st.markdown("#### 🔎 Search for an Anime")
    col1, col2 = st.columns([2, 1])
    with col1:
        anime_input = st.selectbox("Choose an anime (or type to search):", anime_names, index=None, placeholder="e.g. Naruto")
    with col2:
        manual_input = st.text_input("Or enter manually:", placeholder="e.g. Code Geass")

    query = anime_input or manual_input

    # --- Recommend Button ---
    if st.button("🎯 Recommend"):
        if query:
            resolved_name, recs = recommend(query)

            if isinstance(recs, pd.DataFrame):
                st.success(f"Recommendations based on **{resolved_name}**:")
                for i in range(len(recs)):
                    title = recs.iloc[i]["Recommended Anime"]
                    score = recs.iloc[i]["Similarity Score"]
                    image_url = fetch_image(title)

                    match = anime_df[anime_df["name"] == title]
                    if match.empty:
                        st.warning(f"⚠️ Info not found for: {title}")
                        continue  # Skip to next recommendation
                    anime_info = match.iloc[0]

                    genre = anime_info["genre"]
                    atype = anime_info["type"]
                    episodes = anime_info["episodes"]
                    rating = anime_info["rating"]
                    members = anime_info["members"]

                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if image_url:
                                st.image(image_url, width=130)
                            else:
                                st.write("❌ No image")
                        with col2:
                            st.markdown(f"""
                                <div class='anime-card'>
                                    <h4>{title}</h4>
                                    <p>🎯 Similarity Score: {score:.4f}</p>
                                    <p>🎬 Type: {atype} | 📺 Episodes: {episodes}</p>
                                    <p>⭐ Rating: {rating} | 👥 Members: {members:,}</p>
                                    <p>🏷️ Genre: {genre}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        st.markdown("---")

            else:
                st.error(recs)
        else:
            st.warning("Please enter or select an anime name.")
    
with tab2:
    st.markdown("## 🧭 Explore Top Anime")

    subtab1, subtab2, subtab3 = st.tabs(["⭐ By Rating", "🔥 By Popularity", "🏷️ By Genre"])

    # --- ⭐ By Rating ---
    with subtab1:
        st.subheader("Top 100 Anime by Rating")
        sorted_by_rating = top_100_df.sort_values("avg_rating", ascending=False).reset_index(drop=True)
        st.dataframe(
            sorted_by_rating.style.format({
                "avg_rating": "{:.2f}",
                "num_rating": "{:,}"
            }),
            use_container_width=True
        )

    # --- 🔥 By Popularity ---
    with subtab2:
        st.subheader("Top 100 Anime by Popularity (Number of Ratings)")
        sorted_by_popularity = top_100_df.sort_values("num_rating", ascending=False).reset_index(drop=True)
        st.dataframe(
            sorted_by_popularity.style.format({
                "avg_rating": "{:.2f}",
                "num_rating": "{:,}"
            }),
            use_container_width=True
        )

    # --- 🏷️ By Genre ---
    with subtab3:
        st.subheader("Top Anime by Genre")
        top_100_df["genre"] = top_100_df["genre"].fillna("")

        all_genres = set()
        for genre_str in top_100_df["genre"]:
            genres = [g.strip() for g in genre_str.split(",") if g.strip()]
            all_genres.update(genres)
        genre_choice = st.selectbox("🎭 Select a Genre", sorted(all_genres))

        genre_filtered = top_100_df[top_100_df["genre"].str.contains(genre_choice, case=False, na=False)]

        if genre_filtered.empty:
            st.warning(f"No anime found for genre: {genre_choice}")
        else:
            st.dataframe(
                genre_filtered.sort_values("avg_rating", ascending=False).reset_index(drop=True).style.format({
                    "avg_rating": "{:.2f}",
                    "num_rating": "{:,}"
                }),
                use_container_width=True
            )
