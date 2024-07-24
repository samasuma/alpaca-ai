# Alpaca Voice Assistant AI 

A text to speech reminder app 

# Example Workflow

1. User Action: User speaks a command like "Today I used my shampoo."
2. Speech-to-Text: Use Azure Speech Service to convert the spoken command into text.
3. NLU Processing: Send the text to an NLU API (e.g., Dialogflow, LUIS) to understand the intent ("used shampoo") and extract parameters (timestamp, event description).
4. Calendar Integration: Use the appropriate calendar API (e.g., Google Calendar API) to create an event with the extracted details.
Response: Optionally, send a confirmation response to the user through a messaging API or display a confirmation message in the application interface.