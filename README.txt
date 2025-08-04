PASHA - Personal Assistant for Smart Home Automation
==============================================

Installation Guide
------------------

1. Make sure you have Python 3.7 or higher installed on your system.

2. Install the required dependencies by running these commands:

   pip install pyttsx3
   pip install SpeechRecognition
   pip install wikipedia
   pip install pyjokes
   pip install pyautogui
   pip install PyAudio
   pip install python-dotenv
   pip install --upgrade google-cloud-texttospeech openai
   pip install pycaw

Note: If you have trouble installing PyAudio, you might need to:
- Windows: pip install pipwin && pipwin install pyaudio
- Linux: sudo apt-get install python3-pyaudio
- macOS: brew install portaudio && pip install pyaudio

Starting PASHA
-------------

1. Make sure your microphone is connected and working.

2. Open a terminal/command prompt in the project directory.

3. Run the assistant:
   python pasha.py

4. Wait for the "PASHA is now online and ready to assist" message.

5. You can now use PASHA in two ways:
   - Say "pasha" and wait for "Yes, sir?" before giving your command
   - Include "pasha" in your command, like "pasha tell me the time"

Troubleshooting
--------------

1. If PASHA can't hear you:
   - Check your microphone settings
   - Speak clearly and at a normal pace
   - Use PASHA in a quieter environment

2. If you get a PyAudio error:
   - Follow the PyAudio installation instructions above for your operating system

3. If some features don't work:
   - Make sure all dependencies are installed correctly
   - Check your internet connection for web-based features