import os
import re
import json
import pandas as pd
import spacy
import streamlit as st
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI


import asyncio
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
# Loading environment variables
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

# Implementing Spacy Model
import spacy.cli
try:
    nlp = spacy.load("en_core_web_sm")
except:
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Dummy intent data for training
intent_data = {
    "Course Info": ["Tell me about courses", "What courses do you offer?", "Give me course details"],
    "Fees": ["What is the fee?", "Tell me the cost", "How much does it cost?"],
    "Career Advice": ["Guide me for my career", "What should I learn?", "Career suggestions?"],
    "Lead Capture": ["My name is John", "Call me at 9876543210", "I want to enroll", "My email is test@gmail.com"]
}
X = []
y = []
for intent, examples in intent_data.items():
    for example in examples:
        X.append(example)
        y.append(intent)

vectorizer = TfidfVectorizer()
X_vect = vectorizer.fit_transform(X)
clf = LogisticRegression()
clf.fit(X_vect, y)

# Define prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Please respond to user queries."),
    ("user", "Question: {question}")
])
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")  # or gemini-2.0-flash if preferred
output_parser = StrOutputParser()
chain = prompt | llm | output_parser

# Utility functions
def classify_intent(text):
    vect = vectorizer.transform([text])
    return clf.predict(vect)[0]

def extract_entities(text):
    doc = nlp(text)
    email = re.search(r"\S+@\S+", text)
    phone = re.search(r"\b\d{10}\b", text)
    name = None
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
            break
    return {
        "name": name,
        "email": email.group() if email else None,
        "phone": phone.group() if phone else None
    }

def store_lead(data):
    filename = "leads.json"
    leads = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            leads = json.load(f)
    leads.append(data)
    with open(filename, "w") as f:
        json.dump(leads, f, indent=4)

def load_leads():
    filename = "leads.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return []

# Streamlit UI
st.title("Oreana AI Chatbot")

user_input = st.text_input("Ask me anything...")

if user_input:
    intent = classify_intent(user_input)
    st.markdown("### Detected Intent:")
    st.write(intent)

    entities = extract_entities(user_input)
    st.markdown("### Extracted Entities:")
    st.json(entities)

    # Store if valid lead
    if intent == "Lead Capture" and any(entities.values()):
        store_lead(entities)

    # Response
    if intent == "Lead Capture" and entities["name"]:
        response = f"Okay {entities['name']}, thanks for providing your information. I have saved your name, email and phone number.\nWhich course are you interested in enrolling in?"
    else:
        response = chain.invoke({"question": user_input})

    st.markdown("### Bot Response:")
    st.write(response)

# Button to show stored leads
if st.button("Show Stored Leads"):
    leads = load_leads()
    if leads:
        df = pd.DataFrame(leads)
        st.dataframe(df)
    else:
        st.write("No leads captured yet.")
