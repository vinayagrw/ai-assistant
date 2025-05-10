import streamlit as st
import requests


st.title("AI Assistant Chat Bot")

# Function to call the Flask API
def call_flask_api(query):
    try:
        response = requests.post("http://localhost:8000/query", json={"query": query})
        return response.json().get("answer", "No response from server.")
    except Exception as e:
        return f"Error: {str(e)}"

# Initialize session state for conversation history
if 'history' not in st.session_state:
    st.session_state.history = []

with st.chat_message("user"):
    st.write("Hello 👋")

# Display chat messages from history on app rerun
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Accept user input
if prompt := st.chat_input("What is up?"):

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        stream = call_flask_api(prompt)
        st.markdown(stream) 
        st.session_state.history.append({"role": "assistant", "content": stream})   
                




# # When the user submits a query
# if st.button("Send"):
#     if user_input:
#         # Call the Flask API with the user input
#         api_response = call_flask_api(user_input)
        
#         # Store the conversation in session state
#         st.session_state.history.append({"user": user_input, "bot": api_response})
        
#         # Clear the input box
#         st.rerun()
#     else:
#         st.warning("Please enter a message.")

# # Display chat messages from history on app rerun
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])   

# # Display conversation history
# if st.session_state.history:
#     for chat in st.session_state.history:
#         # Display bot response on the left
#         st.text_area("Bot:", chat["bot"],  key=f"bot_{chat['bot']}", disabled=True)

#         st.text_area("You:", chat["user"],  key=f"user_{chat['user']}", disabled=True)

     