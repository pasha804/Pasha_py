# Required pip install commands:
# pip install pyttsx3 SpeechRecognition wikipedia pyjokes pyautogui PyAudio
# pip install python-dotenv openai google-cloud-texttospeech
# pip install pycaw  # For Windows volume control

import speech_recognition as sr
import pyttsx3
import openai
from google.cloud import texttospeech as gtts
import datetime
import wikipedia
import webbrowser
import os
import platform
import subprocess
import pyautogui
import pyjokes
from dotenv import load_dotenv
import re # For more advanced command parsing

# --- CONFIGURATION ---
load_dotenv()
CONFIG = {
    "assistant_name": "pasha",
    "user_name": "sir",
    "openai_api_key": os.getenv('OPENAI_API_KEY'),
    "default_language": "en-US", # 'en-US' for English, 'hi-IN' for Hindi
}

# --- SETUP ---
# Initialize OpenAI
if CONFIG["openai_api_key"]:
    openai.api_key = CONFIG["openai_api_key"]
else:
    print("Warning: OpenAI API key not found. General Q&A features will be disabled.")

# Initialize Google Cloud TTS Client
try:
    gtts_client = gtts.TextToSpeechClient()
except Exception as e:
    print(f"Warning: Could not initialize Google Cloud TTS. Using offline voice. Error: {e}")
    gtts_client = None

# Initialize offline TTS engine as a fallback
offline_engine = pyttsx3.init()
voices = offline_engine.getProperty('voices')
offline_engine.setProperty('rate', 180)
for voice in voices:
    if "david" in voice.name.lower() or "male" in voice.name.lower():
        offline_engine.setProperty('voice', voice.id)
        break

