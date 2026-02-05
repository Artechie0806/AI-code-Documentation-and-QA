# src/ui.py
import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"

st.title("🤖 AI Code Documentation")

with st.sidebar:
    st.header("Settings")
    repo_path = st.text_input("Repository Path", value="D:/academics/python/Pong game")
    
    if st.button("Ingest Codebase"):
        # Create a container for the logs
        status_box = st.status("Processing Codebase...", expanded=True)
        
        try:
            # stream=True is critical here
            response = requests.post(
                f"{API_URL}/ingest", 
                json={"path": repo_path}, 
                stream=True
            )
            
            if response.status_code == 200:
                # Iterate over the lines as they arrive
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        
                        # Update the UI based on the message
                        if data['status'] == 'error':
                            status_box.update(label="❌ Error", state="error", expanded=True)
                            st.error(data['message'])
                            break
                            
                        elif data['status'] == 'complete':
                            status_box.update(label="✅ Complete!", state="complete", expanded=False)
                            st.success(data['message'])
            else:
                st.error(f"Server Error: {response.status_code}")
                
        except Exception as e:
            st.error(f"Connection Error: {e}")

# ... (Rest of your Chat Interface code remains the same)
st.header("Ask about your code")
query = st.text_input("Question:", placeholder="How does the paddle movement work?")

if query:
    with st.spinner("Searching docs..."):
        response = requests.post(f"{API_URL}/search", json={"query": query})
        data = response.json()
        
        results = data.get("results", [])
        
        if not results:
            st.warning("No relevant documentation found.")
        else:
            for item in results:
                with st.expander(f"📄 {item['file']} - {item['summary']}"):
                    st.code(item['content'], language='python')