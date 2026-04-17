import os
import glob
import pickle
import faiss
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")

# ── CONFIG ──────────────────────────────────────────
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
INDEX_CACHE   = os.path.join(os.path.dirname(__file__), "faiss_index.pkl")
CHUNK_SIZE    = 400
CHUNK_OVERLAP = 80
TOP_K         = 4

# ── EMBEDDER (loaded once) ───────────────────────────
embedder = SentenceTransformer("all-MiniLM-L6-v2")


# ── CHUNKING ─────────────────────────────────────────
def chunk_text(text):
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) > 50]


# ── BUILD / LOAD INDEX ───────────────────────────────
def build_index(force_rebuild=False):
    if not force_rebuild and os.path.exists(INDEX_CACHE):
        with open(INDEX_CACHE, "rb") as f:
            data = pickle.load(f)
        print("[RAG] Index loaded from cache.")
        return data["index"], data["chunks"]

    print("[RAG] Building index...")
    txt_files = glob.glob(os.path.join(KNOWLEDGE_DIR, "*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {KNOWLEDGE_DIR}")

    all_chunks = []
    for path in txt_files:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").title()
        all_chunks.extend([f"[{name}]\n{c}" for c in chunk_text(text)])

    print(f"[RAG] {len(txt_files)} files → {len(all_chunks)} chunks")

    embeddings = embedder.encode(all_chunks, show_progress_bar=False, convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    with open(INDEX_CACHE, "wb") as f:
        pickle.dump({"index": index, "chunks": all_chunks}, f)

    print("[RAG] Index built and cached.")
    return index, all_chunks


# ── RETRIEVE ─────────────────────────────────────────
def retrieve(query, index, chunks):
    q_emb = embedder.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)
    scores, indices = index.search(q_emb, TOP_K)
    results = [chunks[i] for s, i in zip(scores[0], indices[0]) if i != -1 and s > 0.2]
    return "\n\n---\n\n".join(results) if results else ""


# ── GLOBAL INDEX ─────────────────────────────────────
_index, _chunks = build_index()


def rebuild_index():
    """Call this after adding new .txt files to knowledge_base/"""
    global _index, _chunks
    _index, _chunks = build_index(force_rebuild=True)


# ── MAIN FUNCTION ────────────────────────────────────
def get_chatbot_response(user_message, chat_history=None):
    try:
        context = retrieve(user_message, _index, _chunks)

        context_section = (
            "Use this verified knowledge to answer:\n\n" + context
        ) if context else "Answer from your general agricultural knowledge."

        system_prompt = (
            "You are an expert agricultural assistant specialized in wheat farming and crop diseases.\n"
            "You help farmers diagnose plant diseases, understand symptoms, and get treatment advice.\n\n"
            + context_section +
            "\n\nGuidelines:\n"
            "- Answer clearly and practically for farmers\n"
            "- Keep answers concise but informative\n"
            "- Use bullet points for symptoms, treatments, or steps\n"
            "- If unsure, recommend consulting a local agricultural expert\n"
            "- Always be supportive and encouraging"
        )

        history = [
            {"role": "user",  "parts": system_prompt},
            {"role": "model", "parts": "Understood! I'll use the knowledge base to give accurate, practical advice."}
        ]

        if chat_history:
            for msg in chat_history[:-1]:
                history.append({"role": msg["role"], "parts": msg["content"]})

        chat = model.start_chat(history=history)
        response = chat.send_message(user_message)

        return {"success": True, "message": response.text}

    except Exception as e:
        return {"success": False, "message": f"Sorry, I couldn't process your request. Error: {str(e)}"}