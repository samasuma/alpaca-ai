# Agenda for Tomorrow

## 1. Allow Guest Users to Use the App Without Registering

### Objective
Enable guest users to use the app without registering, but limit their interactions to a few prompts.

### Steps
- **Identify Guest Sessions**: Use session management to distinguish between guest users and registered users.
- **Handle Guest Prompts**: Allow guest users to interact with the app for a limited number of prompts (e.g., 3).
- **Show Call to Action**:
  - After the third prompt, display a call to action at the bottom of the transcription div.
  - Consider alternatives like showing a registration/signup popup or an alert with a call to action message.

## 2. Implement UI for Guest Users

### Objective
Update the frontend to handle guest user interactions and display appropriate prompts.

### Steps
- **Modify Transcription Div**: Add logic to insert a call to action after a certain number of prompts.
- **Create Call to Action Message**:
  - Design a `<p>` element or a modal to encourage registration after reaching the interaction limit.
  - Implement an alert that pops up after the interaction limit is reached.

## 3. Handle UI Alerts for Authentication and Registration Errors

### Objective
Use UIkit JavaScript alerts to inform users when they cannot authenticate or if their email is already registered.

### Steps
- **Integrate UIkit Alerts**: Use UIkit's JavaScript alert system to display error messages.
- **Update Backend**: Ensure that the backend sends appropriate error messages when authentication or registration fails.
- **Frontend Handling**:
  - Capture error messages from the backend and display them using UIkit alerts.

## 4. Manage Guest Data Without Persisting It

### Objective
Handle guest user data temporarily without persisting it in the database.

### Steps
- **Temporary Data Storage**: Use session storage to temporarily hold chat history for guest users.
- **Clear Data on Logout/Exit**: Ensure that guest data is cleared when the user leaves the session or logs out.

# Detailed Tasks

## Backend Modifications

1. **Identify and Handle Guest Sessions**:
   - Modify `/api/ask-question` to handle guest sessions.
   - Track the number of interactions for guest users in the session.

2. **Send Authentication and Registration Errors to Frontend**:
   - Update `/api/register` and `/api/login` endpoints to return specific error messages.
   - Ensure these messages are structured for easy parsing on the frontend.

## Frontend Modifications

1. **Transcription Div Updates**:
   - Add logic to count the number of prompts by guest users.
   - Insert a call to action message after the interaction limit is reached.

2. **UIkit Alerts**:
   - Capture error responses from the backend.
   - Use UIkit to display alerts for authentication and registration errors.

3. **Session Management for Guests**:
   - Use JavaScript to handle session storage for guest chat history.
   - Ensure data is cleared appropriately.

## Testing and Validation

- **Test Guest User Flow**:
  - Verify that guest users can interact with the app without registering.
  - Ensure that the call to action message appears after the set number of prompts.

- **Test Error Handling**:
  - Simulate authentication and registration errors to verify that UIkit alerts are displayed correctly.
