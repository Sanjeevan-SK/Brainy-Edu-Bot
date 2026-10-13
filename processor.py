import os
import fitz  # PyMuPDF
import ollama
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using PyMuPDF."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None
    return text

def generate_study_notes(text):
    """Generates concise study notes from text using Ollama."""
    if not text:
        return "No text provided for summarization."
    
    prompt = f"""
    You are an expert academic assistant. Summarize the following text into concise and high-quality study notes.
    Use bullet points, bold key terms, and organize the content into logical sections (e.g., Introduction, Key Concepts, Summary).
    Make it easy for a student to quickly grasp the core ideas.
    
    Text:
    {text[:10000]}  # Ollama context window might be smaller, limiting to 10k for better performance
    """
    
    try:
        response = ollama.chat(model=MODEL, messages=[
            {'role': 'system', 'content': 'You are an academic study assistant.'},
            {'role': 'user', 'content': prompt}
        ])
        return response['message']['content']
    except Exception as e:
        return f"Error generating notes with Ollama: {e}"

def answer_question(context, question):
    """Answers a specific question based on the provided context."""
    if not context or not question:
        return "Please provide both context and a question."

    prompt = f"""
    Based on the following context, answer the user's question accurately.
    If the answer is not in the context, say you don't know based on the document, but provide a general answer if relevant.
    
    Context:
    {context[:10000]}
    
    Question: {question}
    """

    try:
        response = ollama.chat(model=MODEL, messages=[
            {'role': 'system', 'content': 'You are an academic study assistant.'},
            {'role': 'user', 'content': prompt}
        ])
        return response['message']['content']
    except Exception as e:
        return f"Error answering question with Ollama: {e}"
