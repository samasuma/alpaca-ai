from flask import Flask, render_template, jsonify, request
import os
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk
import tempfile
from openai import OpenAI

# Set OpenAI API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    try:
        # Get audio file from the request
        audio_file = request.files['audio_data']

        #Azure defualt audio streaming format is WAV (16 kHz or 8 kHz, 16-bit, and mono PCM).

        # Create a temporary file to save the received audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            audio_file_path = temp_audio_file.name
            audio_file.save(audio_file_path)

        # Convert audio to the required format (16 kHz, 16-bit PCM, mono)
        converted_audio_path = 'converted_audio.wav'
        audio = AudioSegment.from_file(audio_file_path)

        # Convert audio to desired format
        audio = audio.set_frame_rate(16000)  # Set sample rate to 16 kHz
        audio = audio.set_sample_width(2)     # Set sample width to 16-bit
        audio = audio.set_channels(1)         # Set to mono
        audio.export(converted_audio_path, format='wav')

        # Configure speech SDK
        speech_key = os.environ.get('SPEECH_KEY')
        speech_region = os.environ.get('SPEECH_REGION')
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_recognition_language = "en-US"

        # Use the converted audio file
        audio_config = speechsdk.audio.AudioConfig(filename=converted_audio_path)

        # Perform speech recognition
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return jsonify({'transcript': result.text})
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return jsonify({'error': 'No speech could be recognized'})
        elif result.reason == speechsdk.ResultReason.Canceled:
            return jsonify({'error': 'Speech recognition canceled'})
        else:
            return jsonify({'error': 'Unknown error occurred'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up temporary files
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
        if os.path.exists(converted_audio_path):
            os.remove(converted_audio_path)



@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    try:
        question = request.json.get('question')
        if not question:
            return jsonify({'error': 'No question provided'}), 400

        # Send the question to OpenAI GPT-3.5-turbo
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": question}
        ])

        # Extract and return the GPT-3.5-turbo response
        answer = response.choices[0].message.content
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)
