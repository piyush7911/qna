from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import nest_asyncio
import re
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

nest_asyncio.apply()

app = Flask(__name__)
CORS(app)

# Configure Google Gemini API
GOOGLE_API_KEY = "AIzaSyAbBHbu3pQru4LY8sa-J7oPUBmrL7GBvko"  
genai.configure(api_key=GOOGLE_API_KEY)
embedding_function = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
llm = GoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)

# Initialize ChromaDB
vectorstore = Chroma(
    collection_name="rag_docs",
    embedding_function=embedding_function,
    persist_directory="./chroma_db"
)

def clean_markdown(raw_text):
    raw_text = re.sub(r'Skip to main content\n?', '', raw_text)
    raw_text = re.sub(r'Powered By\nWas this helpful\? Yes No\n?', '', raw_text)
    raw_text = re.sub(r'[#*_`]', '', raw_text)
    raw_text = re.sub(r'!\[.*?\]\(.*?\)', '', raw_text)
    raw_text = re.sub(r'\[.*?\]\(.*?\)', '', raw_text)
    raw_text = re.sub(r'\n+', '\n', raw_text).strip()
    raw_text = re.sub(r' {2,}', ' ', raw_text)
    return raw_text

async def scrape_website(url):
    docs = []
    async with AsyncWebCrawler(verbose=True) as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            excluded_tags=['nav', 'footer', 'aside'],
            remove_overlay_elements=True,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0),
                options={"ignore_links": True}
            ),
        )
        result = await crawler.arun(url=url, config=config)
        raw_markdown = result.markdown_v2.raw_markdown
        cleaned_text = clean_markdown(raw_markdown)
        return cleaned_text

def split_text(text, chunk_size=1200, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def store_data_in_db(text):
    chunks = split_text(text)
    vectorstore.add_texts(texts=chunks)
    vectorstore.persist()

def retrieve_relevant_chunks(query, k=3):
    results = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in results])

def generate_answer(query):
    context = retrieve_relevant_chunks(query)
    prompt = f"""
    You are an expert AI assistant. Use the provided context to answer the question accurately.
    Context:
    {context}
    
    Question: {query}
    Answer:
    """
    response = llm.invoke(prompt)
    return response

@app.route('/scrape', methods=['POST'])
def scrape():
    urls = request.json.get('urls', [])
    if not urls:
        return jsonify({"error": "No URLs provided"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    scraped_data = []
    
    async def process_url(url):
        cleaned_text = await scrape_website(url)
        store_data_in_db(cleaned_text)
        scraped_data.append(f"Scraped {url}")

    async def process_all_urls():
        await asyncio.gather(*[process_url(url) for url in urls])

    loop.run_until_complete(process_all_urls())

    return jsonify({"message": f"Successfully scraped {len(urls)} website(s)!"})


@app.route('/ask', methods=['POST'])
def ask():
    query = request.json.get('query')
    answer = generate_answer(query)
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
