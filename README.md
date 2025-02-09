
# Website Content QnA Tool

This is a Flask-based Q&A system that scrapes website content, stores it in a database, and answers user queries using AI.

## 🚀 Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/piyush7911/qna-backend
cd qna-backend
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
pip install -U crawl4ai
pip install nest_asyncio
```

### 3️⃣ Setup Crawl4AI
```bash
crawl4ai-setup
crawl4ai-doctor
```

### 4️⃣ Add Google Gemini API Key
Before running the backend, open `app.py` and paste your Google Gemini API Key inside:

### 5️⃣ Start the Backend
```bash
python app.py
```

## 🖥️ Start the Frontend

### 1️⃣ Move to the Frontend Directory
```bash
cd frontend
```

### 2️⃣ Install Dependencies
```bash
npm install
npx shadcn@latest init
```

### 3️⃣ Start the Frontend
```bash
npm run dev
```

### 4️⃣ Open Browser and Start Chatting
Open `http://localhost:3001` in your browser. Start chatting with the chatbot! 🎉
