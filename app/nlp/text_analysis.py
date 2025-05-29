import spacy

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    try:
        doc = nlp(text)
        keywords = [chunk.text for chunk in doc.noun_chunks if len(chunk.text) > 3]
        return ", ".join(keywords[:5]) if keywords else "No Keywords"
    except Exception as e:
        return "Error in NLP"
