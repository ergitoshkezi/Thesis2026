import streamlit as st
from unstructured.chunking.title import chunk_by_title
from htmlTemplates import css, bot_template, user_template
from flask import Flask
import os
import sqlite3
from unstructured.partition.pdf import partition_pdf
import requests
import glob
from dotenv import load_dotenv
load_dotenv()
import numpy as np
import  faiss
import json
from collections.abc import Iterable
import gzip
import tiktoken
import Machine_A
tokenizer = tiktoken.get_encoding("cl100k_base")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add Poppler bin folder to PATH so pdf2image can find it
poppler_bin_path = r"C:\Users\z004rnva\ALT\Definitve_Project\AI_Chatbot\poppler-25.11.0\Library\bin"
os.environ["PATH"] += os.pathsep + poppler_bin_path



def save_uploaded_file(uploaded_file, save_path):
    """Saves the uploaded file to the specified directory.""" 
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())




# Initialize the Flask application
app = Flask(__name__)
UPLOAD_FOLDER = './Analysed_PDFs'  # Change this to your desired upload folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def get_available_dbs():

    db_files = glob.glob('*.db')  # Find all .db files in the current directory
    return [os.path.splitext(db_file)[0] for db_file in db_files]



def does_DB_exists(DB):

    # Use glob to find files with the partial name and .db extension
    db_files = glob.glob(f'*{DB}*.db')
    
    # Check if any matching files were found
    if db_files:
        st.write(f"Database file(s) found: {db_files}")
        return db_files[0]  # Return the first matching file
    else:
        st.error("No matching database files found.")
        return None


# Database setup
def init_db(DB):
    
    new_db_file = f'{DB}.db'
    # Create cursor and ensure table exists with the dynamic name
    conn = sqlite3.connect(F'{DB}.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pdf_analysis (
        id INTEGER PRIMARY KEY,
        filename TEXT UNIQUE,
        analysis TEXT,
        chunked_text TEXT,
        vectorstore BLOB
    )
    ''')

    conn.commit()  # Save the changes
    conn.close()   # Close the connection

    return new_db_file



# PDF analysis placeholder
def analyze_pdf(file_path):
    # Placeholder for actual PDF analysis logic
    return "Analysis results for " + file_path





def save_analysis_to_db(filename, analysis, text, faiss_index, DB):
    # Serialize FAISS index to bytes
    faiss_index_bytes = faiss.serialize_index(faiss_index)
    st.success(f"Serialized FAISS index type: {type(faiss_index_bytes)}, length: {len(faiss_index_bytes)}")
    
    # Compress and serialize the JSON text
    if isinstance(text, list):
        text_json = json.dumps(text)  # Convert list to JSON string
        compressed_text = gzip.compress(text_json.encode('utf-8'))  # Compress JSON string
        st.success(f"Compressed text type: {type(compressed_text)}, length: {len(compressed_text)}")

    # Connect to SQLite database
    conn = sqlite3.connect(f'{DB}.db')
    cursor = conn.cursor()

    # Ensure the table exists with necessary columns
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS pdf_analysis (
            filename TEXT PRIMARY KEY,
            analysis TEXT,
            chunked_text BLOB,
            vectorstore BLOB
        )
    ''')
    
    # Insert or replace the data into the database
    cursor.execute('''
        INSERT OR REPLACE INTO pdf_analysis (filename, analysis, chunked_text, vectorstore)
        VALUES (?, ?, ?, ?)
    ''', (filename, analysis, compressed_text, sqlite3.Binary(faiss_index_bytes)))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    st.success(f"Data successfully saved for file: {filename}")





