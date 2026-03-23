import os
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

DB_PATH = "db"

# 1. Загрузка всех файлов из папки data
def load_documents():
    docs = []
    for file in os.listdir("data"):
        path = os.path.join("data", file)

        if file.endswith(".txt"):
            docs.extend(TextLoader(path).load())

        elif file.endswith(".pdf"):
            docs.extend(PyPDFLoader(path).load())

    return docs

# 2. Создание базы (делается 1 раз)
def build_db():
    documents = load_documents()

    splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    texts = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings()

    db = Chroma.from_documents(
        texts,
        embeddings,
        persist_directory=DB_PATH
    )

    db.persist()
    print("База создана")

# 3. Загрузка базы
def load_db():
    embeddings = HuggingFaceEmbeddings()
    return Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

# 4. Генерация ответа через Ollama
import requests

def generate_answer(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# 5. Основная функция
db = None

def ask(question):
    global db

    if db is None:
        db = load_db()

    docs = db.similarity_search(question, k=3)
    context = "\n".join([d.page_content for d in docs])

    prompt = f"""
    Отвечай только по этому контексту:
    {context}

    Вопрос: {question}
    """

    return generate_answer(prompt)