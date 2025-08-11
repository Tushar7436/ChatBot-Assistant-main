# app.py
# This file contains the complete FastAPI application with CORS policy, replacing the API functionality
# from the original Streamlit script. The Streamlit UI would now be a separate client.

import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
import uvicorn

# Loading environment variables
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

# --- FIX for Render deployment issue with read-only filesystem ---
# This redirects Cargo's home and pip's cache directory to a writable location
# This is necessary because some dependencies (like Matplotlib which uses Rust)
# try to write to a read-only directory during the build process.
os.environ['CARGO_HOME'] = '/tmp/cargo'
os.environ['PIP_CACHE_DIR'] = '/tmp/pip_cache'
# --- END FIX ---

# Dummy intent data for training
intent_data = {
    "Course Info": ["Tell me about courses", "What courses do you offer?", "Give me course details"],
    "Fees": ["What is the fee?", "Tell me the cost", "How much does it cost?"],
    "Career Advice": ["Guide me for my career", "What should I learn?", "Career suggestions?"],
    "Lead Capture": ["My name is John", "Call me at 9876543210", "I want to enroll", "My email is test@gmail.com"]
}

# Training the intent classification model
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

# Define prompt template for the LLM
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant for Oreana Educational Institute. Provide helpful responses about courses, fees, and career guidance."),
    ("user", "Question: {question}")
])

# Initialize the LLM chain
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    llm_available = True
except Exception as e:
    print(f"LLM initialization failed: {str(e)}")
    llm_available = False

# Utility functions
def classify_intent(text):
    """Classifies the user's intent using a trained TF-IDF and Logistic Regression model."""
    vect = vectorizer.transform([text])
    return clf.predict(vect)[0]

def extract_entities(text):
    """
    Extracts entities like name, email, and phone number from the user's message
    using regex patterns.
    """
    email = re.search(r"\S+@\S+", text)
    phone = re.search(r"\b\d{10}\b", text)
    name = None
    name_patterns = [
        r'my name is (\w+(?:\s+\w+)*)',
        r'i am (\w+(?:\s+\w+)*)',
        r'call me (\w+(?:\s+\w+)*)',
        r'i\'m (\w+(?:\s+\w+)*)',
        r'name:\s*(\w+(?:\s+\w+)*)',
        r'this is (\w+(?:\s+\w+)*)',
        r'hello.*?(\w+(?:\s+\w+)*?)(?:\s|$)',
    ]
    for pattern in name_patterns:
        name_match = re.search(pattern, text.lower())
        if name_match:
            potential_name = name_match.group(1).strip().title()
            if potential_name.lower() not in ['the', 'a', 'an', 'this', 'that', 'here', 'there']:
                name = potential_name
                break
    return {
        "name": name,
        "email": email.group() if email else None,
        "phone": phone.group() if phone else None
    }

def store_lead(data):
    """Saves lead information to a JSON file."""
    filename = "leads.json"
    leads = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                leads = json.load(f)
            except json.JSONDecodeError:
                leads = []
    leads.append(data)
    with open(filename, "w") as f:
        json.dump(leads, f, indent=4)

def get_fallback_response(intent):
    """Provides a predefined response if the LLM is unavailable or fails."""
    fallback_responses = {
        "Course Info": "We offer comprehensive courses in Technology, Business, Creative Design, and Data Science. Each program is designed with industry experts to provide practical, job-ready skills. Would you like details about any specific field?",
        "Fees": "Our course fees vary by program and duration. We offer flexible payment plans and scholarships. Contact us for detailed pricing: courses start from ₹15,000 to ₹1,50,000 depending on the specialization.",
        "Career Advice": "I'd love to help guide your career! What field interests you most? Whether it's tech, business, creative, or data - I can suggest the best learning path and career opportunities.",
        "General": "I'm here to help with information about our courses, fees, and career guidance. What would you like to know more about?",
        "Lead Capture": "Thanks for providing your information! What course are you interested in?"
    }
    return fallback_responses.get(intent, fallback_responses["General"])

# Instantiate FastAPI app
app = FastAPI(title="Oreana AI Chatbot API")

# Configure CORS middleware to allow cross-origin requests
origins = [
    "*"  # Allows all origins. In a production environment, you should replace this with your actual frontend URL(s).
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a Pydantic model for the request body
class ChatRequest(BaseModel):
    message: str

# Define a Pydantic model for the response body
class ApiResponse(BaseModel):
    intent: str
    entities: dict
    response: str
    status: str

@app.post("/chat", response_model=ApiResponse)
async def chat_api(request: ChatRequest):
    """
    API endpoint to handle chatbot requests. It classifies intent, extracts
    entities, stores leads, and generates a response using an LLM or a fallback.
    """
    user_message = request.message
    
    intent = classify_intent(user_message)
    entities = extract_entities(user_message)

    if intent == "Lead Capture" and any(entities.values()):
        store_lead(entities)

    if intent == "Lead Capture" and entities["name"]:
        response = f"Hello {entities['name']}! 👋 Thanks for providing your information. I've saved your details.\n\nWhich course are you interested in? We offer:\n• Technology & Programming\n• Business & Management\n• Creative Design\n• Data Science & AI\n\nHow can I help you choose the right path?"
    else:
        if llm_available:
            try:
                response = chain.invoke({"question": user_message})
            except Exception as e:
                print(f"LLM chain invocation failed: {str(e)}")
                response = get_fallback_response(intent)
        else:
            response = get_fallback_response(intent)
    
    return ApiResponse(
        intent=intent,
        entities=entities,
        response=response,
        status="success"
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
