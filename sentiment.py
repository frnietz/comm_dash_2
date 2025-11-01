from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()
def score_headlines(items):
    out = []
    for it in items:
        title = (it.get('title') or '').strip()
        vs = analyzer.polarity_scores(title) if title else {'compound': 0.0}
        it2 = dict(it)
        it2['sentiment'] = vs['compound']
        out.append(it2)
    return out
