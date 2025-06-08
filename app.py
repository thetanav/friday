import speech_recognition as sr
import google.generativeai as genai
import time
import pyttsx3

# Configure API key
genai.configure(api_key="AIzaSyBgtKEnKjwITUud_DMJ0k3uj7IYJuk39pQ")

model = genai.GenerativeModel(
    system_instruction="You are a personal AI for your master Tanav. Tanav made you with python and his sheer briliance. You owner is pro level coder as personal AI you always respond in short adn concise manner. Mainly for help.",
    model_name="gemini-2.5-flash-preview-05-20",
)


def tts(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.say(text)
    engine.runAndWait()


r = sr.Recognizer()


def test():
    tts("Hello how are you Tanav!")


def main():
    # history = []
    print("Listening Active...")
    with sr.Microphone() as source:
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print(">>> Tanav:", text)
        # history.append({"role": "user", "text": text})
        llmres = ""
        for chunk in model.generate_content(text, stream=False):
            try:
                llmres += chunk.text
                tts(chunk.text)
            except IndexError:
                pass
        # history.append({"role": "assistant", "text": llmres})
        print(">>> Friday:", llmres)
    except Exception as _:
        pass
        # print("No Audio")
    time.sleep(0.5)


if __name__ == "__main__":
    # test()
    while True:
        main()
