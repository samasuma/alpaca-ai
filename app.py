from flask import Flask, render_template, jsonify, request, send_file, session
import firebase_admin
from firebase_admin import credentials, auth
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk
import tempfile
from openai import OpenAI
from models import db, Chat, User
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize Firebase Admin SDK
cred = credentials.Certificate(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
firebase_admin.initialize_app(cred)

# Set OpenAI API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Set a secret key for session management

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not (email and password):
        return jsonify({'error': 'Email and password are required'}), 400

    try:
        # Check if user already exists
        try:
            user = auth.get_user_by_email(email)
            return jsonify({'error': 'Email already in use'}), 400
        except auth.UserNotFoundError:
            # User does not exist, proceed with registration
            pass

        # Create a new user with Firebase
        user = auth.create_user(email=email, password=password)
        user_id = user.uid

        # Create local user record
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=email, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not (email and password):
        return jsonify({'error': 'Email and password are required'}), 400

    try:
        # Verify the user with Firebase
        user = auth.get_user_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401

        # Verify the password locally
        local_user = User.query.filter_by(email=email).first()
        if local_user and check_password_hash(local_user.password, password):
            session['user_id'] = local_user.id
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    try:
        audio_file = request.files['audio_data']
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            audio_file_path = temp_audio_file.name
            audio_file.save(audio_file_path)

        converted_audio_path = 'converted_audio.wav'
        audio = AudioSegment.from_file(audio_file_path)
        audio = audio.set_frame_rate(16000)
        audio = audio.set_sample_width(2)
        audio = audio.set_channels(1)
        audio.export(converted_audio_path, format='wav')

        speech_key = os.environ.get('SPEECH_KEY')
        speech_region = os.environ.get('SPEECH_REGION')
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_recognition_language = "en-US"

        audio_config = speechsdk.audio.AudioConfig(filename=converted_audio_path)
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
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
        if os.path.exists(converted_audio_path):
            os.remove(converted_audio_path)

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401
        
        user_message = request.json.get('question')
        if not user_message:
            return jsonify({'error': 'No question provided'}), 400

        # Retrieve chat history with timestamps for the current user
        history = Chat.query.filter_by(user_id=user_id).order_by(Chat.timestamp).all()
        messages = [
            {"role": "user", "content": f"{chat.user_message} (Asked on: {chat.timestamp.strftime('%Y-%m-%d %A %H:%M:%S %Z')} UTC)"}
            for chat in history
        ]

        # Add a system message to set the assistant's tone
        system_message = {
            "role": "system",
            "content": "You are a helpful, mindful, and cheerful assistant here to assist users with their daily needs. Provide responses that are positive and supportive."
        }

        # Add current user message to history
        messages.append({"role": "user", "content": user_message})

        # Include the system message in the context
        messages = [system_message] + messages

        # Send the question to OpenAI GPT-3.5-turbo
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150
        )

        assistant_response = response.choices[0].message.content

        # Save the chat history to the database
        chat = Chat(user_message=user_message, assistant_response=assistant_response, user_id=user_id)
        db.session.add(chat)
        db.session.commit()

        return jsonify({'answer': assistant_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    try:
        text = request.json.get('text')
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        speech_key = os.environ.get('SPEECH_KEY')
        speech_region = os.environ.get('SPEECH_REGION')
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_synthesis_voice_name = 'en-US-AmberNeural'

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            audio_file_path = temp_audio_file.name

            audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file_path)
            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

            if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return send_file(audio_file_path, mimetype='audio/wav')
            elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speech_synthesis_result.cancellation_details
                return jsonify({'error': f'Speech synthesis canceled: {cancellation_details.reason}'}), 500
            else:
                return jsonify({'error': 'Unknown error occurred'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

@app.route('/api/get-chats', methods=['GET'])
def get_chats():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401
    
    chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.timestamp).all()
    chat_list = [
        {
            'id': chat.id,
            'user_message': chat.user_message,
            'assistant_response': chat.assistant_response,
            'timestamp': chat.timestamp.isoformat()
        } for chat in chats
    ]
    return jsonify({'chats': chat_list})

if __name__ == '__main__':
    app.run(debug=True)