# Load FAISS index from the database
def load_analysis_from_db(filename, DB):
    conn = sqlite3.connect(f'{DB}.db')
    cursor = conn.cursor()

    # Query the database to get the analysis and serialized FAISS index
    cursor.execute('''
        SELECT vectorstore FROM pdf_analysis WHERE filename = ?
    ''', (filename,))

    row = cursor.fetchone()
    conn.close()

    # If the record exists, deserialize the FAISS index
    if row:
        faiss_index_bytes = row[0]  # Fetching the BLOB from the row

        # Ensure the data is in bytes format (could be memoryview, so convert to bytes)
        if isinstance(faiss_index_bytes, memoryview):
            faiss_index_bytes = faiss_index_bytes.tobytes()

        # Deserialize the FAISS index from bytes
        try:
            faiss_index = faiss.deserialize_index(faiss_index_bytes)
            st.success(f"Deserialized FAISS index type: {type(faiss_index)}")
            return faiss_index
        except Exception as e:
            st.error(f"Error during deserialization: {str(e)}")
            return None
    else:
        st.error("No record found for the specified filename.")
        return None




def Load_selected_analysis_from_db(sel, DB):
    if isinstance(sel, str):
        search_terms = [sel]
    elif isinstance(sel, list):
        search_terms = sel
    else:
        raise ValueError("sel must be a string or a list of strings")

    # Build the SQL query dynamically based on the search terms
    placeholders = ['filename LIKE ?' for _ in search_terms]
    query_conditions = ' OR '.join(placeholders)

    query = f'''
    SELECT filename, chunked_text, vectorstore 
    FROM pdf_analysis 
    WHERE {query_conditions}
    '''

    params = [f'%{term}%' for term in search_terms]

    # Connect to the SQLite database
    conn = sqlite3.connect(f'{DB}.db')
    cursor = conn.cursor()

    try:
        # Execute the query and fetch results
        cursor.execute(query, params)
        result = cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Error executing database query: {str(e)}")
        conn.close()
        return None
    finally:
        conn.close()

    # Check if results are found
    if not result:
        st.error("No vectorstore found for the specified filename(s).")
        return None

    # Initialize lists to store FAISS indexes and retrieved text chunks
    retrieved_text_chunks = []
    faiss_indexes = []

    # Iterate through each result row
    for row in result:
        # Extract the BLOB (serialized FAISS index) and the chunked text
        filename = row[0]
        compressed_text = row[1]
        faiss_index_bytes = row[2]
        #st.success(faiss_index_text)

        # Show filename for user feedback
        st.success(f"Processing file: {filename}")

        # Ensure the BLOB is in bytes format (sometimes returned as memoryview)
        if isinstance(faiss_index_bytes, memoryview):
            faiss_index_bytes = faiss_index_bytes.tobytes()

        # Deserialize the FAISS index
        try:
            faiss_index_bytes_np = np.frombuffer(faiss_index_bytes, dtype=np.uint8)
            faiss_index = faiss.deserialize_index(faiss_index_bytes_np)
            faiss_indexes.append(faiss_index)
        except Exception as e:
            st.error(f"Error deserializing FAISS index for file '{filename}': {str(e)}")

        # Deserialize the FAISS text index (the chunked text)
        try:
            decompressed_text_json = gzip.decompress(compressed_text).decode('utf-8')
            retrieved_text_chunks = json.loads(decompressed_text_json)
        except Exception as e:
            st.error(f"Error deserializing FAISS text index for file '{filename}': {str(e)}")

    return faiss_indexes, retrieved_text_chunks






# Extract text from PDFs
def get_pdf_text0(filepath):
    # Partition the PDF, inferring table structure where possible
    elements = partition_pdf(filepath, strategy="hi_res", infer_table_structure=True)
    container=[]

    for i in elements:
        text = i.to_dict()
        container.append(text)
    return categorize(container)




# Extract text from PDFs
def get_pdf_text(filepath):
    # Partition the PDF, inferring table structure where possible
    elements = partition_pdf(filepath,
                              strategy="hi_res",
                                infer_table_structure=True)

    return elements


# Split text into chunks
def get_text_chunks(elements):
    chunks = chunk_by_title(
        elements, max_characters=3000, 
        new_after_n_chars=2000,
        multipage_sections=False)
    return chunks





