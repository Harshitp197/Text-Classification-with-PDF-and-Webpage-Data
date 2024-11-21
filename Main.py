import os
import PyPDF2
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.metrics import classification_report, accuracy_score
import requests
from bs4 import BeautifulSoup

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Step 1: Extract Text from PDFs
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""

        # Check if the PDF is encrypted
        if reader.is_encrypted:
            try:
                reader.decrypt("")  # Decrypt using an empty password, adjust if you have a password
            except:
                print(f"Failed to decrypt {pdf_path}. Skipping this file.")
                return None

        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
    return text

# Step 1 (Alternative): Extract Text from a Webpage
def extract_text_from_webpage(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract text from all relevant HTML elements
    text = soup.get_text(separator=' ')
    return text

# Step 2: Preprocess the Text Data
def preprocess_text(text):
    # Convert text to lowercase
    text = text.lower()
    # Tokenize the text
    tokens = word_tokenize(text)
    # Remove punctuation
    tokens = [word for word in tokens if word.isalnum()]
    # Remove stopwords
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    return ' '.join(tokens)

# Step 3: Create a Dataset
def create_dataset(directory):
    data = []
    labels = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    
    for label in labels:
        folder_path = os.path.join(directory, label)
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                text = extract_text_from_pdf(pdf_path)
                if text:  # Skip if text extraction failed
                    preprocessed_text = preprocess_text(text)
                    data.append((preprocessed_text, label))
    
    return pd.DataFrame(data, columns=['text', 'label'])

# Step 4: Train an SVM Classifier
def train_classifier(df):
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42)

    # Convert text data into TF-IDF features
    vectorizer = TfidfVectorizer()
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Train an SVM classifier
    classifier = SVC(kernel='linear')
    classifier.fit(X_train_tfidf, y_train)

    # Predict and evaluate the model
    y_pred = classifier.predict(X_test_tfidf)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred, labels=df['label'].unique()))

    return vectorizer, classifier

# Step 5: Classify New PDF or Webpage
def classify_text(text, vectorizer, classifier):
    preprocessed_text = preprocess_text(text)
    text_tfidf = vectorizer.transform([preprocessed_text])
    prediction = classifier.predict(text_tfidf)
    return prediction[0]

# Putting It All Together
if __name__ == "__main__":
    # Step 1: Get the dataset directory from the user
    dataset_directory = input("Enter the path to your dataset directory: ")

    # Step 2: Create the dataset
    df = create_dataset(dataset_directory)

    # Ensure that the dataset contains exactly 11 categories
    if len(df['label'].unique()) != 11:
        print("Warning: The dataset does not contain exactly 11 categories.")
    
    # Step 3: Train the classifier
    vectorizer, classifier = train_classifier(df)

    # Step 4: Get input from the user for classification (PDF or URL)
    input_type = input("Would you like to classify a 'PDF' or 'Webpage'? ").strip().lower()
    
    if input_type == 'pdf':
        pdf_path = input("Enter the path to the PDF you want to classify: ")
        text = extract_text_from_pdf(pdf_path)
    elif input_type == 'webpage':
        url = input("Enter the URL of the webpage you want to classify: ")
        text = extract_text_from_webpage(url)
    else:
        print("Invalid input type. Please enter 'PDF' or 'Webpage'.")
        exit()

    # Step 5: Classify the new text (from PDF or Webpage)
    if text:
        category = classify_text(text, vectorizer, classifier)
        print(f'The text belongs to category: {category}')
    else:
        print("Unable to classify due to text extraction failure.")
