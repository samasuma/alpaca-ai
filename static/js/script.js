document.addEventListener('DOMContentLoaded', function () {
    const startRecordButton = document.getElementById('startRecord');
    const transcriptionDiv = document.getElementById('transcription');
    const questionForm = document.getElementById('questionForm');
    const questionInput = document.getElementById('questionInput');
    const micIcon = document.getElementById('micIcon');
  
    // Event listener for startRecordButton click
    startRecordButton.addEventListener('click', function () {
      if (startRecordButton.textContent === 'Start Recording') {
        startRecordButton.textContent = 'Stop Recording';
        startRecording();
      } else {
        startRecordButton.textContent = 'Start Recording';
        stopRecording();
      }
    });
  
    // Function to start recording audio
    function startRecording() {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function (stream) {
          const mediaRecorder = new MediaRecorder(stream);
          let audioChunks = [];
  
          // Add animation class to mic icon
          micIcon.classList.add('recording-indicator');
  
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
                transcriptionDiv.textContent = response.data.transcript;
              })
              .catch(function (error) {
                console.error('Error converting speech to text:', error);
                transcriptionDiv.textContent = 'Error converting speech to text';
              });
  
            // Remove animation class from mic icon
            micIcon.classList.remove('recording-indicator');
          });
  
          mediaRecorder.start();
          setTimeout(() => {
            mediaRecorder.stop();
          }, 5000); // Adjust recording duration as needed
        })
        .catch(function (error) {
          console.error('Error accessing microphone:', error);
          transcriptionDiv.textContent = 'Error accessing microphone';
        });
    }
  
    // Function to stop recording audio
    function stopRecording() {
      // Logic to stop recording (handled by mediaRecorder.stop() in startRecording function)
    }
  
    // Event listener for form submission
    questionForm.addEventListener('submit', function (event) {
      event.preventDefault();
      const question = questionInput.value.trim();
      if (question !== '') {
        // Handle form submission for text input (if needed)
        // Example: Send question to backend and display response
      }
    });
  
  });
  