# ChatBot-Assistant
## 📚 Oreana AI Chatbot

**Oreana AI Chatbot** is a smart conversational assistant built using a hybrid of traditional ML techniques and LLMs. It can detect intent, extract user information, respond using Google's Gemini Pro (via LangChain), and even store leads locally in a JSON file.

![Streamlit Screenshot Placeholder](https://via.placeholder.com/700x300.png?text=Oreana+AI+Chatbot+Streamlit+UI)

---

### 🚀 Features

* ✅ Intent classification using TF-IDF + Logistic Regression
* ✅ Entity extraction (name, phone, email) using spaCy + regex
* ✅ Lead capture and storage in `leads.json`
* ✅ LLM response generation via Gemini Pro using LangChain
* ✅ Streamlit-based web interface

---

### ⚙️ Tech Stack

* `Python 3.10`
* `scikit-learn`
* `spaCy`
* `streamlit`
* `pandas`
* `langchain`
* `google-generativeai`
* `langchain-google-genai`
* `python-dotenv`

---

### 📦 Installation

#### 🔹 1. Clone the repository

```bash
git clone https://github.com/moni-0712/ChatBot-Assistant.git
cd ChatBot-Assistant
```

#### 🔹 2. Create & activate a Conda environment

```bash
conda create -n oreana_env python=3.10 -y
conda activate oreana_env
```

#### 🔹 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` isn't available, install manually:

```bash
pip install streamlit pandas scikit-learn spacy langchain google-generativeai langchain-google-genai python-dotenv
python -m spacy download en_core_web_sm
```

#### 🔹 4. Add environment variables

Create a `.env` file in the root directory:

```env
GOOGLE_API_KEY=your-gemini-api-key
LANGCHAIN_API_KEY=your-langchain-key-if-needed
```

---

### ▶️ Run the Chatbot

```bash
streamlit run app.py
```

> Type in questions like:
>
> * “Tell me about courses”
> * “My name is Rahul and my phone number is 9876543210”

---

### 🧠 Intent Classes

* `Course Info`
* `Fees`
* `Career Advice`
* `Lead Capture`

Intent is detected using a TF-IDF + Logistic Regression model trained on a small sample.

---

### 📤 Lead Capture

If a message contains a name, email, or phone number, it's stored in `leads.json`. You can view all leads in-app via the **Show Stored Leads** button.

---

### 🗂 Project Structure

```
ChatBot-Assistant/
├── app.py
├── leads.json
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

### 🙋 Author

**Monisha Mukherjee**
🔗 [GitHub](https://github.com/moni-0712)
🔗 [LinkedIn](https://www.linkedin.com/in/monisha-mukherjee-932124240/)

---

### 📄 License

MIT License *(optional – add a LICENSE file if needed)*

---

### ✅ To-Do (Future Improvements)

* Add user authentication
* Integrate database (e.g., SQLite, MongoDB)
* Add multi-turn memory with LangChain agents
* Deploy on Streamlit Cloud / HuggingFace Spaces
