# utils/chroma_vault_simple.py
# Version ringan tanpa chromadb - untuk deploy

class ChromaVault:
    def __init__(self):
        # Tak buat apa-apa
        pass
    
    def save_conversation(self, user_message, ayra_response, mood_score=0.0, model_used="Gemini", is_important=False):
        # Tak simpan apa-apa
        return None
    
    def search_memories(self, query, n_results=5):
        # Takde memory
        return []
    
    def get_important_memories(self, limit=5):
        return []
    
    def get_stats(self):
        return {'total_memories': 0}