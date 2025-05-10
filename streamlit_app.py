import streamlit as st
import requests

# Set the title of the app
st.title("AI Assistant Chat Bot")


# Initialize session state for conversation history
if 'history' not in st.session_state:
    st.session_state.history = []

# Create a text input for user queries
user_input = st.text_input("You: ", "")
# Create a text input for user queries


# Function to call the Flask API
def call_flask_api(query):
    try:
        response = requests.post("http://localhost:8000/query", json={"query": query})
        return response.json().get("answer", "No response from server.")
    except Exception as e:
        return f"Error: {str(e)}"

# When the user submits a query
if st.button("Send"):
    if user_input:
        # Call the Flask API with the user input
        api_response = call_flask_api(user_input)
        
        # Store the conversation in session state
        st.session_state.history.append({"user": user_input, "bot": api_response})
        
        # Clear the input box
        st.rerun()
    else:
        st.warning("Please enter a message.")


# Display conversation history
if st.session_state.history:
    for chat in st.session_state.history:
        # Display bot response on the left
        st.text_area("Bot:", chat["bot"],  key=f"bot_{chat['bot']}", disabled=True)

        st.text_area("You:", chat["user"],  key=f"user_{chat['user']}", disabled=True)