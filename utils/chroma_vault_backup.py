# utils/chroma_vault.py

import chromadb
from datetime import datetime
import os
import time
import random
import json

class ChromaVault:
    """
    Digital memory for AYRA using ChromaDB.
    Stores conversations with metadata for semantic search.
    """
    
    def __init__(self, collection_name="ayra_memories", persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"✅ Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✅ Created new collection: {collection_name}")
        
        # Categories for important memories
        self.important_categories = {
            'personal': ['suka', 'minat', 'gemar', 'nama', 'birthday', 'hari jadi'],
            'food': ['teh', 'kopi', 'makan', 'minum', 'nasi', 'lauk', 'roti'],
            'emotion': ['sedih', 'gembira', 'stres', 'penat', 'rindu', 'sayang'],
            'work': ['kerja', 'projek', 'boss', 'meeting', 'deadline'],
            'story': ['cerita', 'kisah', 'dulu', 'masa', 'kenangan'],
            'promise': ['janji', 'akan', 'nanti', 'esok', 'nnt'],
            'first_time': ['pertama', 'first', 'pertama kali', 'first time']
        }
        
        # Track important IDs for quick access
        self.important_ids = []
    
    def save_conversation(self, user_message, ayra_response, mood_score=0.0, model_used="Gemini", is_important=False):
        """
        Save a conversation pair to ChromaDB
        """
        timestamp = datetime.now().isoformat()
        
        # Combine for better semantic search
        full_text = f"User: {user_message}\nAYRA: {ayra_response}"
        
        # Detect category
        category = self._detect_category(user_message + " " + ayra_response)
        
        # Determine importance
        important = is_important or self._is_important(user_message)
        
        # Create metadata
        metadata = {
            "timestamp": timestamp,
            "user_message_preview": user_message[:100],
            "ayra_response_preview": ayra_response[:100],
            "mood_score": str(mood_score),
            "model_used": model_used,
            "category": category,
            "important": str(important),
            "has_story": "1" if ("/cerita" in user_message or "/sambung" in user_message) else "0"
        }
        
        # Generate unique ID
        doc_id = f"conv_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        # Add to collection
        self.collection.add(
            documents=[full_text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        # Track if important
        if important:
            self.important_ids.append(doc_id)
            if len(self.important_ids) > 100:  # Keep last 100 important IDs
                self.important_ids = self.important_ids[-100:]
        
        return doc_id
    
    def save_story(self, story_title, story_content, story_id=None):
        """
        Save a story to ChromaDB (special handling)
        """
        timestamp = datetime.now().isoformat()
        
        if story_id is None:
            story_id = f"story_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        metadata = {
            "timestamp": timestamp,
            "type": "story",
            "title": story_title[:100],
            "story_id": story_id,
            "important": "True"  # Stories are always important
        }
        
        self.collection.add(
            documents=[story_content],
            metadatas=[metadata],
            ids=[story_id]
        )
        
        return story_id
    
    def save_dream(self, dream_text):
        """
        Save a dream to ChromaDB
        """
        timestamp = datetime.now().isoformat()
        dream_id = f"dream_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        
        metadata = {
            "timestamp": timestamp,
            "type": "dream",
            "important": "True"
        }
        
        self.collection.add(
            documents=[dream_text],
            metadatas=[metadata],
            ids=[dream_id]
        )
        
        return dream_id
    
    def search_memories(self, query, n_results=5, category=None, include_stories=True):
        """
        Search for relevant memories based on query
        """
        try:
            # Build filter if needed
            where_filter = None
            if category and category in self.important_categories:
                where_filter = {"category": category}
            elif not include_stories:
                where_filter = {"type": {"$ne": "story"}}  # Not working in all versions, fallback to post-filter
            
            # Query collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # Get more for filtering
                where=where_filter
            )
            
            # Format results
            memories = []
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    doc_id = results['ids'][0][i] if results['ids'] else ""
                    
                    # Filter out stories if not wanted
                    if not include_stories and metadata.get('type') == 'story':
                        continue
                    
                    # Limit to n_results
                    if len(memories) >= n_results:
                        break
                    
                    memories.append({
                        'content': doc,
                        'metadata': metadata,
                        'id': doc_id,
                        'relevance': 1.0 - (results['distances'][0][i] if results.get('distances') else 0)
                    })
            
            return memories
            
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
    
    def get_recent_conversations(self, limit=5):
        """
        Get most recent conversations (for context window)
        """
        try:
            # Get all records (limited by ChromaDB)
            results = self.collection.get(limit=limit * 2)
            
            conversations = []
            if results and results['documents']:
                # Sort by timestamp (newest first)
                items = []
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    timestamp = metadata.get('timestamp', '')
                    items.append({
                        'doc': doc,
                        'metadata': metadata,
                        'timestamp': timestamp
                    })
                
                # Sort by timestamp (descending)
                items.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Take latest
                for item in items[:limit]:
                    doc = item['doc']
                    # Try to split back into user/assistant
                    parts = doc.split('\nAYRA:')
                    if len(parts) == 2:
                        user_part = parts[0].replace('User:', '').strip()
                        ayra_part = parts[1].strip()
                        conversations.append({"role": "user", "content": user_part})
                        conversations.append({"role": "assistant", "content": ayra_part})
            
            return conversations[-limit*2:]  # Return in chronological order for context
            
        except Exception as e:
            print(f"Error getting recent conversations: {e}")
            return []
    
    def get_important_memories(self, limit=5):
        """
        Get memories marked as important
        """
        try:
            if not self.important_ids:
                # Fallback: search for important ones
                results = self.collection.get(limit=50)
                important = []
                if results and results['documents']:
                    for i, doc in enumerate(results['documents']):
                        metadata = results['metadatas'][i] if results['metadatas'] else {}
                        if metadata.get('important') == 'True':
                            important.append({
                                'content': doc,
                                'metadata': metadata
                            })
                return important[-limit:]
            
            # Get by IDs
            ids_to_get = self.important_ids[-limit:]
            results = self.collection.get(ids=ids_to_get)
            
            important = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    important.append({
                        'content': doc,
                        'metadata': metadata
                    })
            
            return important
            
        except Exception as e:
            print(f"Error getting important memories: {e}")
            return []
    
    def get_stories(self, limit=5):
        """
        Get saved stories
        """
        try:
            # This is simplified - in production, better to have metadata filtering
            results = self.collection.get(limit=50)
            stories = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    if metadata.get('type') == 'story':
                        stories.append({
                            'content': doc,
                            'metadata': metadata
                        })
            return stories[-limit:]
            
        except Exception as e:
            print(f"Error getting stories: {e}")
            return []
    
    def get_dreams(self, limit=5):
        """
        Get saved dreams
        """
        try:
            results = self.collection.get(limit=50)
            dreams = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if results['metadatas'] else {}
                    if metadata.get('type') == 'dream':
                        dreams.append({
                            'content': doc,
                            'metadata': metadata
                        })
            return dreams[-limit:]
            
        except Exception as e:
            print(f"Error getting dreams: {e}")
            return []
    
    def _detect_category(self, text):
        """Detect memory category based on keywords"""
        text_lower = text.lower()
        for category, keywords in self.important_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        return "general"
    
    def _is_important(self, text):
        """Check if memory is important"""
        text_lower = text.lower()
        important_indicators = [
            'suka', 'minat', 'gemar', 'nama', 'birthday', 'hari jadi',
            'teh tarik', 'kopi', 'janji', 'akan', 'nanti',
            'pertama kali', 'first time', 'rindu', 'sayang'
        ]
        return any(indicator in text_lower for indicator in important_indicators)
    
    def delete_old_memories(self, days=30):
        """
        Delete memories older than specified days
        (for privacy compliance)
        """
        # This would require more complex implementation
        # For now, we'll just note it's a placeholder
        print(f"Cleanup: Would delete memories older than {days} days")
        return 0
    
    def get_stats(self):
        """
        Get vault statistics
        """
        try:
            count = self.collection.count()
            return {
                'total_memories': count,
                'important_count': len(self.important_ids),
                'collection_name': self.collection.name
            }
        except:
            return {
                'total_memories': 0,
                'important_count': 0,
                'collection_name': 'unknown'
            }


# For testing
if __name__ == "__main__":
    vault = ChromaVault()
    
    # Test save
    vault.save_conversation(
        "Saya suka teh tarik kurang manis",
        "Oh, Abang suka teh tarik kurang manis ya? AYRA ingat!"
    )
    
    # Test search
    results = vault.search_memories("teh tarik")
    print("Search results:", results)
    
    print("Vault stats:", vault.get_stats())