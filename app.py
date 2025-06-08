import speech_recognition as sr
import time

r = sr.Recognizer()

while True:
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print(text)
    except:
        print("No Audio")
    time.sleep(0.5)