def categorize(elements):
    chunks = []
    current_chunk = []
    
    for i in range(len(elements)):
        element = elements[i]

        # Check if the element is a table
        if element["type"] == "Table":
            table_text = convert_table_to_text(element["text"])  # Convert the table to a readable format
            current_chunk.append("Table Start:\n" + table_text + "\nTable End")

        else:
            current_chunk.append(element["text"])

        # Check for a transition to a new section
        if i < len(elements) - 1 and elements[i]["type"] != "Title" and elements[i + 1]["type"] == "Title":
            current_chunk.append("ERGI")
            chunks.append(" ".join(current_chunk).strip())
            current_chunk = []  # Reset for the next chunk

    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())

    # Write to a file for inspection
    with open("Output_Chunk.txt", "w") as file:
        for chunk in chunks:
            file.write(chunk + "\n\n")

    return chunks

def convert_table_to_text(table_element):
    # Split the table rows and format them into a string
    formatted_table = []
    for row in table_element.split("\n"):
        formatted_table.append(" | ".join(row.split("\t")))  # Replace tabs with pipes for readability
    return "\n".join(formatted_table)









class EmbeddingApiRunnable:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    
    # Rename the primary method to invoke_e
    def invoke_e(self, texts):
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "bge-m3",
            "input": texts  # Assuming the API accepts a list of texts
        }

        response = requests.post(self.api_url, headers=headers, json=payload)
        print(f"API response: {response.text}")

        if response.status_code != 200:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None

        try:
            response_json = response.json()
            if 'data' in response_json and len(response_json['data']) > 0:
                # Ensure each item['embedding'] is a list (and not a single float or anything else)
                embeddings = [item['embedding'] for item in response_json['data']]
                for embedding in embeddings:
                    if not isinstance(embedding, list):
                        st.error(f"Invalid embedding format: {embedding}")
                        return None
                return embeddings
            else:
                st.error("Unexpected response structure or 'data' key missing")
                return None
        except (KeyError, IndexError, ValueError) as e:
            st.error(f"Error extracting embeddings: {e}")
            return None

    # Wrapper invoke method calls invoke_e for compatibility
    def invoke(self, texts):
        return self.invoke_e(texts)

    def embed_documents(self, texts):
        """Embed a list of documents (texts) using the invoke_e method."""
        return self.invoke_e(texts)  # Use invoke_e to process the batch of texts

    # Add the __call__ method to make the object callable
    def __call__(self, texts):
        return self.invoke_e(texts)

    


    

# Create vector store from text chunks using the API
def get_vectorstore(text_chunks):
    
    
    api_key_e=Machine_A.decrypt_message(os.getenv('API_KEY'),Machine_A.load_private_key())


    #api_key_e = os.getenv('API_KEY')
    api_url_e = os.getenv('API_EMBEDDING')

    embedding_runnable = EmbeddingApiRunnable(api_url=api_url_e, api_key=api_key_e)
    
    texts = []
    #meta = []
    for chunk in text_chunks:
        texts.append(chunk.to_dict()['text'])
        #meta.append(chunk.metadata.to_dict())
    
    # Generate embeddings
    embeddings = embedding_runnable(texts)
    
    # Ensure embeddings were retrieved successfully
    if embeddings is None or len(embeddings) == 0:
        raise ValueError("Embedding API returned no embeddings.")
    
    embeddings = np.array(embeddings)
    d = embeddings.shape[1]  # Dimension of the embeddings
    
    #nlist = min(len(embeddings), 10)   # Number of centroids for clustering
    
    # Initialize and train FAISS index
    index = faiss.IndexFlatL2(d)
    #index = faiss.IndexIVFFlat(quantizer, d, nlist)
    #index = faiss.IndexIVFPQ(quantizer, d, nlist, 8, 8)
    #print("Index embedding shape:", embeddings.shape)
    
    if index.is_trained:  # Proceed if there are at least 2 embeddings
        index.train(embeddings)
        index.add(embeddings)
    else:
        index.add(embeddings)
        #raise ValueError("Insufficient embeddings for FAISS training; need at least 2.")
    
    # Store index, texts, and meta in session state

    return index,texts # Return index and metadata as tuple

    



   



