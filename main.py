import time
from core.audio import AudioCore
from core.brain import Brain
from actions.system import SystemActions
from actions.apps import AppActions
from actions.web import WebActions

class RockAssistant:
    def __init__(self):
        print("=========================================")
        print(" ROCK SYSTEM INITIALIZATION ")
        print("=========================================")
        self.audio = AudioCore()
        # Initialize the Brain with llama3, can be changed to mistral depending on what you downloaded in Ollama
        self.brain = Brain(model_name="llama3")
        
        self.audio.speak("System initialized. ROCK is online and ready.")

    def run(self):
        while True:
            try:
                # 1. Wait for wake word
                self.audio.wait_for_wake_word()
                
                # 2. Acknowledge
                self.audio.speak("Yes Sarvesh?")
                
                # 3. Listen for command
                command = self.audio.listen_for_command()
                
                if not command:
                    # Timeout or unverified voice
                    continue
                    
                print(f"[User] {command}")
                cmd_lower = command.lower()
                
                # 4. Action Routing (Hardcoded fast-paths for OS actions)
                response = ""
                if "battery" in cmd_lower:
                    response = SystemActions.get_battery_status()
                elif "cpu" in cmd_lower:
                    response = SystemActions.get_cpu_status()
                elif "memory" in cmd_lower or "ram" in cmd_lower:
                    response = SystemActions.get_memory_status()
                elif "code" in cmd_lower or "vs code" in cmd_lower:
                    response = AppActions.open_vscode()
                elif "unity" in cmd_lower:
                    response = AppActions.open_unity()
                elif "browser" in cmd_lower or "chrome" in cmd_lower:
                    response = AppActions.open_browser()
                elif "stop listening" in cmd_lower or "sleep" in cmd_lower:
                    self.audio.speak("Going offline. Wake me if you need anything.")
                    break
                elif any(kw in cmd_lower for kw in ["search", "look up", "what is", "who is", "tell me about", "how to"]):
                    # Gather context from the web
                    self.audio.speak("Searching the web for you...")
                    web_context = WebActions.search_web(command)
                    response = self.brain.process_command(command, web_context=web_context)
                else:
                    # 5. Pass to LLM Brain if no hardcoded action matches
                    response = self.brain.process_command(command)
                
                # 6. Speak the response
                self.audio.speak(response)
                
            except KeyboardInterrupt:
                print("\n[System] ROCK shutting down.")
                break
            except Exception as e:
                print(f"[System Error] {e}")

if __name__ == "__main__":
    rock = RockAssistant()
    rock.run()
