import PyPDF2
import docx
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

nltk.download('punkt')
nltk.download('stopwords')

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_name_email(text):
    # Extract email
    email_pattern = r'[\w\.-]+@[\w\.-]+'
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else None

    # Extract name (Assuming name is in the first few words)
    words = text.split()
    name = " ".join(words[:2]) if len(words) > 1 else None

    return name, email

def preprocess_text(text):
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def calculate_similarity(job_description, resume_text):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([job_description, resume_text])
    similarity_score = cosine_similarity(vectors[0], vectors[1])[0][0]
    
    return round(similarity_score * 100, 2)