# Function to count tokens in a text
def count_tokens(text):

    return len(text.split())





# Function to truncate chat history to fit within the token limit
def truncate_chat_history_(history):
    while sum(count_tokens(message['content']) for message in history) > 512:
        if len(history) > 0:
            history.pop(0)
        else:
            break
    return history






    

# LLMApiRunnable class definition
class LLMApiRunnable:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key

    def __call__(self, messages, temperature=0.1, max_tokens=1024):
        return self.invoke(messages, temperature=temperature, max_tokens=max_tokens)

    def invoke(self, messages, temperature=0.1, max_tokens=1024):
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        #print(messages)
        # Construct the payload according to the correct Siemens API structure
        payload = {
            "model": "mistral-7b-instruct",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": messages
                }
            ]
        }

        # Make the POST request to the API
        #print(f"Sending request to API with payload: {payload}")
        response = requests.post(self.api_url, headers=headers, json=payload)

        # Parse the API response
        response_json = response.json()
        print(f"Received response: {response_json}")

        # Extract the content from the response, assuming it is under 'choices'
        try:
            content = response_json['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            st.error(f"Error extracting content from response: {e}")
            content = "Error: Could not extract content from API response."
        
        return content





def count_tokens(text):
    """Counts the number of tokens in a given text."""
    return len(tokenizer.encode(text))  # Tokenizes and counts tokens





# The get_conversation_chain function
def get_conversation_chain_faiss(query, faiss_results):

    api_key = Machine_A.decrypt_message(os.getenv('API_KEY'),Machine_A.load_private_key())  # Make sure the API key is set in your environment
    api_url = os.getenv('API_URL')  # The API URL

    # Initialize the LLM API
    llm = LLMApiRunnable(api_url=api_url, api_key=api_key)

    # Format FAISS results as a prompt for the LLM API
    results_text = "\n".join(
        [f"Result {i + 1}: {result['text']} (distance: {result['distance']:.4f})" for i, result in enumerate(faiss_results)]
    )
    
    # Construct the prompt for the LLM
    prompt = (
        f"User question: {query}\n\n"
        f"Here are some related results:\n{results_text}\n\n"
        "Please summarize or reorder the results based on their relevance to the question."
    )

    # Send the structured prompt to the LLM API
    response = llm(prompt)
    
    # Store the response in session state for later retrieval or display
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    st.session_state.chat_history.append({
        'role': 'Siemens',
        'content': response
    })

    return response






def Embedd_user_question(user_question):
    # Check if the user question is empty, and set a default if so
    print(user_question)
    # API credentials
    
    print(os.getenv('API_KEY_Embedding'))
    api_key_e = Machine_A.decrypt_message(os.getenv('API_KEY_Embedding'),Machine_A.load_private_key())
    
    #os.getenv('API_KEY')
    api_url_e = os.getenv('API_EMBEDDING')
    print(api_key_e)
    print(api_url_e)
    
    # Initialize the embedding API call
    vectorstore_user = EmbeddingApiRunnable(api_url=api_url_e, api_key=api_key_e)
    
    # Retrieve embeddings
    try:
        embeddings = vectorstore_user.invoke([user_question])  # Embedding as list
    except Exception as e:
        st.error("Error during embedding retrieval:", e)
        return None
    
    # Check if embeddings were returned and convert to np.array if valid
    if embeddings and isinstance(embeddings, list) and len(embeddings) > 0:
        return np.array([embeddings[0]])  # Convert to 2D array (1, embedding_dim)
    
    st.error("No embeddings found for the given user question.")
    return None  # Return None if embedding not found or invalid response









def handle_userinput(user_question):
    if 'conversation' not in st.session_state or st.session_state.conversation is None:
        st.error("<= Please add new PDF files or retrieve an existing one from the DB")
        return

    # Ensure question length is within limit
    if len(user_question.split()) > 70:
        user_question = ' '.join(user_question.split()[:70])

    if 'chat_history' not in st.session_state or st.session_state.chat_history is None:
        st.session_state.chat_history = []

    st.session_state.chat_history.append({'role': 'user', 'content': user_question})

    # Calculate token count
    user_question_tokens = count_tokens(user_question)
    chat_history_tokens = sum(count_tokens(msg['content']) for msg in st.session_state.chat_history)
    total_tokens = user_question_tokens + chat_history_tokens

# Generate query embedding
    if total_tokens < 512:
        print("Ergi")
        query_embedding = Embedd_user_question(user_question)
        if query_embedding is not None:
            query_embedding = query_embedding.reshape(1, -1)



            # Retrieve FAISS index, texts, and meta from session state
            print("ERgi")
            if isinstance(st.session_state.conversation, Iterable):
                for i in st.session_state.conversation:
                    i.nprobe = 8

            else:
                    st.session_state.conversation.nprobe = 8
             # Number of nearest neighbor

            # Perform the FAISS search with the query embedding
            k = 5 
            
            try:
                # Store all responses with distances across all conversation indices
                all_responses = []

                # Loop through each index in the conversation
                for index in st.session_state.conversation:
                    distances, indices = index.search(query_embedding, k)
                    
                    # Collect each response with its distance
                    for i in range(k):
                        if indices[0][i] < len(st.session_state.text):  # Ensure the index is within bounds
                            response_text = st.session_state.text[indices[0][i]]
                            response_distance = distances[0][i]
                            all_responses.append({
                                'text': response_text,
                                'distance': response_distance
                            })

                # Sort all responses by distance in ascending order
                sorted_responses = sorted(all_responses, key=lambda x: x['distance'])

                # Select the top 3 responses with the lowest distances
                top_k_responses = sorted_responses[:k]

                response = get_conversation_chain_faiss(user_question, top_k_responses)
                #print("Final LLM-enhanced response:", response)
            except Exception as e:
                st.error(f"Error finding closest responses: {str(e)}")
                return


    else:
        # Truncate chat history if token limit is exceeded
        st.session_state.chat_history = truncate_chat_history_(st.session_state.chat_history)
        
        query_embedding = Embedd_user_question(user_question)
        if query_embedding is not None:
            query_embedding = query_embedding.reshape(1, -1)
            # Retrieve FAISS index, texts, and meta from session state
            
            if isinstance(st.session_state.conversation, Iterable):
                for i in st.session_state.conversation:
                    i.nprobe = 8

            else:
                    st.session_state.conversation.nprobe = 8
            # Number of nearest neighbor

            # Perform the FAISS search with the query embedding
            k = 5
            
            try:
                # Store all responses with distances across all conversation indices
                all_responses = []

                # Loop through each index in the conversation
                for index in st.session_state.conversation:
                    distances, indices = index.search(query_embedding, k)
                    
                    # Collect each response with its distance
                    for i in range(k):
                        if indices[0][i] < len(st.session_state.text):  # Ensure the index is within bounds
                            response_text = st.session_state.text[indices[0][i]]
                            response_distance = distances[0][i]
                            all_responses.append({
                                'text': response_text,
                                'distance': response_distance
                            })

                # Sort all responses by distance in ascending order
                sorted_responses = sorted(all_responses, key=lambda x: x['distance'])

                # Select the top 3 responses with the lowest distances
                top_k_responses = sorted_responses[:k]

                response = get_conversation_chain_faiss(user_question, top_k_responses)
                #print("Final LLM-enhanced response:", response)
            except Exception as e:
                st.error(f"Error finding closest responses: {str(e)}")
                return
            
    # Display the chat history to the user
    display_chat_history()










def vectorize(selection):
    return (selection.split(','))



    
# Function to display chat history
def display_chat_history():
    for entry in st.session_state.chat_history:
    
        if entry['role']== 'user':
            user_message = entry['content']
            st.write(user_template.replace("{{MSG}}", user_message), unsafe_allow_html=True)
        else :
            bot_message = entry['content']
            st.write(bot_template.replace("{{MSG}}", bot_message), unsafe_allow_html=True)


    

def check_if_present(DB_name,pdf):


    query_conditions = f"filename = '{pdf}'"
    conn = sqlite3.connect(f'{DB_name}.db')
    cursor = conn.cursor()
    cursor.execute(f'SELECT filename FROM pdf_analysis WHERE {query_conditions}')
    result = cursor.fetchall()
    conn.close()
    return bool(result)




# Main function
def main():
    
    DB_name=""

    Current_dir=os.getcwd()
        

       
# Set the page configuration with a robot emoji
    st.set_page_config(
        page_title="AI ChatBot",
        page_icon="🤖"
    )

    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("AI ChatBot 🤖")
    
    with st.form(key='my_form'):
        user_question = st.text_input("Ask a question about your documents:")
        submit_button = st.form_submit_button(label='Submit')


    if submit_button:
        handle_userinput(user_question)


    with st.sidebar:
        st.subheader("Select Database")
        
        # Get list of available databases
        available_dbs = get_available_dbs()

        # Display the databases in a dropdown
        if available_dbs:
            sel = st.selectbox("Select the Database you want to query:", available_dbs)
            
            
        else:
            st.write("No databases found in the directory.")
            sel = None

        DB_name=sel

        if st.button("Choose"):
            if sel:
                with st.spinner("Processing"):
                      # Initialize selected DB
                    if DB_name:
                        st.success(f"DB = {sel}")
                        init_db(sel)
                    else:
                        st.write(f"DB not found, {sel} created")
    

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and click on 'Process'", accept_multiple_files=True)


        if st.button("Process"):
            

            with st.spinner("Processing"): 
                
                if len(pdf_docs) != 0:

                    for pdf in pdf_docs:

                        file_path = os.path.join(UPLOAD_FOLDER, pdf.name)
                        
                        save_uploaded_file(pdf, file_path)

                        if check_if_present(DB_name,pdf.name):
                            
                            st.error(f"File {pdf.name} already present in the DB ")
                            
                            continue

                        
                        pdf_text = get_pdf_text(file_path)
                        text_chunks = get_text_chunks(pdf_text)
                        
                        index,text= get_vectorstore(text_chunks)
                        st.session_state.conversation=index
                        st.session_state.text=text
                        #st.session_state.conversation = (index)  # Store index and metadata tuple
                        
                        analysis = analyze_pdf(file_path)
                        save_analysis_to_db(pdf.name, analysis, text, index, DB_name)
                        st.write(f"Performed new analysis for {pdf.name} and saved to database.")
                        
                else:
                    
                    st.write(f"Use the Select Manual Menus Or Add PDfs in Order to Perform New Analysis.")
                    #st.session_state.conversation = Load_selected_analysis_from_db(DB_name)

        # Form for querying existing analysis, placed under the Process button
    
    with st.sidebar:

        st.subheader("Select Manuals")
        sel = st.text_input("Select the documents you want to query:")

        if st.button("Select"):
            with st.spinner("Processing"): 
                analysis_i,analysis_t = Load_selected_analysis_from_db(vectorize(sel),DB_name)
                if analysis_i:
                    
                    st.session_state.conversation = list(analysis_i)
                    st.session_state.text=list(analysis_t)
                    st.write("Retrieved analysis from database.")
                else:
                    st.write("No analysis found for the selected documents.")




if __name__ == '__main__':
    main()