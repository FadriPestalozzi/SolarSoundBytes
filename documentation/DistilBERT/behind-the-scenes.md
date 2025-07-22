# Behind the Scenes: How DistilBERT Powers SolarSoundBytes’ Sentiment Analysis

In SolarSoundBytes we use sentiment analysis to understand how people feel about **renewable energy** and **energy storage**. 

To visualize sentiment trends in the general public and in official news media over time, you can place this sentiment data into a broader context using our interactive dashboard!  

## Table of Contents
- [What is sentiment analysis?](#what-is-sentiment-analysis)
- [How does sentiment analysis work?](#how-does-sentiment-analysis-work)
- [How did we choose a model?](#how-did-we-choose-a-model)
  - [Model Comparison](#model-comparison)
  - [What is DistilBERT?](#what-is-distilbert)
  - [What is BERT?](#what-is-bert)
- [Step‑by‑Step: How DistilBERT Turns a Text into a Sentiment](#step-by-step-how-distilbert-turns-a-text-into-a-sentiment)
  - [Why logits first, probabilities later?](#why-logits-first-probabilities-later)
- [Throughput snapshot](#throughput-snapshot)
- [Limitations to keep in mind](#limitations-to-keep-in-mind)


## What is sentiment analysis?

[Sentiment analysis](https://en.wikipedia.org/wiki/Sentiment_analysis) is a way of **classifying text by emotional tone** – for instance, telling whether a social‑media post sounds positive or negative. 


## How does sentiment analysis work?

As part of [Natural Language Processing (NLP)](https://en.wikipedia.org/wiki/Natural_language_processing), sentiment analysis uses a **Transformer model** to extract the emotional tone embedded within a specific text. 

A Transformer is like a **group discussion**: every word "listens" to every other word to understand its context before speaking.

Thanks to the so-called **self‑attention** (i.e. every word considering all other words), a Transformer can spot whether _“bright”_ refers to _a sunny day_ or _a clever idea_.


## How did we choose a model?

During prototyping we benchmarked several transformer models, everyone of which can perform sentiment analysis. 

Think of each model as a **recipe**: same ingredients (tweets & news) but different cooking styles that yield dishes of varying quality and cost.

Here “**cost**” means the total inference cost of serving a sample batch of 100 k predictions on a standard cloud CPU (32 vCPU, 64 GB RAM) – a blend of runtime, memory footprint and resulting electricity/hosting bill.
By the way: inference cost is the amount a cloud provider bills you for **running (evaluating) a trained model on new data**, i.e. turning input data into predictions.

### Model Comparison

When comparing cloud cost for batch inference we see that: 
- 🎯 Although VADER is the cheapest model, it's inaccuracy renders it useless for us. 
- 💸 Generative models like Gemma3 are expensive and overkill for classification. 
- 🏆 DistilBERT turns out to be the best trade‑off between speed, memory and accuracy for both short tweets and longer news articles.

| #   | Model / Link                                                                                                 | Type                   | Notes                                    | Accuracy (measured by applying to 3300 manually‑labelled tweets) | cloud cost for batch inference |
| --- | ------------------------------------------------------------------------------------------------------------ | ---------------------- | ---------------------------------------- | ---------------------------------------------------------------- | ------------------------------ |
| 0   | **DistilBERT**                                                                                               | Binary (Pos/Neg)       | ★ Limited to 2 classes.                  | **High**                                                         | **$ 1.20**                     |
| 1   | [twitter‑RoBERTa](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment)                          | 3‑way (Pos/Neu/Neg)    | ✓ Great on very short text.              | High                                                             | $ 2.10                         |
| 2   | nlptown‑reviews                                                                                              | Multilingual / Reviews | ✗ Tuned for product & movie reviews.     | Low                                                              | $ 1.70                         |
| 3   | [VADER (NLTK)](https://stackoverflow.com/questions/38819968/vader-sentiment-values-not-coming-out-correctly) | 3‑way rule‑based       | ✗ Ignores context, fails on sarcasm.     | Low                                                              | **$ 0.05**                     |
| 4   | Gemma 3 / Vertex AI                                                                                          | Generative             | ✗ API unstable; fine‑tuning failed.      | Low                                                              | $ 9.80                         |
| 5   | **Custom DistilBERT ×3**                                                                                     | Fine‑tuned Transformer | ✗ Fine-tuning failed due to biased data. | Medium                                                           | $ 1.45                         |

### What is DistilBERT?

- Based on its large and expensive [BERT “teacher” model](https://huggingface.co/docs/transformers/en/model_doc/bert), the [DistilBERT “student” model](https://huggingface.co/docs/transformers/model_doc/distilbert) [is a transformer representing the embedded NLP knowledge in a more efficient and compact way](https://arxiv.org/abs/1910.01108).
* **Compact:** 66 M parameters (40 % fewer than BERT) yet ~97 % of its language grasp; ~60 % faster.
	* source: [DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter](https://arxiv.org/abs/1910.01108)
* **Well‑maintained:** DistilBERT is part of the Hugging Face ecosystem.
	* [source](https://huggingface.co/docs/transformers/model_doc/distilbert)
* **Economical:** can serve predictions in < 25 ms per sentence on a 2024 M2 Pro laptop (8 performance + 4 efficiency cores), keeping our hosting bill small.



### What is BERT?

[BERT](https://aclanthology.org/N19-1423.pdf) (“**B**idirectional **E**ncoder **R**epresentations from **T**ransformers”) is a transformer model which was pretrained on about 3.3 billion words (see table below) and then **fine-tuned** for sentiment analysis by adding a lightweight classification layer on top of its pooled output.

|Corpus|Word count|
|---|---|
|**BooksCorpus**|≈ 800 million words|
|**English Wikipedia** (cleaned)|≈ 2 500 million words|

As mentioned in both the [original BERT paper](https://aclanthology.org/N19-1423.pdf) and the [BERT article on Wikipedia (accessed on 12.07.2025)](https://en.wikipedia.org/wiki/BERT_(language_model)), BERT was trained on the **Toronto BooksCorpus (800 M)** plus **English Wikipedia (2.5 B)**. [Wikipedia](https://en.wikipedia.org/wiki/BERT_%28language_model%29?utm_source=chatgpt.com)[ACL Anthology](https://aclanthology.org/N19-1423.pdf?utm_source=chatgpt.com)

During training the text is converted into about 30 000 WordPiece tokens, so the model actually “sees” sub-word pieces rather than raw words - but the totals above give a more intuitive sense of the data scale.


## Step‑by‑Step: How DistilBERT Turns a Text into a Sentiment

This section guides you through the sentiment analysis of the sentence: **“Love this gizmo!”**

After Step 2, DistilBERT has produced a **768‑D “fingerprint”** (the `[CLS]` vector) that encodes the whole sentence’s meaning.  
Steps 3–5 turn that abstract fingerprint into a concrete **Positive / Negative** label.

<table>
<tr>
<th style="width: 10%">Stage</th>
<th style="width: 50%">What DistilBERT does</th>
<th style="width: 40%">Example</th>
</tr>
<tr>
<td><strong>1  Tokenisation – "chopping text into tokens"</strong></td>
<td>Prior to its analysis, an input text is divided into chunks, a.k.a. tokens. <br>Each chunk has an associated ID-number and represents a unique meaning.<br><br>A tokenized text starts with a classification-token (CLS, ID=101) and ends with a separator-token (SEP, ID=102).<br><br>Regular WordPiece-tokens come after the first 100 reserved indices and the special tokens (CLS, SEP, MASK) and are ordered by frequency.<br><br>After the first 106 reserved entries (<code>[PAD]</code>, <code>[UNK]</code>, <code>[CLS]</code>, <code>[SEP]</code>, <code>[MASK]</code>, plus 100 <code>[unused]</code> slots), the rest of BERT's <code>vocab.txt</code> is simply a list of WordPiece tokens sorted by how often they appeared in the BooksCorpus + Wikipedia training data. <a href="https://juditacs.github.io/2019/02/19/bert-tokenization-stats.html">juditacs.github.io</a><br><br>- Lower ID → earlier line → <strong>more frequent token</strong><br>- Higher ID → later line → <strong>less frequent token</strong></td>
<td><em>Love this gizmo!</em> → tokens <br><br><code>['[CLS]', 'love', 'this', 'g', '##iz', '##mo', '!', '[SEP]']</code> → IDs <br><br><code>[101, 3862, 2023, 2290, 12770, 2213, 999, 102]</code> (the rare word <strong>gizmo</strong> is split into <code>g + ##iz + ##mo</code>).<br><br>Because 2023 < 3862, the token "this" occurs more often than "love" in the pre-training corpus—exactly what you'd expect for a common stop-word versus a content verb.</td>
</tr>
<tr>
<td><strong>2  Encoding – "group discussion"</strong></td>
<td>The ID-numbers are fed through 6 Transformer layers. <br>Each layer lets every word listen to every other word and update its meaning. <br><br>Every Transformer layer in DistilBERT outputs a vector with <strong>768 numbers (=dimensions) per token</strong>. <br><br>The final hidden state of <code>[CLS]</code> becomes a 768‑digit-long numeric fingerprint which encodes the meaning of the entire input text.</td>
<td>One dimension (e.g. <em>#512</em>) might measure <em>positivity</em>, another (e.g. <em>#233</em>) might light up for <em>energy gadgets</em> – like the way mixing red & green gives yellow, combining many dimensions encodes subtle meaning.<br><br>These are just examples of how some numbers in the vector may correlate with certain concepts. <br><br>Since DistilBERT starts with <strong>random weights</strong>, training shapes the space, but doesn't label individual coordinates.<br><br>Thus the <strong>coordinate indices in a 768-dimensional DistilBERT vector carry no fixed meaning</strong>; any semantic signal (like positivity) can end up aligned with <em>any</em> combination of axes.</td>
</tr>
<tr>
<td><strong>3 Classification head – "opinion poll"</strong></td>
<td>The fingerprint of the entire input text is fed into a <strong>tiny neural layer</strong> (768 inputs → 2 outputs) which multiplies each of the 768 numbers by a learned weight and adds a bias. <br><br>The two resulting values are called <strong>logits</strong>.<br>These logits can be interpreted as <strong>votes</strong> - one for <em>negative</em>, one for <em>positive</em>.</td>
<td>Imagine two judges—one rooting for <em>Negative</em>, one for <em>Positive</em>. <br>Each judge scans the fingerprint, sums up the signals they care about, and produces a raw score.<br><br><code>logits</code> <br><code>[neg, pos]</code> <br><code>[-1.43, 1.25]</code></td>
</tr>
<tr>
<td><strong>4 Softmax – "turn votes into odds"</strong></td>
<td>Softmax takes the two logits, exponentiates them, and divides by their sum so the outputs become <strong>probabilities that add up to 1</strong>.</td>
<td>It's like converting the judges' raw scores into betting odds you can actually compare. <br><br>1. Exponentiate each logit	e^(-1.43) ≈ 0.2393  <br>e^(1.25) ≈ 3.4903<br><br>2. Sum the exponentials	0.2393 + 3.4903 = 3.7296<br><br>3. Divide each exp by the sum	<br>0.2393 / 3.7296 = 0.064  <br>3.4903 / 3.7296 = 0.936 <br><br><code>neg = 6.4 %</code> <br><code>pos = 93.6 %</code></td>
</tr>
<tr>
<td><strong>5 Decision – "pick the winner"</strong></td>
<td>Whichever probability is higher is the model's answer; we log the confidence too.<br><br>The label with the higher probability is returned, and the probability itself is logged as <strong>confidence</strong>.</td>
<td>highest value = 0.936 <br><br>model output = text sentiment is positive with 93.6 % confidence</td>
</tr>
</table>


### Why logits first, probabilities later?
*Logits separate “scoring” from “probability making.”*  
- They let the model learn **unbounded linear scores** without worrying about the 0‑1 range during training.  
- Softmax then normalises those scores only at the very end, giving a clean probabilistic interpretation. 


Each weight tells how strongly a fingerprint dimension pushes toward Positive or Negative.
- During fine‑tuning the model automatically adjusts those 768×2 weights so the final decision aligns with your training labels.



## Throughput snapshot
* **Laptop:** Apple M2 Pro (2024) – **130 k tweets** inferenced in **~57 s** (≈ 2 270 tweets/s).
* **Server:** 32 vCPU cloud VM – same corpus in **~31 s**.

## Limitations to keep in mind
* **Sarcasm & irony** remain hard, even for large models.  
* **Domain shift:** new slang or emerging topics require re‑training.  
* **Ultra‑short texts:** single emojis give little semantic context, leading to unreliable predictions.
