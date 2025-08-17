import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_components import get_emoji_title, render_footer


def header_section():
    """Display the main header and hero section"""
    st.title("🔧 From Raw Data to User Podcasts 🎧")
    st.markdown(f"## Welcome to our {get_emoji_title()}🧑‍🍳Kitchen!")
    st.markdown("""
        Let us walk you through our journey of transforming years of
        public opinion data, official news, market metrics, and historical events
        into an interactive dashboard to create your very own audio insights.
        """)
    st.markdown("---")

def sentiment_analysis_intro():
    """Introduction to sentiment analysis"""
    st.header("🎯 What is Sentiment Analysis?")
    
    st.markdown("""
    [Sentiment analysis](https://en.wikipedia.org/wiki/Sentiment_analysis) is a way of **classifying text by emotional tone** – for instance, 
    telling whether a social‑media post sounds positive or negative.
    
    As part of [Natural Language Processing (NLP)](https://en.wikipedia.org/wiki/Natural_language_processing), 
    sentiment analysis uses a **Transformer model** to extract the emotional tone embedded within a specific text.
    
    A Transformer is like a **group discussion**: every word "listens" to every other word to understand its context before speaking.
    
    Thanks to the so-called **self‑attention** (i.e. every word considering all other words), 
    a Transformer can spot whether _"bright"_ refers to _a sunny day_ or _a clever idea_.
    """)
    
    st.info("""
    **💡 Key Insight**
    
    In SolarSoundBytes we use sentiment analysis to understand how people feel about **renewable energy** and **energy storage**.
    
    To visualize sentiment trends in the general public and in official news media over time, you can place this sentiment data into a broader context using our [interactive dashboard](/Interactive_Dashboard)!
    """)
    
    st.markdown("---")

