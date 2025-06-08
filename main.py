import streamlit as st
import google.generativeai as genai
import os
import speech_recognition as sr
from gtts import gTTS
import io

# Configure API key
genai.configure(api_key="AIzaSyBgtKEnKjwITUud_DMJ0k3uj7IYJuk39pQ")

# Set up the model
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 500,  # Reduced for shorter responses
}

# Set up the safety settings
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-preview-05-20",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

# Initialize chat history and TTS state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "speak_aloud_active" not in st.session_state:
    st.session_state.speak_aloud_active = True  # TTS active by default

st.set_page_config(layout="wide")
st.title("Gemini Chatbot")


def send_message(prompt):
    st.session_state.messages.append({"role": "user", "text": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate a response from the model
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        # Prepend instruction for shorter response
        llm_prompt = "Please respond concisely: " + prompt
        for chunk in model.generate_content(llm_prompt, stream=True):
            try:
                full_response += chunk.text
            except IndexError:
                # Handle cases where chunk.text might not be available
                pass
            message_placeholder.markdown(full_response + " ")
        message_placeholder.markdown(full_response)

        # Text-to-Speech for assistant's response
        if st.session_state.speak_aloud_active:
            try:
                tts = gTTS(full_response, lang="en")
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                st.info("Attempting to play audio...")
                st.audio(audio_fp, format="audio/mp3", start_time=0)
            except Exception as e:
                st.warning(f"Could not generate audio for response: {e}")

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "text": full_response})


# Create two columns for layout
col_left, col_right = st.columns([1, 3])  # Left column for options, Right for chat

with col_left:
    st.markdown("### Voice Input")
    # --- Voice Input Setup ---
    if "is_listening" not in st.session_state:
        st.session_state.is_listening = False

    start_button = st.button("Start Voice Input")
    stop_button = st.button("Stop Voice Input")

    if start_button and not st.session_state.is_listening:
        st.session_state.is_listening = True
        st.rerun()  # Trigger rerun to start listening

    if stop_button and st.session_state.is_listening:
        st.session_state.is_listening = False
        st.warning("Voice input stopped.")
        st.rerun()  # Trigger rerun to update UI

    if st.session_state.is_listening:
        r = sr.Recognizer()
        st.info("Listening for your voice... (Speak now)")
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source)  # Adjust for ambient noise
                audio = r.listen(
                    source, phrase_time_limit=5
                )  # Listen for a phrase, with a 5-second limit

            transcript = r.recognize_google(audio)
            st.success(f"Transcription: {transcript}")
            send_message(transcript)

        except sr.UnknownValueError:
            st.error("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            st.error(
                f"Could not request results from Google Speech Recognition service; {e}"
            )
        except Exception as e:
            st.error(f"An unexpected error occurred during audio processing: {e}")
        finally:
            # After one listening attempt (success or failure), stop listening mode
            st.session_state.is_listening = False
            st.rerun()  # Trigger rerun to update UI

    st.markdown("### Speaking Options")
    speak_aloud_toggle = st.checkbox(
        "Speak AI Responses Aloud", value=st.session_state.speak_aloud_active
    )
    if speak_aloud_toggle != st.session_state.speak_aloud_active:
        st.session_state.speak_aloud_active = speak_aloud_toggle
        st.rerun()

with col_right:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])

    # Accept user input for text chat
    if prompt := st.chat_input("Ask me anything..."):
        send_message(prompt)
