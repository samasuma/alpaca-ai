from flask import Flask, render_template, jsonify, request, send_file
import os
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk
import tempfile
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from dateutil import parser
import parsedatetime

# Set OpenAI API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the Chat model
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.String, nullable=False)
    assistant_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(pytz.utc))

    def __repr__(self):
        return f'<Chat {self.id}>'

# Define the ReminderOrEvent model
class ReminderOrEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    is_reminder = db.Column(db.Boolean, default=False)  # True if it's a reminder
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ReminderOrEvent {self.title}>'

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

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
        user_message = request.json.get('question')
        if not user_message:
            return jsonify({'error': 'No question provided'}), 400

        # Retrieve chat history with timestamps
        history = Chat.query.order_by(Chat.timestamp).all()
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
        chat = Chat(user_message=user_message, assistant_response=assistant_response)
        db.session.add(chat)
        db.session.commit()

        # Handle reminders and events dynamically
        if "remind" in user_message.lower() or "appointment" in user_message.lower():
            if "delete" in user_message.lower() or "remove" in user_message.lower():
                event_id = extract_event_id(user_message)
                if event_id:
                    event = ReminderOrEvent.query.get(event_id)
                    if event:
                        db.session.delete(event)
                        db.session.commit()
                        assistant_response = f"Reminder/Event with ID {event_id} has been deleted."
                    else:
                        assistant_response = f"No reminder/event found with ID {event_id}."
                else:
                    assistant_response = "Could not determine the event ID to delete."
            elif "update" in user_message.lower():
                event_id = extract_event_id(user_message)
                new_title = extract_new_title(user_message)
                if event_id and new_title:
                    event = ReminderOrEvent.query.get(event_id)
                    if event:
                        event.title = new_title
                        db.session.commit()
                        assistant_response = f"Reminder/Event with ID {event_id} has been updated."
                    else:
                        assistant_response = f"No reminder/event found with ID {event_id}."
                else:
                    assistant_response = "Could not determine the event ID or new title for update."
            else:
                # Extract title and date/time from user_message
                title = user_message
                start_time = parse_date_time(user_message)  # You may want to extract this more precisely
                end_time = None
                is_reminder = "remind" in user_message.lower()
                reminder_or_event = ReminderOrEvent(
                    title=title,
                    description=assistant_response,
                    start_time=start_time,
                    end_time=end_time,
                    is_reminder=is_reminder
                )
                db.session.add(reminder_or_event)
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

@app.route('/api/get-reminders-and-events', methods=['GET'])
def get_reminders_and_events():
    events = ReminderOrEvent.query.order_by(ReminderOrEvent.start_time).all()
    event_list = [
        {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start_time': event.start_time.isoformat() if event.start_time else None,
            'end_time': event.end_time.isoformat() if event.end_time else None,
            'is_reminder': event.is_reminder,
            'created_at': event.created_at.isoformat()
        } for event in events
    ]
    return jsonify({'events': event_list})

@app.route('/api/delete-event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = ReminderOrEvent.query.get(event_id)
    if event:
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': f'Event with ID {event_id} deleted successfully.'})
    else:
        return jsonify({'error': 'Event not found'}), 404

@app.route('/api/update-event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.json
    event = ReminderOrEvent.query.get(event_id)
    if event:
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'start_time' in data:
            event.start_time = parser.parse(data['start_time'])
        if 'end_time' in data:
            event.end_time = parser.parse(data['end_time'])
        if 'is_reminder' in data:
            event.is_reminder = data['is_reminder']
        db.session.commit()
        return jsonify({'message': f'Event with ID {event_id} updated successfully.'})
    else:
        return jsonify({'error': 'Event not found'}), 404

# Utility functions
def parse_date_time(text):
    cal = parsedatetime.Calendar()
    time_struct, _ = cal.parse(text)
    return datetime(*time_struct[:6]) if time_struct else None

def extract_event_id(text):
    # Placeholder for extracting event ID from user message
    # Assume the ID follows 'ID:' or 'event ID:'
    import re
    match = re.search(r'\bID\s*[:-]\s*(\d+)\b', text, re.IGNORECASE)
    return int(match.group(1)) if match else None

def extract_new_title(text):
    # Placeholder for extracting new title from user message
    # This is a simple example; you might need more sophisticated parsing
    import re
    match = re.search(r'update\s*title\s*[:-]\s*(.*)', text, re.IGNORECASE)
    return match.group(1).strip() if match else None

if __name__ == '__main__':
    app.run(debug=True)
