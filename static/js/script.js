document.addEventListener('DOMContentLoaded', function () {
  const startRecordButton = document.getElementById('startRecord');
  const transcriptionDiv = document.getElementById('transcription');
  const questionForm = document.getElementById('questionForm');
  const questionInput = document.getElementById('questionInput');
  const micIcon = document.getElementById('micIcon');
  const askButton = document.querySelector('button[type="submit"]'); // Reference to the "ASK" button
  let mediaRecorder;
  let audioChunks = [];
  let recording = false;
  let lastAnswer = ''; // Variable to store the last answer

  // Event listener for startRecordButton click
  startRecordButton.addEventListener('click', function () {
    if (!recording) {
      startRecording();
    }
  });

  // Event listener for askButton click
  askButton.addEventListener('click', function (event) {
    event.preventDefault(); // Prevent form submission
    if (questionInput.value.trim() !== '') {
      askQuestion(questionInput.value.trim());
    }
  });

  // Function to start recording audio
  function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function (stream) {
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        // Add animation class to mic icon and change color
        micIcon.classList.add('recording-indicator');
        micIcon.style.color = 'red';

        mediaRecorder.addEventListener('dataavailable', function (event) {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        });

        mediaRecorder.addEventListener('stop', function () {
          const audioBlob = new Blob(audioChunks);
          const formData = new FormData();
          formData.append('audio_data', audioBlob, 'audio.wav');

          // Send audio data to backend for speech-to-text
          axios.post('/api/speech-to-text', formData)
            .then(function (response) {
              questionInput.value = response.data.transcript;
              questionInput.placeholder = ''; 
              // Automatically send the question to the AI after transcription
              askQuestion(response.data.transcript);
            })
            .catch(function (error) {
              console.error('Error converting speech to text:', error);
              transcriptionDiv.textContent = 'Error converting speech to text';
            });

          // Remove animation class from mic icon and reset color
          micIcon.classList.remove('recording-indicator');
          micIcon.style.color = '';
          recording = false;
        });

        mediaRecorder.start();

        // Automatically stop recording after 5 seconds or if no speech detected
        setTimeout(() => {
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
        }, 5000); // Adjust recording duration as needed

      })
      .catch(function (error) {
        console.error('Error accessing microphone:', error);
        transcriptionDiv.textContent = 'Error accessing microphone';
      });

    recording = true;
  }

  // Function to send question and handle AI response
  function askQuestion(question) {
    axios.post('/api/ask-question', { question: question })
      .then(function (response) {
        const answer = response.data.answer;
        transcriptionDiv.innerHTML = `<br><strong>AI:</strong> ${answer}`;
        lastAnswer = answer; // Store the answer for text-to-speech
        // Automatically convert the answer to speech
        convertTextToSpeech(answer);
      })
      .catch(function (error) {
        console.error('Error asking question:', error);
        transcriptionDiv.textContent = 'Error asking question';
      });
  }

  // Function to convert text to speech
  function convertTextToSpeech(text) {
    axios.post('/api/text-to-speech', { text: text }, { responseType: 'blob' })
      .then(function (response) {
        const audioUrl = URL.createObjectURL(response.data);
        const audio = new Audio(audioUrl);
        audio.play();
      })
      .catch(function (error) {
        console.error('Error converting text to speech:', error);
        transcriptionDiv.textContent = 'Error converting text to speech';
      });
  }
});
