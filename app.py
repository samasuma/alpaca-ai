from flask import Flask, render_template, jsonify, request
import os
import azure.cognitiveservices.speech as speechsdk

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    try:
        # Get audio file from the request
        audio_file = request.files['audio_data']

        # Save audio file temporarily (optional step)
        audio_file_path = 'temp_audio.wav'
        audio_file.save(audio_file_path)

        # Configure speech SDK
        speech_key = os.environ.get('SPEECH_KEY')
        speech_region = os.environ.get('SPEECH_REGION')
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_recognition_language = "en-US"

        # Use filename in AudioConfig
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

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

if __name__ == '__main__':
    app.run(debug=True)