class Pasha:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000
        self.recognizer.dynamic_energy_threshold = True
        self.current_language = CONFIG["default_language"]

    def speak(self, text, lang=None):
        """
        Convert text to speech using Google Cloud TTS if available, otherwise fallback to offline TTS.
        Dynamically switches language for speech.
        """
        if lang is None:
            lang = self.current_language

        print(f"PASHA ({lang}): {text}")

        # Try Google Cloud TTS first for high-quality voice
        if gtts_client:
            try:
                synthesis_input = gtts.SynthesisInput(text=text)
                voice_params = gtts.VoiceSelectionParams(
                    language_code=lang, ssml_gender=gtts.SsmlVoiceGender.MALE
                )
                audio_config = gtts.AudioConfig(
                    audio_encoding=gtts.AudioEncoding.MP3
                )
                response = gtts_client.synthesize_speech(
                    input=synthesis_input, voice=voice_params, audio_config=audio_config
                )
                
                # Play the audio
                audio_file = "response.mp3"
                with open(audio_file, "wb") as out:
                    out.write(response.audio_content)
                
                if platform.system() == "Windows":
                    os.startfile(audio_file)
                else:
                    subprocess.call(["afplay", audio_file] if platform.system() == "Darwin" else ["xdg-open", audio_file])
                return
            except Exception as e:
                print(f"Google TTS failed: {e}. Falling back to offline engine.")

        # Fallback to offline pyttsx3
        offline_engine.say(text)
        offline_engine.runAndWait()


    def listen(self):
        """Listen for user's command and recognize it in both English and Hindi."""
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                # Try recognizing in the current primary language first
                try:
                    command = self.recognizer.recognize_google(audio, language=self.current_language).lower()
                    print(f"User ({self.current_language}): {command}")
                    return command
                except sr.UnknownValueError:
                    # If it fails, try the other language as a fallback
                    other_lang = 'hi-IN' if self.current_language == 'en-US' else 'en-US'
                    try:
                        command = self.recognizer.recognize_google(audio, language=other_lang).lower()
                        print(f"User (detected {other_lang}): {command}")
                        # Switch language context if spoken in the other language
                        self.current_language = other_lang
                        return command
                    except sr.UnknownValueError:
                        # self.speak("I'm sorry, I didn't catch that.", lang='en-US')
                        return ""
                
            except (sr.WaitTimeoutError, sr.RequestError) as e:
                print(f"Recognition error: {e}")
                return ""
        return ""

    def ask_openai(self, query):
        """Send a query to OpenAI for a general knowledge response."""
        if not openai.api_key:
            return "OpenAI API key is not configured. I cannot answer that."
        try:
            self.speak("Thinking...")
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful and concise assistant named Pasha. Respond in the language of the query."},
                    {"role": "user", "content": query}
                ],
                max_tokens=100
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return f"I encountered an error with my AI core, {CONFIG['user_name']}."
    
    def set_volume(self, level):
        """Set system volume (0-100). Works on Windows and macOS."""
        system = platform.system()
        try:
            if system == "Windows":
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = interface.QueryInterface(IAudioEndpointVolume)
                volume.SetMasterVolumeLevelScalar(level / 100, None)
            elif system == "Darwin": # macOS
                subprocess.call(["osascript", "-e", f"set volume output volume {level}"])
            self.speak(f"Volume set to {level} percent.")
        except Exception as e:
            print(f"Volume control error: {e}")
            self.speak("I am unable to control the volume on this system.")

    def process_command(self, command):
        """Process user's command in both English and Hindi."""
        # Language Switching
        if "switch to hindi" in command:
            self.current_language = 'hi-IN'
            self.speak("ठीक है, मैं अब हिंदी में बात करूँगा।", lang='hi-IN')
            return True
        elif "switch to english" in command or "अंग्रेजी में बोलो" in command:
            self.current_language = 'en-US'
            self.speak("Alright, I will now speak in English.", lang='en-US')
            return True

        # --- English Commands ---
        if self.current_language == 'en-US':
            if any(word in command for word in ["hello", "hi"]):
                self.speak(f"Hello {CONFIG['user_name']}, how can I assist?")
            elif "time" in command:
                self.speak(f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}")
            elif "date" in command:
                self.speak(f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}")
            elif "wikipedia" in command:
                query = command.replace("wikipedia", "").strip()
                self.speak(self.ask_openai(f"Summarize the wikipedia page for {query} in 2 sentences."))
            elif "open" in command:
                # Use regex to find what to open (website or app)
                match = re.search(r'open (.+)', command)
                if match:
                    target = match.group(1).strip()
                    if '.' in target: # Likely a website
                        webbrowser.open(f'https://{target}')
                        self.speak(f"Opening {target}")
                    else: # Likely an application
                        # Simple mapping for common apps
                        app_map = {"visual studio code": "Code", "vs code": "Code"}
                        app_name = app_map.get(target, target)
                        try:
                            if platform.system() == "Windows": os.startfile(app_name)
                            else: subprocess.call(["open", "-a", app_name] if platform.system() == "Darwin" else ["xdg-open", target])
                            self.speak(f"Opening {target}")
                        except Exception:
                            self.speak(f"I couldn't find or open the application {target}.")
            elif "volume to" in command or "set volume" in command:
                match = re.search(r'(\d+)', command)
                if match: self.set_volume(int(match.group(1)))
                else: self.speak("Please specify a volume level from 0 to 100.")
            elif "joke" in command:
                self.speak(pyjokes.get_joke())
            elif any(word in command for word in ["goodbye", "shut down", "exit"]):
                self.speak(f"Goodbye, {CONFIG['user_name']}.")
                return False
            else: # Fallback to OpenAI
                response = self.ask_openai(command)
                self.speak(response)

        # --- Hindi Commands ---
        elif self.current_language == 'hi-IN':
            if "नमस्ते" in command or "हेलो" in command:
                self.speak(f"नमस्ते {CONFIG['user_name']}, मैं आपकी क्या सहायता कर सकता हूँ?")
            elif "समय" in command:
                self.speak(f"अभी {datetime.datetime.now().strftime('%I:%M %p')} बजे हैं")
            elif "तारीख" in command:
                self.speak(f"आज {datetime.datetime.now().strftime('%A, %B %d, %Y')} है")
            elif "विकिपीडिया" in command:
                query = command.replace("विकिपीडिया", "").strip()
                self.speak(self.ask_openai(f"विकिपीडिया पर '{query}' का 2 वाक्यों में सारांश दें।"))
            elif "खोलो" in command or "खोल दो" in command: # "chrome kholo"
                target = command.replace("खोलो", "").replace("खोल दो", "").strip()
                if '.' in target:
                    webbrowser.open(f'https://{target}')
                    self.speak(f"{target} खोल रहा हूँ।")
                else:
                    self.speak("माफ़ कीजिये, मैं अभी हिंदी में एप्लीकेशन नहीं खोल सकता।")
            elif "मजाक" in command or "चुटकुला" in command:
                self.speak("माफ़ कीजिये, मेरे पास अभी हिंदी में चुटकुले नहीं हैं।")
            elif "धन्यवाद" in command:
                self.speak("आपका स्वागत है।")
            elif any(word in command for word in ["अलविदा", "बंद करो"]):
                self.speak(f"अलविदा, {CONFIG['user_name']}.")
                return False
            else: # Fallback to OpenAI
                response = self.ask_openai(command)
                self.speak(response, lang='hi-IN')

        return True


    def run(self):
        """Main loop of the assistant."""
        self.speak(f"{CONFIG['assistant_name']} is online.", lang='en-US')
        while True:
            command = self.listen()
            if not command:
                continue

            # Check for wake word or direct command
            if CONFIG["assistant_name"] in command:
                # Remove wake word to get the actual command
                actual_command = command.replace(CONFIG["assistant_name"], "").strip()
                
                if not actual_command:
                    self.speak("Yes?")
                    continue
                
                if not self.process_command(actual_command):
                    break

if __name__ == "__main__":
    assistant = Pasha()
    assistant.run()