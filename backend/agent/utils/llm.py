from langchain_groq import ChatGroq
from core.config import Config

# Shared LLM instance
llm = ChatGroq(api_key=Config.GROQ_API_KEY, model="llama-3.3-70b-versatile")

