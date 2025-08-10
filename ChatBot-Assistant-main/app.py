import os
import re
import json
import pandas as pd
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
    ("system", "You are a helpful assistant for Oreana Educational Institute. Provide helpful responses about courses, fees, and career guidance."),
    ("user", "Question: {question}")
])

try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    llm_available = True
except Exception as e:
    st.error(f"LLM initialization failed: {str(e)}")
    llm_available = False

# Utility functions
def classify_intent(text):
    vect = vectorizer.transform([text])
    return clf.predict(vect)[0]

def extract_entities(text):
    """Extract entities using regex patterns - no SpaCy needed!"""
    
    # Email regex
    email = re.search(r"\S+@\S+", text)
    
    # Phone regex (10 digits)
    phone = re.search(r"\b\d{10}\b", text)
    
    # Name extraction using multiple patterns
    name = None
    name_patterns = [
        r'my name is (\w+(?:\s+\w+)*)',
        r'i am (\w+(?:\s+\w+)*)',
        r'call me (\w+(?:\s+\w+)*)',
        r'i\'m (\w+(?:\s+\w+)*)',
        r'name:\s*(\w+(?:\s+\w+)*)',
        r'this is (\w+(?:\s+\w+)*)',
        r'hello.*?(\w+(?:\s+\w+)*?)(?:\s|$)',  # "Hello, I'm John"
    ]
    
    for pattern in name_patterns:
        name_match = re.search(pattern, text.lower())
        if name_match:
            potential_name = name_match.group(1).strip().title()
            # Filter out common words that aren't names
            if potential_name.lower() not in ['the', 'a', 'an', 'this', 'that', 'here', 'there']:
                name = potential_name
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
            try:
                leads = json.load(f)
            except json.JSONDecodeError:
                leads = []
    leads.append(data)
    with open(filename, "w") as f:
        json.dump(leads, f, indent=4)

def load_leads():
    filename = "leads.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

# Streamlit UI
st.title("🎓 Oreana AI Chatbot")
st.caption("Your AI Assistant for Course Information & Career Guidance")

# Input section
user_input = st.text_input("Ask me anything about courses, fees, or career advice...")

if user_input:
    # Process user input
    intent = classify_intent(user_input)
    entities = extract_entities(user_input)
    
    # Display results in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Detected Intent:")
        st.success(intent)
    
    with col2:
        st.markdown("### 📋 Extracted Entities:")
        st.json(entities)

    # Store lead if valid
    if intent == "Lead Capture" and any(entities.values()):
        store_lead(entities)
        st.success("✅ Lead information saved!")

    # Generate response
    if intent == "Lead Capture" and entities["name"]:
        response = f"Hello {entities['name']}! 👋 Thanks for providing your information. I've saved your details.\n\nWhich course are you interested in? We offer:\n• Technology & Programming\n• Business & Management\n• Creative Design\n• Data Science & AI\n\nHow can I help you choose the right path?"
    elif llm_available:
        try:
            response = chain.invoke({"question": user_input})
        except Exception as e:
            # Fallback responses
            fallback_responses = {
                "Course Info": "We offer comprehensive courses in Technology, Business, Creative Design, and Data Science. Each program is designed with industry experts to provide practical, job-ready skills. Would you like details about any specific field?",
                "Fees": "Our course fees vary by program and duration. We offer flexible payment plans and scholarships. Contact us for detailed pricing: courses start from ₹15,000 to ₹1,50,000 depending on the specialization.",
                "Career Advice": "I'd love to help guide your career! What field interests you most? Whether it's tech, business, creative, or data - I can suggest the best learning path and career opportunities.",
                "General": "I'm here to help with information about our courses, fees, and career guidance. What would you like to know more about?"
            }
            response = fallback_responses.get(intent, "I'm here to help! Ask me about courses, fees, or career advice.")
    else:
        # Fallback when LLM is not available
        fallback_responses = {
            "Course Info": "We offer comprehensive courses in Technology, Business, Creative Design, and Data Science. Each program includes hands-on projects and industry mentorship.",
            "Fees": "Our course fees range from ₹15,000 to ₹1,50,000 based on the program. We offer EMI options and scholarships for deserving students.",
            "Career Advice": "I'd be happy to guide your career path! What field interests you? Technology, Business, Creative, or Data Science?",
            "General": "Welcome to Oreana! I can help you with course information, fees, and career guidance. What would you like to know?"
        }
        response = fallback_responses.get(intent, "I'm here to help with your educational journey!")

    st.markdown("### 🤖 Bot Response:")
    st.write(response)

# Sidebar for admin panel
st.sidebar.markdown("## 📊 Admin Panel")

if st.sidebar.button("📋 Show Stored Leads"):
    leads = load_leads()
    if leads:
        st.sidebar.success(f"Total Leads: {len(leads)}")
        df = pd.DataFrame(leads)
        st.dataframe(df)
        
        # Download leads as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Leads CSV",
            data=csv,
            file_name="leads.csv",
            mime="text/csv"
        )
    else:
        st.sidebar.info("No leads captured yet.")

# Clear leads button (admin)
if st.sidebar.button("🗑️ Clear All Leads", type="secondary"):
    if os.path.exists("leads.json"):
        os.remove("leads.json")
    st.sidebar.success("All leads cleared!")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 Features:")
st.sidebar.markdown("✅ Intent Classification")
st.sidebar.markdown("✅ Entity Extraction") 
st.sidebar.markdown("✅ Lead Capture")
st.sidebar.markdown("✅ AI Responses")
