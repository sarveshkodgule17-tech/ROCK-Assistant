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
    def open_notepad():
        try:
            subprocess.Popen(["notepad.exe"])
            return "Opening Notepad."
        except Exception:
            return "I couldn't launch Notepad."

    @staticmethod
    def open_spotify():
        try:
            # Attempt to launch Windows Store Spotify app
            subprocess.Popen(["start", "spotify:"], shell=True)
            return "Opening Spotify."
        except Exception:
            return "I couldn't launch Spotify."
