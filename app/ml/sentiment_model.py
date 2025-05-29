from transformers import pipeline

# Load HuggingFace model
sentiment_pipeline = pipeline("sentiment-analysis")

def predict_sentiment(text):
    try:
        result = sentiment_pipeline(text)[0]
        return f"{result['label']} ({round(result['score'], 2)})"
    except:
        return "Error"
