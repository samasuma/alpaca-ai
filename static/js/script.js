document.addEventListener('DOMContentLoaded', function () {
  const startRecordButton = document.getElementById('startRecord');
  const transcriptionDiv = document.getElementById('transcription');
  const questionForm = document.getElementById('questionForm');
  const questionInput = document.getElementById('questionInput');
  const askButton = document.querySelector('#questionForm button[type="submit"]');
  const loginPopup = document.getElementById('loginPopup');
  const closePopupButton = document.getElementById('closePopup');
  const toggleFormButton = document.getElementById('toggleForm');
  const usernameDisplay = document.getElementById('usernameDisplay');
  const blurBackground = document.querySelector('.blur-background');
  const logoutButton = document.getElementById('logoutButton');
  const openLoginPopupLink = document.getElementById('openLoginPopup');
  const loginButton = document.getElementById('loginButton'); // Added for login/logout logic
  const recordingIndicator = document.querySelector('.recording-indicator');

  let mediaRecorder;
  let audioChunks = [];
  let recording = false;
  let lastAnswer = '';
  let currentAudio = null;

  // Function to update UI based on login status
  function updateUIBasedOnStatus(status) {
    if (status.logged_in) {
      usernameDisplay.textContent = `Logged in as ${status.email}`;
      loginButton.style.display = 'none';
      logoutButton.style.display = 'block';
      
  loginPopup.style.display = 'none';
  blurBackground.style.display = 'none';
    } else {
      usernameDisplay.textContent = '';
      loginButton.style.display = 'block';
      logoutButton.style.display = 'none';
        // Show login/register popup and background blur
  loginPopup.style.display = 'block';
  blurBackground.style.display = 'block';
    }
  }

  // Check login status on page load
  axios.get('/api/status')
    .then(function (response) {
      updateUIBasedOnStatus(response.data);
    })
    .catch(function (error) {
      console.error('Error checking status:', error);
    });



  // Close popup by clicking outside
  blurBackground.addEventListener('click', function () {
    loginPopup.style.display = 'none';
    blurBackground.style.display = 'none';
  });

  // Close popup button
  closePopupButton.addEventListener('click', function () {
    loginPopup.style.display = 'none';
    blurBackground.style.display = 'none';
  });

  // Event listener for login button
  loginButton.addEventListener('click', function () {
    loginPopup.style.display = 'block';
    blurBackground.style.display = 'block'; // Show background blur
  });

  // Toggle between login and register forms
  toggleFormButton.addEventListener('click', function () {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    if (loginForm.style.display === 'none') {
      loginForm.style.display = 'block';
      registerForm.style.display = 'none';
      toggleFormButton.textContent = 'Switch to Sign Up';
    } else {
      loginForm.style.display = 'none';
      registerForm.style.display = 'block';
      toggleFormButton.textContent = 'Switch to Login';
    }
  });

  // Handle login form submission
  document.getElementById('loginForm').addEventListener('submit', function (event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    axios.post('/api/login', { email, password })
      .then(function () {
        return axios.get('/api/status'); // Check status after login
      })
      .then(function (response) {
        updateUIBasedOnStatus(response.data);
        loginPopup.style.display = 'none';
        blurBackground.style.display = 'none';
      })
      .catch(function (error) {
        console.error('Login failed:', error);
      });
  });

  // Handle registration form submission
  document.getElementById('registerForm').addEventListener('submit', function (event) {
    event.preventDefault();
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    axios.post('/api/register', { email, password })
      .then(function () {
        document.getElementById('loginForm').style.display = 'block';
        document.getElementById('registerForm').style.display = 'none';
        toggleFormButton.textContent = 'Register';
      })
      .catch(function (error) {
        console.error('Registration failed:', error);
      });
  });

  // Handle start record button click
  startRecordButton.addEventListener('click', function () {
    if (!recording) {
      stopCurrentAudio();
      startRecording();
    }
  });

  // Handle ask button click
  askButton.addEventListener('click', function (event) {
    event.preventDefault();
    if (questionInput.value.trim() !== '') {
      stopCurrentAudio();
      askQuestion(questionInput.value.trim());
    } else {
      console.warn('Question input is empty.');
    }
  });

  // Handle logout button click
  logoutButton.addEventListener('click', function () {
    axios.post('/api/logout')
      .then(function () {
        return axios.get('/api/status'); // Check status after logout
      })
      .then(function (response) {
        updateUIBasedOnStatus(response.data);
        loginPopup.style.display = 'block';
        blurBackground.style.display = 'block';
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

        recordingIndicator.style.display = 'flex'; // Show the recording indicator

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

            recordingIndicator.style.display = 'none'; // Hide the recording indicator
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

  // Open login or registration popup based on link click
  openLoginPopupLink.addEventListener('click', function (event) {
    event.preventDefault();
    loginPopup.style.display = 'block';
    blurBackground.style.display = 'block';
  });
});
