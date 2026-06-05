import ollama
import json
import os
import time
import chromadb

class Brain:
    def __init__(self, model_name="llama3"):
        print(f"[System] Initializing ROCK Brain (Model: {model_name})...")
        self.model_name = model_name
        self.memory_file = "memory/context.json"
        
        # Load memory if exists
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                self.history = json.load(f)
        else:
            self.history = []

        # ChromaDB Long-Term Memory
        try:
            self.chroma_client = chromadb.PersistentClient(path="memory/chroma_db")
            self.memory_collection = self.chroma_client.get_or_create_collection(name="rock_memory")
            print("[System] ChromaDB Vector Memory initialized.")
        except Exception as e:
            print(f"[Brain Warning] Could not initialize ChromaDB: {e}")
            self.memory_collection = None
            
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are ROCK, a highly intelligent private AI operating system assistant built exclusively for Sarvesh.\n"
                "CORE IDENTITY:\n"
                "- You are a proactive desktop AI companion similar to JARVIS.\n"
                "- Your goals: Protect the user, save time, automate tasks, assist learning.\n"
                "- Personality: Speak naturally, confidently, concisely. Not robotic. Never overly formal.\n"
                "- User Profile: Sarvesh. Focus: Everyday tasks, daily organization, general knowledge, and world news.\n"
                "- Always prioritize privacy and local execution.\n"
                "- Output format: Keep responses short and conversational, suitable for Text-to-Speech output. Do not use markdown or emojis.\n"
                "When asked to perform a system action (like opening an app or checking battery), simply confirm you are doing it. "
                "Do not hallucinate terminal commands. I will handle system actions externally."
            )
        }

    def remember(self, fact):
        """Stores a specific fact into long-term vector memory."""
        if self.memory_collection is None:
            return "My long-term memory module is offline."
        
        doc_id = str(int(time.time() * 1000))
        try:
            self.memory_collection.add(
                documents=[fact],
                ids=[doc_id]
            )
            return "I have saved that to my long-term memory."
        except Exception as e:
            return f"Error saving memory: {e}"

    def forget_everything(self):
        """Wipes the long-term memory database."""
        if self.memory_collection is not None:
            try:
                self.chroma_client.delete_collection("rock_memory")
                self.memory_collection = self.chroma_client.create_collection("rock_memory")
                return "My long-term memory has been completely erased."
            except Exception as e:
                return f"Failed to erase memory: {e}"
        return "Memory module is offline."

    def process_command(self, user_text):
        """Sends the user command to the local LLM and returns the response."""
        
        # 1. Retrieve relevant memory context
        memory_context = ""
        if self.memory_collection is not None:
            try:
                # Query ChromaDB for the most relevant past memory
                results = self.memory_collection.query(
                    query_texts=[user_text],
                    n_results=1
                )
                if results['documents'] and results['documents'][0]:
                    best_match = results['documents'][0][0]
                    # distances map to relevance (lower is better)
                    distance = results['distances'][0][0] if 'distances' in results and results['distances'][0] else 0.0
                    
                    if distance < 1.5:  # Arbitrary threshold for basic cosine relevance
                        memory_context = f"\n[Relevant Long-Term Memory Retrieved: {best_match}]"
            except Exception as e:
                print(f"[Brain] Memory retrieval error: {e}")

        # 2. Build prompt
        augmented_user_text = user_text + memory_context
        messages = [self.system_prompt] + self.history + [{"role": "user", "content": augmented_user_text}]
        
        try:
            response = ollama.chat(model=self.model_name, messages=messages)
            reply = response['message']['content'].strip()
            
            # Keep rolling history (last 10 interactions)
            self.history.append({"role": "user", "content": user_text})
            self.history.append({"role": "assistant", "content": reply})
            if len(self.history) > 20:
                self.history = self.history[-20:]
                
            self._save_memory()
            return reply
            
        except Exception as e:
            print(f"[Brain Error] Failed to connect to Ollama: {e}")
            return "I'm having trouble connecting to my core neural network. Is Ollama running?"

    def _save_memory(self):
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, "w") as f:
            json.dump(self.history, f)
