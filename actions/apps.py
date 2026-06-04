import os
import subprocess

class AppActions:
    @staticmethod
    def open_vscode():
        try:
            # Assumes VS Code is in PATH
            subprocess.Popen(["code"], shell=True)
            return "Opening Visual Studio Code."
        except Exception:
            return "I couldn't launch Visual Studio Code. Is it installed and added to the PATH?"

    @staticmethod
    def open_browser():
        try:
            # Opens default browser
            os.startfile("http://www.google.com")
            return "Opening your browser."
        except Exception:
            return "I couldn't launch the browser."

    @staticmethod
    def open_unity():
        try:
            # Assumes Unity Hub is installed in the default location
            unity_path = r"C:\Program Files\Unity Hub\Unity Hub.exe"
            if os.path.exists(unity_path):
                subprocess.Popen([unity_path])
                return "Launching Unity Hub."
            else:
                return "I couldn't find Unity Hub in the default installation path."
        except Exception:
            return "I failed to launch Unity."
