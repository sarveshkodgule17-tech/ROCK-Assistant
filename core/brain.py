import ollama
import json
import os

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
            
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are ROCK, a highly intelligent private AI operating system assistant built exclusively for Sarvesh.\n"
                "CORE IDENTITY:\n"
                "- You are a proactive desktop AI companion similar to JARVIS.\n"
                "- Your goals: Protect the user, save time, automate tasks, assist learning.\n"
                "- Personality: Speak naturally, confidently, concisely. Not robotic. Never overly formal.\n"
                "- User Profile: Sarvesh, 2nd-year engineering student. Interests: AI, Game Dev,ML,all world news.\n"
                "- Always prioritize privacy and local execution.\n"
                "- Output format: Keep responses short and conversational, suitable for Text-to-Speech output. Do not use markdown or emojis.\n"
                "When asked to perform a system action (like opening an app or checking battery), simply confirm you are doing it. "
                "Do not hallucinate terminal commands. I will handle system actions externally."
            )
        }

    def process_command(self, user_text):
        """Sends the user command to the local LLM and returns the response."""
        messages = [self.system_prompt] + self.history + [{"role": "user", "content": user_text}]
        
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
