# Table of Contents
- [📖 Get an Overview](#-get-an-overview)
- [👥 Meet the Core Team](#-meet-the-core-team)
- [📊 Gather and Process Data](#-gather-and-process-data)
- [🌍 Identify Global Events](#-identify-global-events)
- [🎭 Sentiment Analysis using DistilBERT](#-sentiment-analysis-using-distilbert)
- [🎉 Now it's Your Turn to Play!](#-now-its-your-turn-to-play)
- [🛠️ How to Contribute](#️-how-to-contribute)
- [📚 List Acronyms](#-list-acronyms)

# 📖 Get an Overview

[**SolarSoundBytes**](https://solar-sound-bytes.app/) is a data-driven machine-learning project that explores the global sentiment towards **renewable energy** and **energy storage** in the timeframe from 2022-01-02 to 2024-12-24.

This project is a real-world application of the learnings acquired
during a [9-week bootcamp at Le Wagon](https://www.lewagon.com/barcelona/data-science-course) and was created during [our](#-core-team) final 2 weeks together in Barcelona from June 2 to 13, 2025.


## Input: Sentiment Analysis

Sentiment analysis is a well-known Natural Language Processing (NLP) technique used to determine the emotional tone of a text, classifying it as either positive, negative, or neutral. 

- The sentiment of the general public is being inferred by performing sentiment analysis on **129,756 tweets from 72,088 users** ([database/db-twitter.db](database/db-twitter.db)). 
- Analogously, the sentiment of official channels is derived by sentiment analysis on **4,093 news articles from 186 unique sources** ([database/db-news-articles.db](database/db-news-articles.db)). 

By feeding the sentiment analysis results of these 2 datasets into an [interactive dashboard](https://solar-sound-bytes.app/dashboard), the user is empowered to perform an independent investigation and identify possible correlations between public and official sentiments as well as compare those sentiments with additional metrics. 

## Input: Additional Metrics

So far, two additional metrics have been implemented, which can be optionally overlaid to compare with sentiments during the same timeframe from 2022-01-02 to 2024-12-24. 

1. Renewables Dataset: [Global capacity of renewable energy technologies, solar and wind](https://ember-energy.org/data/monthly-wind-and-solar-capacity-data/)
2. Economic Dataset: [S&P 500 Historical Data downloaded on 2025-06-12 from investing.com](https://www.investing.com/indices/us-spx-500-historical-data)


## Output: SoundBytes

To draw your own conclusions regarding the ongoing energy transition, you can play with our extensive dataset using an [interactive dashboard](https://solar-sound-bytes.app/dashboard).

Users can pick any combination of data streams for a specific time period to generate custom audio reports, making the complex and multi-layered topic of energy transition accessible to everyone. Based on the user-defined timeframe of [sentiment analysis results](#input-sentiment-analysis) and optional [additional metrics](#input-additional-metrics), turned on or off by the user, the user can trigger the generation of an AI report.

This report is displayed as plain text and also available in audio format, aka a **SoundByte**. 

A SoundByte is a short audio summary which turns the chosen data range into a simple and easily digestible explanation. 


# 👥 Meet the Core Team

| Name                  | GitHub                                                 | Role             | Content                                                                                                                                                               |
| --------------------- | ------------------------------------------------------ | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fadri Pestalozzi      | [@FadriPestalozzi](https://github.com/FadriPestalozzi) | Team Lead        | Documentation // Tweets on renewable energy: Research data sources, scraping and perform NLP                                                                          |
| Steffen Lauterbach    | [@steffenlaut](https://github.com/steffenlaut)         | System Architect | Create model pipeline and docker container to expose API // Research and process satellite images to detect and quantify solar panels //Integrate TTS (text-to-sound) |
| Enrique Flores Roldán | [@efloresr](https://github.com/efloresr)               | Project Manager  | News Articles: Research data sources // Create data processing pipeline, and tested models for NLP. // Fine tune distilber model for sentiment analysis.              |

# 📊 Gather and Process Data


## News Articles

Online research for datasets of news-articles in the field of renewable energy technologies led us to the [Cleantech Media Dataset by Anacode](https://www.kaggle.com/datasets/jannalipenkova/cleantech-media-dataset).

- 20K articles in total
- Build a code for text processing: cleaning signs & digits, stopwords,
  lemmatize
  - 12,966 articles without a date. 2.5K Dates extracted from urls
  - **9,938** working articles (Europe only) (for MVP)

### Model Evaluation

Tested different models for sentiment analysis.

- [**distilbert-base-uncased-finetuned-sst-2-english**](https://huggingface.co/distilbert/distilbert-base-uncased-finetuned-sst-2-english)
  — Pos/Neg (no neutral)
- [**cardiffnlp/twitter-roberta-base-sentiment-latest**](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest)
  — Pos/Neg/Netural
- [**nlptown/bert-base-multilingual-uncased-sentiment**](https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment)
  — Optimized for reviews
- [**Gemma 3**](https://huggingface.co/google/gemma-3-27b-it) — Large language model for instruction following


### Gemma 3 Fine-tuning Challenges with Vertex AI

The Vertex AI Software Development Kit (SDK) for Generative AI fine-tuning with Gemma models presented significant technical obstacles:

- **Rapid API evolution:** The SDK changes frequently, making stable implementation difficult
- **Method instability:** Core methods like `fine_tune()` and `tune_model()` were either missing, deprecated, or relocated across different SDK versions
- **Inconsistent availability:** The `GenerativeModel.fine_tune()` method proved unreliable across different environments (Cloud Shell and pip installations)
- **Model architecture mismatch:** Gemma 3 is designed for chat and instruction-following tasks, not specialized sentiment analysis like DistilBERT or RoBERTa
- **Implementation complexity:** The recommended approach using helper methods like `aiplatform.model_garden.models.fine_tune_gemma()` requires significant code refactoring

Despite progressively simplifying the approach from heavy preprocessing to reduced preprocessing and finally attempting sentence-level analysis by chunking articles, Gemma 3 consistently delivered poor accuracy, leading to its abandonment in favor of fine-tuning a different model.


### Fine Tuning and Predict

The recommended model for this task was the [distilbert/distilbert-base-uncased](https://huggingface.co/distilbert/distilbert-base-uncased). We trained this model using labeled data from the [NewsArticles_ForTraining](https://www.kaggle.com/datasets/clovisdalmolinvieira/news-sentiment-analysis) dataset, which contains 3.5K news articles with sentiment labels covering various topics. 

We fine-tuned the distilbert/distilbert-base-uncased model with these 3.5K articles labeled as Positive, Negative, or Neutral. The initial test results were disappointing, with a loss of 0.627 and accuracy of 0.782. After adjusting the hyperparameters and running a second test, we achieved significantly better performance with a loss of 0.37 (lower loss is better) and accuracy of 0.796.

### Conclusion
Pre-trained sentiment models performed poorly on CleanTech news articles. We tried advanced models including DistilBERT, Twitter-RoBERTa, and Gemma, but accuracy remained low and the workflow complexity did not fit into our tight schedule to deliver an MVP within 2 weeks. Fine-tuning Gemma on Vertex AI failed due to unstable SDK APIs. Gemma 3 is optimised for chat and instruction-following tasks. We pivoted to fine-tuning DistilBERT-base with 3.5K labeled articles and achieved approximately 0.80 accuracy after tuning. Our conclusion is that domain-specific fine-tuning is required for reliable sentiment analysis on niche topics like CleanTech.


## Social Media Data from Twitter

To compare the sentiment of news articles to a broader public sentiment, we looked for a fitting twitter dataset.

Although [the Climate Change Twitter Dataset](https://www.kaggle.com/datasets/deffro/the-climate-change-twitter-dataset), including 15 million tweets from 2006 to 2019, looked promising at first, we could not use it due to the lack of full-text tweets within.

Since the [vast majority](#futile-rehydration-attempt-of-climate-change-twitter-dataset) of the most recent tweet_ids listed inside [the Climate Change Twitter Dataset](https://www.kaggle.com/datasets/deffro/the-climate-change-twitter-dataset) in GBR are no longer accessible, we abandoned our attempt to rehydrate this dataset.

After extensive and unsuccessful further research for an alternative twitter dataset, we decided to create our own twitter dataset as input for a social media sentiment analysis using a [scraping actor](https://console.apify.com/actors/CJdippxWmn9uRfooo) on [console.apify](https://console.apify.com/).

As a tradeoff between scraping cost, time and scraping-content, a sampling frequency of 1 day per month was chosen, applying an
[actor-specific](https://console.apify.com/actors/CJdippxWmn9uRfooo) format of [scraping input parameters](data_acquisition/apify_twitter_sample_query.json).

### Rehydration of Climate Change Twitter Dataset

To test rehydration of
[the Climate Change Twitter Dataset](https://www.kaggle.com/datasets/deffro/the-climate-change-twitter-dataset),
a tweet-subset of all tweets with geolocation coordinates inside GBR (=557,125 tweets) was selected.
Rehydration was performed in chunks of up to 10k tweets. As shown in below table, the lack of data renders this rehydration attempt pointless.

| range of GBR-tweet-numbers of tweet_ids in scraping-chunk | number of successful rehydrations | rehydration percentage of tweet chunk |
| --------------------------------------------------------- | --------------------------------- | ------------------------------------- |
| 550,000 – 557,125                                         | 1                                 | 0.013%                                |
| 540,000 – 549,999                                         | 5                                 | 0.050%                                |
| 530,000 – 539,999                                         | 11                                | 0.110%                                |

### Scraping Twitter Dataset

To compile a twitter dataset covering the same topics as covered by the [Cleantech Media Dataset](https://www.kaggle.com/datasets/jannalipenkova/cleantech-media-dataset), the [unique values in the cleantech "domains" column](preprocessing/scraping/cleantech_articles__unique_domains.txt) are used as scraping query terms with the chosen [twitter scraper](https://console.apify.com/actors/CJdippxWmn9uRfooo).

To work with a user-friendly scraping GUI while keeping scraping costs below 40 USD/month, the following scraper was chosen: [Tweet Scraper|$0.25/1K Tweets | Pay-Per Result | No Rate Limits](https://console.apify.com/actors/CJdippxWmn9uRfooo/input?addFromActorId=CJdippxWmn9uRfooo).

Unfortunately, this chosen scraping method was unable to handle more than 2 search terms simultaneously. 
Attempts to use more than 2 search terms led to the scraper ignoring the time window, thus always returning the most recent results. 

Therefore, the [initial list of search terms](preprocessing/scraping/cleantech_articles__unique_domains.txt) was replaced with just 2 overarching [search terms](#chosen-search-terms) to generate a twitter dataset with as large of a contextual overlap as possible with the [Cleantech Media Dataset by Anacode](https://www.kaggle.com/datasets/jannalipenkova/cleantech-media-dataset).


### Chosen Search Terms

- renewable energy
- energy storage

# 🌍 Identify Global Events

To identify specific dates around which to refine our twitter dataset, i.e. to allow us to zoom
into global events where a significant change in sentiment is highly probable, a
[deep research was performed by iteratively prompting ChatGPT 4.1](https://chatgpt.com/share/68495bc3-ee6c-8006-9816-8b0480a0bf3c).

The resulting overview with reasoning based on verified refererences is
available in a
[pdf](<website/pages/attachments/global_events_summary.pdf>)
and summarized in the [table below](#global-events-table). For detailed
references and reasoning, see the
[Global Events PDF](<website/pages/attachments/global_events_summary.pdf>).

## Global Events Table

| Date         | Event                                                                                                                                                                                                                | Region | Expected Impact on Sentiment                 |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------- |
| 2022-02-24   | [Russian invasion of Ukraine](https://en.wikipedia.org/wiki/2022_Russian_invasion_of_Ukraine)                                                                                                                        | Global/EU      | Spike in interest and urgency for renewables |
| 2022-05-18   | [EU announces REPowerEU plan](https://ec.europa.eu/commission/presscorner/detail/en/IP_22_3131)                                                                                                                      | EU             | Positive sentiment for renewables            |
| 2022-08-16   | [US Inflation Reduction Act signed (major climate/energy provisions)](https://www.whitehouse.gov/briefing-room/statements-releases/2022/08/16/fact-sheet-the-inflation-reduction-act-supports-workers-and-families/) | USA            | Strong positive sentiment                    |
| 2023-04-20   | [IEA reports global solar power generation surpasses oil for the first time](https://www.iea.org/news/solar-overtakes-oil-in-global-power-generation)                                                                | Global         | Positive sentiment for solar, shift from fossil fuels |
| 2023-12-13   | [COP28 concludes with historic agreement to transition away from fossil fuels](https://unfccc.int/news/cop28-agrees-historic-deal-to-transition-away-from-fossil-fuels)                                             | Global         | Strong positive sentiment for renewables, policy optimism |
| 2023-11-30   | [Global installed solar PV capacity surpasses 1 terawatt milestone](https://www.pv-magazine.com/2023/11/30/global-installed-solar-capacity-surpasses-1-tw/)                                                        | Global         | Positive sentiment, milestone for solar industry      |


# 🎭 Sentiment Analysis using DistilBERT

Raw news and Twitter data are classified as positive or negative sentiment. 
Learn more [behind the scenes](documentation/DistilBERT/behind-the-scenes.md).


# 🎉 Now it's Your Turn to Play!

After gathering this treasure chest of data it's up to you, dear user, to now play with our 📊 [interactive dashboard](https://solar-sound-bytes.app/dashboard) so you can 🔎 discover the stories hidden behind layers of raw data. Good luck 🚀







# 🛠️ How to Contribute

If you're also super excited about [☀️Solar🔊Sound🍔Bytes](https://solar-sound-bytes.app/), here's how you can support our research effort! 

Thank you for sharing your time and energy with us 🫀

## Gitpod Online IDE

You can open this project in a preconfigured Gitpod online IDE and edit, run, test, debug and commit directly from your browser.

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io#https://github.com/FadriPestalozzi/SolarSoundBytes)

## clone this repo to your computer

```shell
cd /path/to/your/project-parent-folder

git clone <paste_your_SSH_link_here>
```

## create virtual python environment

It's good practice to create a separate development environment to prevent growing your global python environment into a cluttered mess. 

```shell
# navigate into the cloned project folder
cd /path/to/SolarSoundBytes

pyenv virtualenv 3.12.9 SolarSoundBytes
```

## activate the new virtual environment inside the cloned repo

```shell
pyenv local SolarSoundBytes
```

## install requirements

To install the required packages and their versions, run the command below.

```shell
pip install -r requirements.txt
```

## activate virtual environment

```shell
pyenv activate SolarSoundBytes
```

## run locally

```shell
streamlit run website/pages/3_Interactive_Dashboard.py
```

# 📚 List Acronyms

- **API**: [Application Programming Interface](https://en.wikipedia.org/wiki/API) – a set of rules that allows
  different software applications to communicate with each other.
- **CLS**: [Classification Token](https://stackoverflow.com/questions/62705268/why-bert-transformer-uses-cls-token-for-classification-instead-of-average-over?utm_source=chatgpt.com) – The first token of every sequence in BERT-like models; its final hidden state is used as the aggregate sequence representation for classification tasks.
- **GBR**: [Great Britain](https://en.wikipedia.org/wiki/Great_Britain)
- **GUI**: [Graphical User Interface](https://en.wikipedia.org/wiki/Graphical_user_interface) – a visual way of interacting with a
  computer using items like windows, icons, and buttons.
- **MVP**: [Minimum Viable Product](https://en.wikipedia.org/wiki/Minimum_viable_product) – the simplest version of a product that can
  be released to test a new business idea and gather user feedback.
- **NLP**: [Natural Language Processing](https://en.wikipedia.org/wiki/Natural_language_processing) – a field of artificial intelligence
  focused on the interaction between computers and human language.
- **PV**: [Photovoltaics](https://en.wikipedia.org/wiki/Photovoltaics) – technology that converts sunlight directly into electricity using solar cells.
- **SDK**: [Software Development Kit](https://en.wikipedia.org/wiki/Software_development_kit) – a collection of software development tools and libraries that allows developers to create applications for a specific platform or framework.
- **TTS**: [Text-to-Speech](https://en.wikipedia.org/wiki/Speech_synthesis) – technology that converts written text into spoken
  voice output.
- **USD**: [United States Dollar](https://en.wikipedia.org/wiki/United_States_dollar) – the official currency of the United States and several other countries.


# 🥚 Lay Easter Eggs

## Tagline

To break down the complexity of this project, we created 2 taglines using either raw brainpower or sprinkling in some AI guesswork.  

Now it's up to your human intuition to decide: 
Which tagline was written by a human and which one is the figment of an AI agent? 

Place your bets in our [TaglineTouringTest](https://form.typeform.com/to/Pqtp10qL) to figure out, if your subconscious chose the blue pill (just NetFlix and Chill) or the red pill (Ready to Face the Terminator)!