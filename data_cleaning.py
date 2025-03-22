import re

def clean_and_normalize_text(text):
    """
    Cleans and normalizes text by:
    1. Removing special characters and numbers.
    2. Removing extra whitespace.
    """
    #Remove special characters and numbers (keep only letters and whitespace)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    #Remove extra whitespace
    text = ' '.join(text.split())
    return text