####----Data Research Tab----####
def data_research_tab():
    """Content for the Data Research tab"""
    st.header("📊 Data Research & Collection")
    
    st.subheader("""Main Questions:""")
    st.write("""
             - Where do we start?
             - How do we find **trustworthy, high-quality data**?
             - How can we ensure our data is **representative and unbiased**?
             - Which **models are best suited** for sentiment analysis of tweets and news articles?
             - How do we **visualize and interpret** the insights we uncover?
    """)

    st.subheader("Data Sources We Explored:")
    st.write("""
            To compare the sentiment of **news articles** to a broader **public sentiment**, we looked for a fitting twitter and news article datasets.
            Both the **Climate Change Twitter Dataset (15 million tweets spanning over 13 years)** and the **Cleantech Media Dataset by Anacode** looked promising at first, but we could not use them due to several limitations:
            - The lack of full-text tweets in the dataset.
            - News articles were bias towards positive sentiment.""")
    st.write("""
            As we were advancing int our process, the Cleantech Media Dataset settled the timeframe of our data collection to **2022-01-02 to 2024-12-24**.
            After extensive and unsuccessful further research for alternative datasets, we decided to create our own datasets for both, tweets and news articles
            for a social media sentiment analysis using a scraping actor on [console.apify](https://console.apify.com/).
             """)
    st.write("### Twitter/X API")
    st.write("""
            To work with a user-friendly scraping GUI while keeping scraping costs below **40 USD/month**, the following scraper was chosen:
            - Tweet Scraper|$0.25/1K Tweets | Pay-Per Result | No Rate Limits.
                Search Terms:
                - Renewable Energy
                - Energy Storage
             """)

    st.write("### News Articles API")
    st.write("""
             The **News API** was our main tool to collect news articles covering many
             - GNews 49,00€/month: API results in JSON format via HTTP GET requests.
                Search Terms:
                - Renewable Energy
                - Energy Storage
             """)

    st.write("### Global Events")
    st.markdown("""
            Key global events with likely sentiment shifts were identified by conducting in-depth research
            using [iterative ChatGPT-4.1 prompts](https://chatgpt.com/share/68495bc3-ee6c-8006-9816-8b0480a0bf3c). The output of our research on global events influencing renewable energy sentiment is shown below:
            """)
    
    with open(os.path.join(os.path.dirname(__file__), "attachments", "global_events_summary.pdf"), "rb") as f:
        st.download_button("📄 Download the research on global events likely influencing renewables sentiment (PDF)", f.read(), "global_events_summary.pdf", "application/pdf")

    st.write("### Data Metrics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tweets Analyzed", "129,756")
        st.caption("from 72,088 users")
    with col2:
        st.metric("News Articles", "4,093")
        st.caption("from 186 unique sources")
    with col3:
        st.metric("Total Words Processed", "3M+")

    # Data volume chart
    col1, col2 = st.columns(2)
    
    with col1:
        fig = go.Figure(data=go.Bar(
            x=['Tweets', 'News'],
            y=[129756, 4093],
            marker_color=['#1DA1F2', '#FF4500']
        ))
        fig.update_layout(
            title="Data Sources Volume",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    # Text volume chart (in millions of words)
    with col2:
        twitts_words = 8 * 136000  # Each tweet ~10 words
        news_words = 500 * 4093     # Each news article ~500 words
        fig = go.Figure(data=go.Bar(
            x=['Tweets ~words', 'News ~words'],
            y=[twitts_words, news_words],
            marker_color=['#1DA1F2', '#FF4500']
        ))
        fig.update_layout(
            title="Text Volume (Estimated Words)",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)


####----NLP Models Tab----#####
def nlp_models_tab():
    """Content for the NLP Models tab"""
    st.header("🤖 NLP Models & Model Selection")

    st.markdown("""
    During prototyping we benchmarked several transformer models, everyone of which can perform sentiment analysis. 
    
    Think of each model as a **recipe**: same ingredients (tweets & news) but different cooking styles that yield dishes of varying quality and cost.
    
    Here "**cost**" means the total inference cost of serving a sample batch of 100 k predictions on a standard cloud CPU (32 vCPU, 64 GB RAM) – a blend of runtime, memory footprint and resulting electricity/hosting bill.
    By the way: inference cost is the amount a cloud provider bills you for **running (evaluating) a trained model on new data**, i.e. turning input data into predictions.
    """)

    st.subheader("🔍 Model Comparison")
    
    st.markdown("**Key Findings:**")
    st.markdown("""
    - 🎯 Although VADER is the cheapest model, it's inaccuracy renders it useless for us. 
    - 💸 Generative models like Gemma3 are expensive and overkill for classification. 
    - 🏆 DistilBERT turns out to be the best trade‑off between speed, memory and accuracy for both short tweets and longer news articles.
    """)

    # Model comparison table with exact data from documentation
    model_data = {
        "#": [0, 1, 2, 3, 4, 5],
        "Model / Link": [
            "DistilBERT",
            "twitter‑RoBERTa",
            "nlptown‑reviews",
            "VADER (NLTK)",
            "Gemma 3 / Vertex AI",
            "Custom DistilBERT ×3"
        ],
        "Type": [
            "Binary (Pos/Neg)",
            "3‑way (Pos/Neu/Neg)",
            "Multilingual / Reviews",
            "3‑way rule‑based",
            "Generative",
            "Fine‑tuned Transformer"
        ],
        "Notes": [
            "★ Limited to 2 classes.",
            "✓ Great on very short text.",
            "✗ Tuned for product & movie reviews.",
            "✗ Ignores context, fails on sarcasm.",
            "✗ API unstable; fine‑tuning failed.",
            "✗ Fine-tuning failed due to biased data."
        ],
        "Accuracy": [
            "High",
            "High",
            "Low",
            "Low",
            "Low",
            "Medium"
        ],
        "Cloud Cost": [
            "$ 1.20",
            "$ 2.10",
            "$ 1.70",
            "$ 0.05",
            "$ 9.80",
            "$ 1.45"
        ]
    }

    model_df = pd.DataFrame(model_data)
    st.dataframe(model_df, hide_index=True)

    # What is DistilBERT section
    st.subheader("🤖 What is DistilBERT?")
    
    st.markdown("""
    Based on its large and expensive [BERT "teacher" model](https://huggingface.co/docs/transformers/en/model_doc/bert), 
    the [DistilBERT "student" model](https://huggingface.co/docs/transformers/model_doc/distilbert) 
    is a transformer representing the embedded NLP knowledge in a more efficient and compact way.
    
    **Key Features:**
    - **Compact:** 66M parameters (40% fewer than BERT) yet ~97% of its language grasp; ~60% faster
    - **Well‑maintained:** DistilBERT is part of the Hugging Face ecosystem
    - **Economical:** can serve predictions in < 25 ms per sentence on a 2024 M2 Pro laptop
    """)
    
    st.info("""
    **📊 BERT Training Data**
    
    **BooksCorpus:** ≈ 800M words
    **English Wikipedia:** ≈ 2.5B words
    
    **Total:** ~3.3B words
    """)



def distilbert_process_tab():
    """Content for the DistilBERT Process tab"""
    st.header("🔍 Step‑by‑Step: How DistilBERT Works")
    
    st.markdown("""
    This section guides you through the sentiment analysis of the sentence: "Love this gizmo!"
    
    After Step 2, DistilBERT has produced a 768‑D "fingerprint" (the [CLS] vector) that encodes the whole sentence's meaning.  
    Steps 3–5 turn that abstract fingerprint into a concrete Positive / Negative label.
    """)

    # Step-by-step process
    steps = [
        {
            "title": "1️⃣ Tokenisation – \"chopping text into tokens\"",
            "description": """Prior to its analysis, an input text is divided into chunks, a.k.a. tokens. 
            Each chunk has an associated ID-number and represents a unique meaning.
            
            A tokenized text starts with a classification-token (CLS, ID=101) and ends with a separator-token (SEP, ID=102).
            
            Regular WordPiece-tokens come after the first 100 reserved indices and the special tokens (CLS, SEP, MASK) and are ordered by frequency.""",
            "example": """Input: Love this gizmo!
            
Tokens: ['[CLS]', 'love', 'this', 'g', '##iz', '##mo', '!', '[SEP]']

Token IDs: [101, 3862, 2023, 2290, 12770, 2213, 999, 102]

Note: The rare word "gizmo" is split into g + ##iz + ##mo.  
Because 2023 < 3862, the token "this" occurs more often than "love" in the pre-training corpus."""
        },
        {
            "title": "2️⃣ Encoding – \"group discussion\"",
            "description": """The ID-numbers are fed through 6 Transformer layers. 
            Each layer lets every word listen to every other word and update its meaning.
            
            Every Transformer layer in DistilBERT outputs a vector with 768 numbers (=dimensions) per token.
            
            The final hidden state of [CLS] becomes a 768‑digit-long numeric fingerprint which encodes the meaning of the entire input text.""",
            "example": """One dimension (e.g. #512) might measure positivity, another (e.g. #233) might light up for energy gadgets.

Like the way mixing red & green gives yellow, combining many dimensions encodes subtle meaning.

Important: The coordinate indices in a 768-dimensional DistilBERT vector carry no fixed meaning. 

Any semantic signal can end up aligned with any combination of axes."""
        },
        {
            "title": "3️⃣ Classification head – \"opinion poll\"",
            "description": """The fingerprint of the entire input text is fed into a tiny neural layer (768 inputs → 2 outputs) which multiplies each of the 768 numbers by a learned weight and adds a bias.
            
            The two resulting values are called logits.
            These logits can be interpreted as votes - one for negative, one for positive.
            
            Why logits first? Logits separate "scoring" from "probability making." They let the model learn unbounded linear scores without worrying about the 0‑1 range during training. Each weight tells how strongly a fingerprint dimension pushes toward Positive or Negative.""",
            "example": """Imagine two judges—one rooting for Negative, one for Positive. 
Each judge scans the fingerprint, sums up the signals they care about, and produces a raw score.

Logits: [neg, pos] → [-1.43, 1.25]

Behind the scenes: During fine‑tuning, the model automatically adjusts those 768×2 weights so the final decision aligns with your training labels."""
        },
        {
            "title": "4️⃣ Softmax – \"turn votes into odds\"",
            "description": """Softmax takes the two logits, exponentiates them, and divides by their sum so the outputs become probabilities that add up to 1.
            
            Why probabilities later? Softmax normalises the unbounded logit scores only at the very end, giving a clean probabilistic interpretation that's easy to understand and compare.""",
            "example": """It's like converting the judges' raw scores into betting odds you can actually compare.

1. Exponentiate each logit: e^(-1.43) ≈ 0.2393, e^(1.25) ≈ 3.4903
2. Sum the exponentials: 0.2393 + 3.4903 = 3.7296
3. Divide each exp by the sum: 
   - 0.2393 / 3.7296 = 0.064
   - 3.4903 / 3.7296 = 0.936

Result: neg = 6.4%, pos = 93.6%"""
        },
        {
            "title": "5️⃣ Decision – \"pick the winner\"",
            "description": """Whichever probability is higher is the model's answer; we log the confidence too.
            
            The label with the higher probability is returned, and the probability itself is logged as confidence.""",
            "example": """Highest value: 0.936

Model output: Text sentiment is positive with 93.6% confidence"""
        }
    ]

    for step in steps:
        with st.expander(step["title"]):
            st.markdown(step["description"])
            if "example" in step:
                st.info(f"**Example:** {step['example']}")

####----Pipeline Tab----#####
def pipeline_tab():
    """Content for the Pipeline tab"""
    st.header("⚙️ The Complete Pipeline")

    st.markdown("**From Raw Data to Insights: Our 6-Step Process**")

    # Pipeline steps
    pipeline_steps = [
        ("🔍 Data Collection", "Gather tweets and news articles"),
        ("🧹 Text Cleaning", "Remove noise, normalize text"),
        ("🤖 Sentiment Analysis", "Apply our trained NLP model"),
        ("📊 Data Aggregation", "Merge sentiment insights from tweets and news with market (S&P 500) and economic (GDP) data to reveal the bigger picture."),
        ("📄 Text Generation", "Generate podcast-style summary content"),
        ("🎧 Text-to-Speech", "Convert to audio format")
    ]

    for i, (step, description) in enumerate(pipeline_steps, 1):
        with st.expander(f"Step {i}: {step}"):
            st.write(description)

            # Code examples for key steps
            if i == 1:
                st.markdown("[**Twitter API user story**](https://drive.google.com/file/d/1uVTl7SvQNJE00I0GaDez2XCjw0byp4j7/view?usp=sharing)")
                st.code("""
def extract_tweet_data(tweet, reference_date):
    def safe_get(dct, key, default=None):
        return dct.get(key, default)

    def get_user_mentions(entities):
        mentions = safe_get(entities, "user_mentions", [])
        id_strs = "~~".join([m.get("id_str", "") for m in mentions])
        indices_0 = mentions[0]["indices"][0] if len(mentions) > 0 else None
        indices_1 = mentions[1]["indices"][1] if len(mentions) > 1 else None
        name = "~~".join([m.get("name", "") for m in mentions])
        screen_name = "~~".join([m.get("screen_name", "") for m in mentions])
        return id_strs, indices_0, indices_1, name, screen_name

    entities = tweet.get("entities", {})
    user_mentions = get_user_mentions(entities)
                            """, language='python')

                st.markdown("[**News Articles API user story**](https://drive.google.com/file/d/1LsZA_0e8LvhuxZZMg6myaI6gNTh1d0-e/view?usp=sharing)")
                st.code("""
def articles_api_2_csv(t_start_str: str, t_end_str: str, query: str, query_subdivisions: int = 1):
    # --------------------- API call ---------------------
    # load API key and plan-specific max_n_articles from .env file
    load_dotenv()
    API_KEY = os.getenv("GNEWS_API_KEY")
    MAX_N_ARTICLES = os.getenv("GNEWS_MAX_N_ARTICLES")

    if not API_KEY:
        raise ValueError("GNEWS_API_KEY not found in environment variables.")
                        """, language='python')

            elif i == 2:
                st.code("""
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r".*'name':\\s*'([^']+)'.*", r'\\1', text)
    text = re.sub(r'^name\\s+(.+?)\\s+url\\s+https.*', r'\\1', text)
    tokens = text.split()
    return ' '.join(tokens)

# Apply preprocessing to text columns
text_columns = ['title', 'description', 'source', 'content']
for col in text_columns:
    df[f'Clean_{col.capitalize()}'] = df[col].apply(preprocess_text)

# Clean and format date
df['Clean_Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')

# Create clean dataframe by dropping original columns
columns_to_drop = ['url', 'image', 'publishedAt', 'title', 'description', 'content', 'source', 'Date']
df_clean = df.drop(columns=columns_to_drop)

df_clean.head()
                            """, language='python')

            elif i == 3:
                st.code("""
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
df_sample = df_clean.sample(n=100, random_state=42).copy()

df_sample[['Sentiment', 'Score']] = df_sample['Clean Article Text'].apply(analyze_sentiment_chunked)
df_sample.head()
                """, language='python')

            elif i == 5:
                st.code("""
client = OpenAI(api_key = api_key)
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a data-analytical journalist."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.2,
    max_tokens=1000
)""", language='python')

            elif i == 6:
                st.code("""
if st.button("Play"):
    if isinstance(text, str) and text.strip():
        tts = gTTS(text.strip(), lang="en")
        tts.save("output.mp3")
        st.audio("output.mp3", format="audio/mp3")
    else:
        st.warning("Text field is empty or invalid.")
                """, language='python')

def limitations_tab():
    """Content for the Limitations tab"""
    st.header("⚠️ Limitations to Keep in Mind")
    
    limitations = [
        {
            "title": "🎭 Sarcasm & Irony",
            "description": "Sarcasm and irony remain hard to detect, even for large transformer models. Context and tone are crucial for humans but challenging for AI.",
            "example": "Tweet: 'Great, another power outage! 🙄' might be classified as positive due to the word 'Great'"
        },
        {
            "title": "🔄 Domain Shift",
            "description": "New slang, emerging topics, or shifts in language use require model re-training to maintain accuracy.",
            "example": "New renewable energy terminology or changing public discourse patterns may not be captured"
        },
        {
            "title": "📱 Ultra‑short Texts",
            "description": "Single emojis or very short messages give little semantic context, leading to unreliable predictions.",
            "example": "A single '⚡' emoji provides insufficient context for reliable sentiment classification"
        }
    ]
    
    for limitation in limitations:
        with st.expander(limitation["title"]):
            st.markdown(limitation["description"])
            if "example" in limitation:
                st.info(f"**Example:** {limitation['example']}")

def final_assembly_tab():
    """Content for the Final Assembly tab"""
    st.header("🚀 Final Assembly & Integration")

    st.subheader("Bringing It All Together with Streamlit")

    # Create two columns for Architecture Overview and Technical Stack
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Architecture Overview:**")
        st.write("• **Frontend**: Streamlit web application")
        st.write("• **Backend**: Python data processing pipeline")
        st.write("• **Database**: Sentiment analysis results")
        st.write("• **APIs**: External data sources integration")
        st.write("• **Deployment**: Cloud-based hosting")

    with col2:
        st.markdown("**Technical Stack:**")
        tech_stack = {
            "Frontend": "Streamlit",
            "ML/NLP": "Transformers, scikit-learn",
            "Data Processing": "Pandas, NumPy",
            "Visualization": "Plotly, Matplotlib",
            "Audio": "Text-to-Speech APIs",
            "Deployment": "Streamlit Cloud"
        }

        for category, tech in tech_stack.items():
            st.write(f"• **{category}**: {tech}")

def main_tabs():
    """Display the main content tabs"""
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Data Research",
        "🤖 NLP Models",
        "🔍 DistilBERT Process",
        "⚙️ Pipeline",
        "⚠️ Limitations",
        "🚀 Final Assembly"
    ])

    with tab1:
        data_research_tab()

    with tab2:
        nlp_models_tab()

    with tab3:
        distilbert_process_tab()

    with tab4:
        pipeline_tab()

    with tab5:
        limitations_tab()

    with tab6:
        final_assembly_tab()

def render_behind_scenes():
    """Render function for importing into other pages"""
    header_section()
    sentiment_analysis_intro()
    main_tabs()
    render_footer()

def main():
    """Main function to run the page"""
    st.set_page_config(page_title="From Data to Podcasts @ ☀️🔊🍔", page_icon="🔧", layout="wide")
    render_behind_scenes()

if __name__ == "__main__":
    main()