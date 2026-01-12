"""
Test Data Generator
Scrapes Wikipedia and creates 3 groups of 3k terms with overlap
"""

import requests
import json
import nltk
from nltk.tokenize import word_tokenize
from collections import Counter
import random

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')

print("STARTED")

def scrape_wikipedia_text(num_articles=10):
    """Scrape random Wikipedia articles"""
    all_text = ""
    
    for _ in range(num_articles):
        try:
            # Get random article
            response = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/random/summary",
                headers={
                    "User-Agent": "termDB/0.1 (test@example.com)",
                    "Accept": "application/json",
                },
                timeout=10,
            )

            data = response.json()
            
            # Extract text
            if 'extract' in data:
                all_text += " " + data['extract']
            
            print(f"Scraped: {data.get('title', 'Unknown')}")
        except Exception as e:
            print(f"Error scraping: {e}")
    
    return all_text

def extract_terms(text, min_length=3):
    """Tokenize and extract valid terms"""
    tokens = word_tokenize(text.lower())
    
    # Filter: alphabetic, min length, no stopwords
    valid_tokens = [
        t for t in tokens 
        if t.isalpha() and len(t) >= min_length
    ]
    
    # Get frequency
    freq = Counter(valid_tokens)
    
    # Return most common unique terms
    return [term for term, _ in freq.most_common(10000)]

def generate_test_groups(all_terms, group_size=1000):
    max_size = len(all_terms) // 3
    if max_size == 0:
        raise RuntimeError("No terms extracted")

    group_size = min(group_size, max_size)
    random.shuffle(all_terms)

    group1 = all_terms[:group_size]

    overlap_size = int(group_size * 0.7)
    group2 = random.sample(group1, overlap_size)
    group2.extend(all_terms[group_size:group_size + (group_size - overlap_size)])

    g1_sample = int(group_size * 0.5)
    g2_sample = int(group_size * 0.2)
    group3 = random.sample(group1, g1_sample)
    group3.extend(random.sample(group2, g2_sample))
    group3.extend(
        all_terms[group_size * 2: group_size * 2 + (group_size - g1_sample - g2_sample)]
    )

    return group1, group2, group3


def create_term_objects(terms):
    """Convert terms to expected format"""
    return [
        {"term": term, "meaning": f"Definition of {term}"}
        for term in terms
    ]

print("Scraping Wikipedia...")
text = scrape_wikipedia_text(num_articles=30)

print("Extracting terms...")
all_terms = extract_terms(text)
print(f"Extracted {len(all_terms)} unique terms")


while len(all_terms) < 4000:
    print(f"Warning: Not enough terms, we only have {len(all_terms)}, scraping more...")
    text += scrape_wikipedia_text(num_articles=5)
    all_terms = extract_terms(text)

print("Generating test groups...")
g1, g2, g3 = generate_test_groups(all_terms)

# Convert to objects
data = {
    "group1": create_term_objects(g1),
    "group2": create_term_objects(g2),
    "group3": create_term_objects(g3)
}

# Calculate overlaps
s1, s2, s3 = set(g1), set(g2), set(g3)
print(f"\nGroup 1: {len(g1)} terms")
print(f"Group 2: {len(g2)} terms ({len(s1 & s2)} overlap with G1)")
print(f"Group 3: {len(g3)} terms ({len(s1 & s3)} overlap with G1, {len(s2 & s3)} with G2)")

# Save to JSON
with open('test_data.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSaved to test_data.json")
