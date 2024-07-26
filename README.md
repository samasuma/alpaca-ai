# Alpaca AI

## Overview

Alpaca AI is a web application that provides a voice and text-based interface for interacting with an AI-powered system. It features speech-to-text conversion, question processing with OpenAI's GPT-3.5-turbo, and text-to-speech functionality.

## Workflow

### 1. **User Interaction**

- **Start Recording:**
  - Users initiate audio recording by clicking on the microphone icon.
  - The app accesses the user's microphone and begins recording audio.

### 2. **Audio Recording**

- **Record Audio:**
  - The `MediaRecorder` API captures audio from the user's microphone.
  - Audio data chunks are collected and combined into a single `Blob`.

- **Stop Recording:**
  - The recording stops automatically after 5 seconds or manually when the user stops it.

### 3. **Send Audio to Backend**

- **Send Audio Data:**
  - The audio `Blob` is sent to the Flask backend as a form data payload.

### 4. **Speech-to-Text Conversion**

- **Process Audio:**
  - The backend saves the audio file as a temporary WAV file and converts it to the required format (16 kHz, 16-bit, mono).

- **Perform Speech Recognition:**
  - The Azure Cognitive Services Speech SDK processes the audio file and converts speech to text.

- **Return Transcript:**
  - The recognized text (transcript) is returned to the frontend as a JSON response.

### 5. **Display Transcript**

- **Update Input Field:**
  - The transcript is placed into the input field of the form.

- **Submit Question:**
  - Automatically send the transcript as a question to the OpenAI GPT-3.5-turbo API.

### 6. **Ask Question**

- **Send Question:**
  - The question is sent to OpenAI's GPT-3.5-turbo for processing.

- **Receive Answer:**
  - The AI's response is returned to the frontend.

### 7. **Display AI Answer**

- **Update UI:**
  - The AI's answer is displayed on the page and saved for text-to-speech conversion.

### 8. **Text-to-Speech (TTS)**

- **Convert Text to Speech:**
  - The AI's response is sent to the text-to-speech endpoint.
  - The backend generates an audio file from the text and returns it to the client.

- **Play Audio:**
  - The audio file is played automatically on the client side using the HTML5 Audio API.

## Optimization Suggestions

### 1. **Optimize Audio Processing**

- **In-Memory Operations:**
  - Use in-memory file operations with `io.BytesIO` to reduce disk I/O overhead.

- **Efficient File Management:**
  - Minimize the number of file writes and deletes to improve performance.

### 2. **Improve Backend Performance**

- **Asynchronous Processing:**
  - Offload long-running tasks (e.g., text-to-speech) to background workers using tools like Celery or RQ.
  - Provide endpoints for checking the status of these background tasks.

- **Production WSGI Server:**
  - Deploy the Flask application using a production WSGI server like Gunicorn or uWSGI to handle concurrent requests more efficiently.

### 3. **Optimize Network Performance**

- **Reduce Latency:**
  - Host backend services in regions closer to your user base to minimize network latency.

- **Implement Caching:**
  - Use a CDN to cache static assets and reduce load times for users.

### 4. **Improve Client-Side Performance**

- **Optimize MediaRecorder:**
  - Ensure the `MediaRecorder` is used efficiently to minimize resource consumption.

- **User Feedback:**
  - Implement visual indicators (e.g., loading spinners) to improve user experience during delays.

### 5. **Enhance Text-to-Speech Processing**

- **Streaming TTS:**
  - If available, use streaming TTS APIs to start generating audio while the request is still being processed.

- **Immediate Feedback:**
  - Provide visual or auditory feedback to users while the TTS conversion is in progress.

### 6. **Monitor and Profile**

- **Performance Monitoring:**
  - Utilize monitoring tools like New Relic or Datadog to track application performance and identify bottlenecks.

- **Profiling:**
  - Regularly profile the application to find and optimize slow code paths.

## Getting Started

1. **Setup Environment:**
   - Install required Python packages: `pip install -r requirements.txt`.
   - Set up environment variables for OpenAI API key and Azure Speech services.

2. **Run the Application:**
   - Start the Flask server: `python app.py`.

3. **Access the App:**
   - Open a web browser and navigate to `http://localhost:5000`.

