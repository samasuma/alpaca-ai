document.addEventListener('DOMContentLoaded', function () {
  const startRecordButton = document.getElementById('startRecord');
  const transcriptionDiv = document.getElementById('transcription');
  const questionForm = document.getElementById('questionForm');
  const questionInput = document.getElementById('questionInput');
  const micIcon = document.getElementById('micIcon');
 // Select the submit button within the questionForm
const askButton = document.querySelector('#questionForm button[type="submit"]');

  const loginPopup = document.getElementById('loginPopup');
  const closePopupButton = document.getElementById('closePopup');
  const toggleFormButton = document.getElementById('toggleForm');
  const usernameDisplay = document.getElementById('usernameDisplay');
  
  let mediaRecorder;
  let audioChunks = [];
  let recording = false;
  let lastAnswer = '';
  let currentAudio = null;

  // Login popup logic 

  // Event listener for login/register popup
  document.getElementById('loginPopup').style.display = 'block';

  closePopupButton.addEventListener('click', function () {
    loginPopup.style.display = 'none';
  });

  toggleFormButton.addEventListener('click', function () {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    if (loginForm.style.display === 'none') {
      loginForm.style.display = 'block';
      registerForm.style.display = 'none';
      toggleFormButton.textContent = 'Register';
    } else {
      loginForm.style.display = 'none';
      registerForm.style.display = 'block';
      toggleFormButton.textContent = 'Login';
    }
  });

  document.getElementById('loginForm').addEventListener('submit', function (event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    axios.post('/api/login', { email, password })
      .then(function (response) {
        loginPopup.style.display = 'none';
        usernameDisplay.textContent = `Logged in as ${email}`;
      })
      .catch(function (error) {
        console.error('Login failed:', error);
      });
  });

  document.getElementById('registerForm').addEventListener('submit', function (event) {
    event.preventDefault();
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    axios.post('/api/register', { email, password })
      .then(function (response) {
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('registerForm').style.display = 'none';
        toggleFormButton.textContent = 'Register';
      })
      .catch(function (error) {
        console.error('Registration failed:', error);
      });
  });

  // Event listener for startRecordButton click
  startRecordButton.addEventListener('click', function () {
    if (!recording) {
      stopCurrentAudio();
      startRecording();
    }
  });


  // Main app logic


  // Event listener for askButton click
  askButton.addEventListener('click', function (event) {
    event.preventDefault();
    if (questionInput.value.trim() !== '') {
      stopCurrentAudio();
      askQuestion(questionInput.value.trim());
    } else {
      console.warn('Question input is empty.');
    }
  });

      // Event listener for logoutButton click
      logoutButton.addEventListener('click', function () {
        axios.post('/api/logout')
          .then(function () {
            // Clear user info from UI
            usernameDisplay.textContent = '';
            // Optionally, show login popup
            loginPopup.style.display = 'block';
            console.log('Logged out successfully.');
          })
          .catch(function (error) {
            console.error('Logout failed:', error);
          });
      });


  // Function to start recording audio
  function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function (stream) {
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

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

          axios.post('/api/speech-to-text', formData)
            .then(function (response) {
              questionInput.value = response.data.transcript;
              questionInput.placeholder = '';
              askQuestion(response.data.transcript);
            })
            .catch(function (error) {
              console.error('Error converting speech to text:', error);
              transcriptionDiv.textContent = 'Error converting speech to text';
            });

          micIcon.classList.remove('recording-indicator');
          micIcon.style.color = '';
          recording = false;
        });

        mediaRecorder.start();

        setTimeout(() => {
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
        }, 5000);

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
        lastAnswer = answer;
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
        const newAudio = new Audio(audioUrl);

        stopCurrentAudio();

        newAudio.play();
        currentAudio = newAudio;

      })
      .catch(function (error) {
        console.error('Error converting text to speech:', error);
        transcriptionDiv.textContent = 'Error converting text to speech';
      });
  }

  // Function to stop the currently playing audio
  function stopCurrentAudio() {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      currentAudio = null;
    }
  }
});
