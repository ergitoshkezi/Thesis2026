import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import re
from datetime import datetime
import requests
import tkinter as tk
import os
import chardet
import threading
from tkinter import filedialog
from nltk.tokenize import word_tokenize
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from lxml import etree
from tkinter import messagebox
import xml.dom.minidom as minidom
import os
import asyncio
from datetime import datetime
import Structure_Excel
import pandas as pd
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QProgressDialog, QApplication
from collections import defaultdict, deque
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.widgets import Button
from matplotlib.backend_bases import MouseButton
import matplotlib
matplotlib.use('TkAgg')  # or 'Qt5Agg'
plt.rcParams['agg.path.chunksize'] = 100000 
from collections import deque
import openpyxl

######################################### API  class ###############
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

        response = requests.post(self.api_url, headers=headers, json=payload)
        response_json = response.json()

        try:
            content = response_json['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            content = "Error: Could not extract content from API response."
        return content

##################################################################################################### 

#### Golbal methods #########



def split_text_no_overlap(text, max_tokens=7500):
    words = word_tokenize(text)  # Tokenize text into words
    chunks = []
    # Start from the end and work backward
    for i in range(len(words), 0, -max_tokens):
        start = max(i - max_tokens, 0)  # Ensure start is not negative
        chunks.append(" ".join(words[start:i]))

    chunks.reverse()  # Reverse to maintain natural reading order
      # Print number of chunks
    return chunks

 # Convert back to text


def split_text_no_overlap_compare(text, max_tokens=7500):
    if isinstance(text, list):  
        text = ' '.join(text)

    words = word_tokenize(text)  # Tokenize text into words
    chunks = []

    # Iterate through words in chunks of max_tokens
    for i in range(0, len(words), max_tokens):
        chunks.append(" ".join(words[i:i + max_tokens]))
      # Print number of chunks
    return chunks

 # Convert back to text



######enhanced O(n+m)

def find_matching_sublists(file_, e, diff_rows):
    # Create a dictionary for the processed content of file_ only for specified indices
    file_dict = {i: " ".join(file_[i].split()[3:]) for i in diff_rows if 0 <= i < len(file_)}

    marked_e = []
    index_found = []

    # Process elements in e and compare to file_dict for a match
    for index, row in enumerate(e):
        e_content = " ".join(row.split()[3:])
        found = False

        # Check against the indices specified in diff_rows
        for i, f_content in file_dict.items():
            if e_content == f_content:
                marked_e.append(f"[FOUND] {file_[i]}")
                index_found.append(i)
                found = True
                break

        if not found:
            marked_e.append(f"[NOT FOUND] {row}")

    return marked_e, index_found


####################



def compareGPT(log, api_key):
    api_url = "https://api.siemens.com/llm/v1/chat/completions"
    llm = LLMApiRunnable(api_url=api_url, api_key=api_key)
    question = "Please Analyze the piece of Logs steps I provided in detail.\n\n"

    chunks=split_text_no_overlap_compare(log)
    l = len(chunks)
    Response=[]

        # Initialize QApplication if it doesn't exist
    if not QApplication.instance():
        app = QApplication(sys.argv)

    # Create QProgressDialog
    progress = QProgressDialog(
        "Processing log lines...",  # labelText
        "Cancel",                   # cancelButtonText
        0,                         # minimum
        100,                       # maximum
        None,                      # parent
        Qt.WindowType.WindowStaysOnTopHint
    )
    progress.setWindowTitle("Progress")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0) 
    progress.show()
    progress.setMaximum(l)
    QApplication.processEvents()
    for i,chunk in enumerate(chunks):

        prompt = (
            f" Hello, I am a Siemens support engineer, and I have provided you with the following additional rows generated by a transaction log in comparison to another: \n\n {chunk}"
            "The log entries follow a specific pattern, which I will explain in detail:\n\n"
            "If a row is marked as [FOUND], it means that this extra row of the file, compared to all the other different rows I have gathered during the comparison, is found somewhere in the other file. This could mean that this action is done in the other file but at a different stage. \n\n"
            "On the other hand, if you find [NOT FOUND], it means that this extra row, compared to the other different rows of the other file, is never found. This could indicate that this is a completely new action or a repetition that is done again.\n\n"
            "The structure of the log entries follows this pattern:\n\n"
            "- <timestamp>: The timestamp of the log entry, in the format \"YYYYMMDDHHMMSS.SSS\".\n"
            "- <threadId>: The ID of the thread that generated the log entry.\n"
            "- Depth: <depth>: The nesting depth of the CDO or CLF operation.\n"
            "- CDO: <CDOName>: The name of the Configurable Data Object (CDO) involved in the operation.\n"
            "- <Operation>: <OperationName>: The type of operation performed on the CDO, such as \"Perform\" or \"Field\".\n"
            "- Exec: <FunctionName>: The name of the function or method that was executed.\n"
            "- <Parameter1> = <Value1>: The input parameters and their values for the function or method.\n"
            "- <ParameterN>, resolved value = ( <ResolvedValue> ): The resolved value of the Nth parameter.\n"
            "- Leaving Depth: <depth>: Indicates the end of the nested operation.\n\n"
            "Below is important know-how about the system components and operations to help understand and analyze the log entries:\n\n"
            "1. **CDO (Configurable Data Objects)**:\n"
            "   - **Service CDO**: Acts as the main service or mediator, coordinating operations among various components in the system architecture.\n"
            "   - **Data CDO**: Manages the data aspects, dealing with data structures and fields essential for operations.\n\n"
            "2. **CLF (Custom Logic Functions)**:\n"
            "   - Comprises of custom procedures and functions forming the core logical framework of the software system. It processes data and implements business logic, interacting with both Service CDO and Data CDO.\n\n"
            "3. **Variables**:\n"
            "   - **Variable Expression**: Strings evaluated at runtime to produce values that replace identifiers in runtime operations. The format is `CDO.Field`.\n\n"
            "4. **Resolved Values**:\n"
            "   - These are concrete results obtained from evaluating Variable Expressions at runtime, crucial for proper system function during operations.\n\n"
            "5. **Unresolved Value**:\n"
            "   - Serves as a fallback when Variable Expressions cannot be accurately evaluated, appearing as an empty string or containing error-related details.\n\n"
            "6. Ignore 'deleting transaction', as it only means the transaction ends.\n\n"
            
            f"My request is: {question}\n\n"
        )
        Response.append(llm(prompt).strip())
                
        progress.setValue(i+1)
        QApplication.processEvents()  # Keep the GUI responsive
        

    return str((',').join(Response))








def tokenize(file1, file2,row,diff_rows):
    s_eq = []
    s_dots= []
    tokens1 = word_tokenize(file1)[3:]
    tokens2 = word_tokenize(file2)[3:]
    for num,i in enumerate(tokens2):
        if i == "=":
            s_eq.append(num)
        if i == ":":
            s_dots.append(num)

    tokens1 = [token for token in word_tokenize(file1)[3:] if token not in ('=', ':')]
    tokens2 = [token for token in word_tokenize(file2)[3:] if token not in ('=', ':')]
    c=0
    flag=False
    max_length = max(len(tokens1), len(tokens2))
    final_tokens = []
    

    for i in range(max_length):
        if i < len(tokens1) and i < len(tokens2):
            if tokens1[i] != tokens2[i]:
                c+=1
                if row not in diff_rows:
                    diff_rows.append(row)
                # Mark the differing token from tokens2
                marked_token = f'@@{tokens2[i]}@@'
                final_tokens.append(marked_token)
            else:
                final_tokens.append(tokens2[i])
        elif i < len(tokens2):
            # Extra tokens in tokens2
            marked_token = f'@@{tokens2[i]}@@'
            final_tokens.append(marked_token)
        elif i < len(tokens1):
            marked_token = f'@@{tokens1[i]}@@'
            ####attenzione implementare per file 1  i extra token della riga 

    if c == len(tokens1) or c == len(tokens2):
        flag=True # The row is completly different  ->True

    for item in s_eq:
        final_tokens.insert(item,"=")
    for item in s_dots:
        final_tokens.insert(item,":")
            
    result = ' '.join(final_tokens)
    return result,diff_rows,flag




def read_lines_list_for_all(filename, search_term):
    # Pre-compile patterns for better performance
    XML_PATTERN = re.compile(r'<\?xml')
    TIMESTAMP_PATTERN = re.compile(r'^\d{14}\.\d{3}')
    line_counter=0

    # Use chunks for large file reading
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks
    formatted_lines = []
    
    try:
        # Read file in binary mode with chunks
        with open(filename, 'rb') as infile:
            # Read first chunk for encoding detection
            first_chunk = infile.read(CHUNK_SIZE)
            encoding = chardet.detect(first_chunk)['encoding'] or 'utf-8'
            
            # Reset file pointer
            infile.seek(0)
            
            # Process file in chunks
            buffer = []
            chunk = infile.read(CHUNK_SIZE)
            while chunk:
                try:
                    decoded_chunk = chunk.decode(encoding)
                    buffer.append(decoded_chunk)
                except UnicodeDecodeError:
                    # Handle potential encoding errors
                    pass
                chunk = infile.read(CHUNK_SIZE)
            
            # Join chunks and split into lines
            content = ''.join(buffer)
            lines = content.splitlines()
            
            # Use state machine approach for better performance
            state = {
                'in_request_document': False,
                'in_transaction': False
            }
            
            # Process lines with optimized logic
            for  line in lines:  # Fixed the enumeration syntax
                line = line.strip()
                if not line:
                    continue
                    
                # State transitions
                if "Request Document" in line:
                    state['in_request_document'] = True
                    continue
                elif "starting transaction" in line:
                    state['in_transaction'] = True
                    state['in_request_document'] = False
                elif "Response Document" in line:
                    state['in_transaction'] = False
                    continue
                    
                # Process line based on current state
                if state['in_transaction']:
                    line_counter+=1

                    if TIMESTAMP_PATTERN.match(line):
                        # Optimize timestamp formatting
                        timestamp, message = line.split(maxsplit=1)
                        formatted_timestamp = (f"{timestamp[:4]}-{timestamp[4:6]}-"
                                            f"{timestamp[6:8]} {timestamp[8:10]}:"
                                            f"{timestamp[10:12]}:{timestamp[12:14]}."
                                            f"{timestamp[15:]}")
                        if search_term.lower() in line.lower():
                            formatted_lines.append(f"Line:  {line_counter}    {formatted_timestamp}  {message.strip()}")
                    else:
                        if search_term.lower() in line.lower():
                            formatted_lines.append(line)
                        
                elif not state['in_request_document'] and not state['in_transaction']:
                    if XML_PATTERN.search(line):
                        if search_term.lower() in line.lower():
                            formatted_lines.append(f"Line: {line_counter}    {line}")
                        
        return formatted_lines
        
    except Exception as e:
        messagebox.showerror("Error", f"Error processing file {filename}: {str(e)}")
        return []


####enhanced readlines for compare
def read_lines_list(filename):
    # Pre-compile patterns for better performance
    XML_PATTERN = re.compile(r'<\?xml')
    TIMESTAMP_PATTERN = re.compile(r'^\d{14}\.\d{3}')
    
    # Use chunks for large file reading
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks
    
    formatted_lines = []
    
    try:
        # Read file in binary mode with chunks
        with open(filename, 'rb') as infile:
            # Read first chunk for encoding detection
            first_chunk = infile.read(CHUNK_SIZE)
            encoding = chardet.detect(first_chunk)['encoding']
            
            # Reset file pointer
            infile.seek(0)
            
            # Process file in chunks
            buffer = []
            chunk = infile.read(CHUNK_SIZE)
            while chunk:
                try:
                    decoded_chunk = chunk.decode(encoding)
                    buffer.append(decoded_chunk)
                except UnicodeDecodeError:
                    # Handle potential encoding errors
                    pass
                chunk = infile.read(CHUNK_SIZE)
            
            # Join chunks and split into lines
            content = ''.join(buffer)
            lines = content.splitlines()
            
        # Use state machine approach for better performance
        state = {
            'in_request_document': False,
            'in_transaction': False
        }
        
        # Process lines with optimized logic
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # State transitions
            if "Request Document" in line:
                state['in_request_document'] = True
                continue
            elif "starting transaction" in line:
                state['in_transaction'] = True
                state['in_request_document'] = False
            elif "Response Document" in line:
                state['in_transaction'] = False
                continue
                
            # Process line based on current state
                    
            if state['in_transaction']:
                if TIMESTAMP_PATTERN.match(line):
                    # Optimize timestamp formatting
                    timestamp, message = line.split(maxsplit=1)
                    formatted_timestamp = (f"{timestamp[:4]}-{timestamp[4:6]}-"
                                        f"{timestamp[6:8]} {timestamp[8:10]}:"
                                        f"{timestamp[10:12]}:{timestamp[12:14]}."
                                        f"{timestamp[15:]}")
                    formatted_lines.append(f"{formatted_timestamp} {message.strip()}")
                else:
                    formatted_lines.append(line)
                    
            elif not state['in_request_document'] and not state['in_transaction']:
                if XML_PATTERN.search(line):
                    continue#Response_Document.append(line.split("\t")[-1])
                else:
                    continue#Response_Document.append(line)
                    
        return formatted_lines
        
    except Exception as e:
        messagebox.showinfo("Error", f"Error processing file: {str(e)}")
        return [], []








def read_lines_list_XML(filename):
    # Pre-compile patterns for better performance
    XML_PATTERN = re.compile(r'<\?xml')
    TIMESTAMP_PATTERN = re.compile(r'^\d{14}\.\d{3}')
    
    # Use chunks for large file reading
    CHUNK_SIZE = 1024 * 1024  # 1MB chunks
    
    #Request_Document = []
    Response_Document = []
    formatted_lines = []
    
    try:
        # Read file in binary mode with chunks
        with open(filename, 'rb') as infile:
            # Read first chunk for encoding detection
            first_chunk = infile.read(CHUNK_SIZE)
            encoding = chardet.detect(first_chunk)['encoding']
            
            # Reset file pointer
            infile.seek(0)
            
            # Process file in chunks
            buffer = []
            chunk = infile.read(CHUNK_SIZE)
            while chunk:
                try:
                    decoded_chunk = chunk.decode(encoding)
                    buffer.append(decoded_chunk)
                except UnicodeDecodeError:
                    # Handle potential encoding errors
                    pass
                chunk = infile.read(CHUNK_SIZE)
            
            # Join chunks and split into lines
            content = ''.join(buffer)
            lines = content.splitlines()
            
        # Use state machine approach for better performance
        state = {
            'in_request_document': False,
            'in_transaction': False
        }
        
        # Process lines with optimized logic
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # State transitions
            if "Request Document" in line:
                state['in_request_document'] = True
                continue
            elif "starting transaction" in line:
                state['in_transaction'] = True
                state['in_request_document'] = False
            elif "Response Document" in line:
                state['in_transaction'] = False
                continue
                
            # Process line based on current state
                    
            if state['in_transaction']:
                if TIMESTAMP_PATTERN.match(line):
                    # Optimize timestamp formatting
                    timestamp, message = line.split(maxsplit=1)
                    formatted_timestamp = (f"{timestamp[:4]}-{timestamp[4:6]}-"
                                        f"{timestamp[6:8]} {timestamp[8:10]}:"
                                        f"{timestamp[10:12]}:{timestamp[12:14]}."
                                        f"{timestamp[15:]}")
                    formatted_lines.append(f"{formatted_timestamp} {message.strip()}")
                else:
                    formatted_lines.append(line)
                    
            elif not state['in_request_document'] and not state['in_transaction']:
                if XML_PATTERN.search(line):
                    Response_Document.append(line.split("\t")[-1])
                else:
                    Response_Document.append(line)
                    
        return Response_Document, formatted_lines
        
    except Exception as e:
        messagebox.showinfo("Error", f"Error processing file: {str(e)}")
        return [], []






def Resume_GPT(log, api_key):
    api_url = "https://api.siemens.com/llm/v1/chat/completions"
    llm = LLMApiRunnable(api_url=api_url, api_key=api_key)
    question = "Please Order this Result analysis list of each chunk of Transaction Log." 

    prompt = (
        f"Hello, I am a Siemens support engineer, and I have provided you with the Analysis Results of each chunk of a Single Transaction Log : \n\n {log} \n\n"
        f"My request is: {question}\n\n"
    )
    
    return llm(prompt).strip()



def SiemensGPT(log, question, api_key):
    api_url = "https://api.siemens.com/llm/v1/chat/completions"
    llm = LLMApiRunnable(api_url=api_url, api_key=api_key)
    Response = []
    chunks=split_text_no_overlap(log)
    l=len(chunks)
        # Initialize QApplication if it doesn't exist
    if not QApplication.instance():
        app = QApplication(sys.argv)

    # Create QProgressDialog
    progress = QProgressDialog(
        "Processing log lines...",  # labelText
        "Cancel",                   # cancelButtonText
        0,                         # minimum
        100,                       # maximum
        None,                      # parent
        Qt.WindowType.WindowStaysOnTopHint
    )

    progress.setWindowTitle("Progress")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)  # Start at 0%
    progress.show()
    progress.setMaximum(l)
    QApplication.processEvents() 

    for i,chunk in enumerate(chunks):
        prompt = (
            f"Hello, I am a Siemens support engineer, and I have provided you with the following chunks of a transaction log data: \n{chunk}\n\n"
            "The structure of the log entries follows this pattern:\n"
            "<Number: > This is the Number Line of the Log's row. \n" 
            "<timestamp>: The timestamp of the log entry, in the format \"YYYYMMDDHHMMSS.SSS\".\n"
            "<threadId>: The ID of the thread that generated the log entry.\n"
            "Depth: <depth>: The nesting depth of the CDO or CLF operation.\n"
            "CDO: <CDOName>: The name of the Configurable Data Object (CDO) involved in the operation.\n"
            "<Operation>: <OperationName>: The type of operation performed on the CDO, such as \"Perform\" or \"Field\".\n"
            "Exec: <FunctionName>: The name of the function or method that was executed.\n"
            "<Parameter1> = <Value1>: The input parameters and their values for the function or method.\n"
            "<ParameterN>, resolved value = ( <ResolvedValue> ): The resolved value of the Nth parameter.\n"
            "Leaving Depth: <depth>: Indicates the end of the nested operation.\n\n"
            "Below is important know-how about the system components and operations to help understand and analyze the log entries:\n"
        
            "1. **CDO (Configurable Data Objects)**:\n"
            "- **Service CDO**: Acts as the main service or mediator, coordinating operations among various components in the system architecture.\n"
            "- **Data CDO**: Manages the data aspects, dealing with data structures and fields essential for operations.\n\n"
            
            "2. **CLF (Custom Logic Functions)**:\n"
            "- Comprises of custom procedures and functions forming the core logical framework of the software system. It processes data and implements business logic, interacting with both Service CDO and Data CDO.\n\n"
            
            "3. **Variables**:\n"
            "- **Variable Expression**: Strings evaluated at runtime to produce values that replace identifiers in runtime operations. The format is `CDO.Field`.\n\n"
            
            "4. **Resolved Values**:\n"
            "- These are concrete results obtained from evaluating Variable Expressions at runtime, crucial for proper system function during operations.\n\n"
        
            "5. **Unresolved Value**:\n"
            "- Serves as a fallback when Variable Expressions cannot be accurately evaluated, appearing as an empty string or containing error-related details.\n\n"

            f"My request is: {question}"
        )
        Response.append(llm(prompt).strip())
        progress.setValue(i+1)
        QApplication.processEvents()  # Keep the GUI responsive
           

    if l >= 3:     
       
        return Resume_GPT((',').join(Response),api_key)
    else:
        return (',').join(Response)


################################################################################################




########### Tree view class ############################

class LogTreeView(tk.Tk):
    def __init__(self, log_file, file):
        super().__init__()

        self.title(f"Log Viewer - {file}")
        
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        

        window_width = screen_width - 2 * 100
        window_height = screen_height - 2 * 100

 

        self.geometry(f"{window_width}x{window_height}+100+100")
        self.minsize(1600, 800)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main frame
        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')


        # Create PanedWindow
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=1, column=0, sticky='nsew')
        self.paned_window_button = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window_button.grid(row=0, column=0, sticky='nsew')




        # Tree and Log frames
        self.tree_frame = tk.Frame(self.paned_window)
        self.log_frame = tk.Frame(self.paned_window)
        self.buttons =tk.Frame(self.paned_window_button)

        # Tree and Log frames
        self.tree_frame = tk.Frame(self.main_frame)
        self.tree_frame.grid(row=1, column=0, sticky='nsew')

        self.log_frame = tk.Frame(self.main_frame)
        self.log_frame.grid(row=1, column=1, sticky='nsew')

        self.buttons = tk.Frame(self.main_frame)
        self.buttons.grid(row=0, column=0, sticky='nsew')

        # Add frames to PanedWindow
        #self.paned_window.add(self.buttons)
        self.paned_window.add(self.tree_frame, minsize=0)  # Set minsize to 0 to allow complete collapse
        self.paned_window.add(self.log_frame, minsize=0)  # Set a minimum size for log frame
        self.paned_window_button.add(self.buttons) 


        # Configure tree and log frames to expand
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)



        self.tree_frame.grid_propagate(1)
        self.log_frame.grid_propagate(1)
        self.buttons.grid_propagate(1)
        
        # Button frames
        self.tree_view_frame = tk.Frame(self.tree_frame)
        self.tree_view_frame.pack(fill=tk.X)
        
        self.Buttons_position= tk.Frame(self.buttons)
        self.Buttons_position.pack(fill=tk.X)

        self.log_view_frame = tk.Frame(self.log_frame)
        self.log_view_frame.pack(fill=tk.X)

        # Create tree view columns
        for i in range(1, 6):
            setattr(self, f'tree_col{i}', tk.Frame(self.Buttons_position))
            getattr(self, f'tree_col{i}').pack(side=tk.LEFT, expand=True)

        # Tree View Components (5 columns)
        # Column 1\
        self.open_button = tk.Menubutton(self.tree_col1, text="Open", 
                                       font=("Arial", 8), bg="#6A5ACD", fg="white",
                                       relief=tk.RAISED, width=8, height=1)
        self.open_menu = tk.Menu(self.open_button, tearoff=0)
        self.open_button.config(menu=self.open_menu)
        self.open_menu.add_command(label="Open File", command=lambda: self.open_file())
        self.open_menu.add_command(label="Open Excel", command=lambda: self.open_excel())
        self.open_menu.add_command(label="Search_In_All_Files", command=lambda: self.search_in_all_files())
        self.open_menu.add_command(label="Top 5", command=lambda: self.Top_5())
        self.open_button.pack(pady=2)

        # Column 2
        self.popup_button = tk.Button(self.tree_col2, text="SiemensGPT",
                                    font=("Italic", 8), bg="#00A5A8", fg="white",
                                    command=self.open_popup, width=10, height=1)
        self.popup_button.pack(pady=2)

        # Column 3
        self.expand_all_button = tk.Button(self.tree_col3, text="Expand All",
                                         font=("Arial", 8), bg="#808000", fg="white",
                                         command=self.expand_all_nodes, width=10, height=1)
        self.expand_all_button.pack(pady=2)

        # Column 4
        self.expand_button = tk.Button(self.tree_col4, text="Expand Nodes",
                                     font=("Arial", 8), bg="#4CAF50", fg="white",
                                     command=self.expand_nodes, width=11, height=1)
        self.expand_button.pack(pady=2)

        # Column 5
        self.close_all_button = tk.Button(self.tree_col5, text="Close Nodes",
                                        font=("Arial", 8), bg="#FF7F50", fg="white",
                                        command=self.close_nodes, width=10, height=1)
        self.close_all_button.pack(pady=2)

        # Create log view columns
        for i in range(1, 5):
            setattr(self, f'log_col{i}', tk.Frame(self.Buttons_position))
            getattr(self, f'log_col{i}').pack(side=tk.LEFT, expand=True)

        # Log View Components (4 columns)
        # Column 1 (Search Entry)
        self.Search_Count = tk.Label(self.log_col1, font=("Arial", 10), text="")
        self.search_entry = tk.Entry(self.log_col1, font=("Arial", 10), width=30)
        self.search_entry.pack(side=tk.LEFT, pady=2)
        self.Search_Count.pack(side=tk.LEFT, pady=2)

        # Column 2 (Search Buttons)

        self.search_button = tk.Button(self.log_col1, text="Search",
                                     font=("Arial", 8), bg="#FFC107", fg="black",
                                     command=self.search_log, width=6, height=1)
        self.next = tk.Button(self.log_col1, text="Next",
                            font=("Arial", 8), bg="#00A5A8", fg="black",
                            command=self.next_search_result, width=6, height=1)
        self.search_button.pack(side=tk.LEFT, pady=2)
        self.next.pack(side=tk.LEFT, pady=2)

        # Column 3 (Analysis Buttons)
        self.toggle_button = tk.Button(self.log_col2, text="XML Time Processing",
                                     font=("Arial", 8), bg="White", fg="Blue",
                                     command=self.Time_Analysis_main, width=25, height=1)
        self.compare_button = tk.Button(self.log_col3, text="Compare Files",
                                      font=("Arial", 8), bg="#FF8C00", fg="white",
                                      command=lambda: self.select_file_to_compare("Main"),
                                      width=12, height=1)
        self.toggle_button.pack(side=tk.LEFT, pady=2)
        self.compare_button.pack(side=tk.LEFT, pady=2)

        # Column 4 (Chart Button)
        self.chart_ = tk.Button(self.log_col4, text="Time Chart",
                              font=("Arial", 8), bg="#4169E1", fg="white",
                              command=lambda: self.chart(), width=10, height=1)
        self.chart_.pack(pady=2)





        self.expanded_levels = 0


        columns = ("message", "delta", "CDO DeltaTime")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="tree headings")
        self.tree.tag_configure("orange_text", foreground="orange")
        self.tree.tag_configure("green_text", foreground="green")
        self.tree.heading("message", text="Message")
        self.tree.heading("delta", text="Delta Time")
        self.tree.heading("CDO DeltaTime", text="CDO DeltaTime")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.tree_scrollbar.set)

        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD)
        self.log_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)

        self.sync_scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.sync_scroll_tree_log)
        self.sync_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.sync_scrollbar.set)
        self.log_text.configure(yscrollcommand=self.sync_scrollbar.set)

        self.exception_depths = []
        self.previous_timestamp = None
        self.depth_start_time = {}
        self.depth_delta_times = {}
        self.current_transaction = []
        self.log_file = log_file
        self.log_lines = []
        self.file = file
        self.highlighted_lines = []
        os.chdir(os.path.dirname(log_file))# tenngo conto della directory

        self.bind("<Control-f>", lambda event: self.search_entry.focus_set())
        self.bind("<Return>", lambda event: self.search_log())
        self.bind("<Escape>", lambda event: self.delete_search())
        self.bind("<Right>", lambda event: self.next_search_result())
        self.bind("<Left>", lambda event: self.prev_search_result())
        self.tree.bind("<Double-1>", self.highlight_log_line)
        self.bind_all('<Control-s>', lambda event: self.create_range_dialog())
                # Add scrolling functionality
        self.tree_view_frame.bind('<MouseWheel>', self.on_mousewheel_tree)
        self.log_view_frame.bind('<MouseWheel>', self.on_mousewheel_log)



        self.protocol("WM_DELETE_WINDOW", self.on_closing)


        if log_file.endswith((".txt", ".log", ".xml")):
            self.parse_log(log_file, file)
        else:
            messagebox.showerror(f"File {log_file} is not a .txt or .log file. Skipping...")

        if self.exception_depths:
            messagebox.showerror("Exception Depths:", self.exception_depths)




    def on_mousewheel_tree(self, event):
        self.tree.yview_scroll(int(-1*(event.delta/120)), "units")
        self.tree.bind('<MouseWheel>', self.on_mousewheel_tree)

    def on_mousewheel_log(self, event):
        self.log_text.yview_scroll(int(-1*(event.delta/120)), "units")
        self.log_text.bind('<MouseWheel>', self.on_mousewheel_log)

    def create_range_dialog(self):
        # Create a popup dialog
        dialog = tk.Toplevel(self)
        dialog.title("")
        
        # Remove window decorations and make it look like a search popup
        dialog.transient(self)
        dialog.resizable(False, False)
        
        # Calculate position (centered near the top of the main window)
        window_width = 400
        window_height = 40
        position_right = self.winfo_x() + (self.winfo_width() // 2) - (window_width // 2)
        position_down = self.winfo_y() + 50
        dialog.geometry(f"{window_width}x{window_height}+{position_right}+{position_down}")

        # Create a frame with raised border for search-like appearance
        frame = ttk.Frame(dialog, style='Search.TFrame')
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # From Label and Entry
        from_label = ttk.Label(frame, text="From:")
        from_label.pack(side=tk.LEFT, padx=2)
        
        # Validation command for numbers only
        vcmd = (self.register(lambda P: P == "" or P.isdigit()), '%P')
        
        # From entry
        from_entry = ttk.Entry(frame, width=10, validate='key', validatecommand=vcmd)
        from_entry.pack(side=tk.LEFT, padx=2)
        from_entry.focus_set()  # Set focus to first entry

        # To Label and Entry
        to_label = ttk.Label(frame, text="To:")
        to_label.pack(side=tk.LEFT, padx=2)

        
        
        # To entry
        to_entry = ttk.Entry(frame, width=10, validate='key', validatecommand=vcmd)
        to_entry.pack(side=tk.LEFT, padx=2)

  


        # Select button
        select_button = ttk.Button(frame, text="Select",
                                command=lambda: self.handle_range_selection(
                                    from_entry.get(), to_entry.get(), dialog))
        select_button.pack(side=tk.LEFT, padx=5)

        # Bind Enter key to select button
        dialog.bind('<Return>', lambda event: self.handle_range_selection(
            from_entry.get(), to_entry.get(), dialog))
        
        # Bind Escape key to close dialog
        dialog.bind('<Escape>', lambda event: dialog.destroy())
        
        # Bind Tab to move between entries
        from_entry.bind('<Tab>', lambda event: to_entry.focus_set())

        # Style configurations
        style = ttk.Style()
        style.configure('Search.TFrame', background='#f0f0f0')
        style.configure('TEntry', padding=3)

    def handle_range_selection(self, from_value, to_value, dialog):
        try:
            if from_value and to_value:
                from_num = int(from_value)
                to_num = int(to_value)
                selected_text=""
                if from_num <= to_num and from_num-1 >=0:
                    for i in range(from_num-1,to_num):
                        selected_text += self.log_lines[i] + "\n"

                        # Copy to clipboard
                    if selected_text:
                        self.clipboard_clear()
                        self.clipboard_append(selected_text)
                        messagebox.showinfo("Success",f"From: {from_num} To: {to_num} Text copied" )
                                # Add your logic here for what to do with the range
                    dialog.destroy()
                else:
                    messagebox.showwarning("warning","'From' value must be less than or equal to 'To' value")
            else:
                messagebox.showwarning("Warning","Please enter both values")
        except ValueError:
            messagebox.showwarning("Warning","Please enter valid numbers")



# Add this to your __init__ or wherever you set up your bindings


#-----------------------------------------------------------------------------

    def chart(self):

        def parse_time(t):
            try:
                dt = datetime.strptime(t, '%H:%M:%S.%f')
            except ValueError:
                dt = datetime.strptime(t, '%H:%M:%S')
            return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)

        # Prepare data
        deltas = [parse_time(t) for t in self.delta]

        cumulative = []
        total = timedelta()
        for delta in deltas:
            total += delta
            cumulative.append(total.total_seconds() * 1000)  # milliseconds

        derivative = [cumulative[i+1] - cumulative[i] for i in range(len(cumulative)-1)]
        x_vals = list(range(1, len(cumulative) + 1))
        dx_vals = list(range(2, len(cumulative) + 1))  # derivative is between points

        # Plot setup
        fig, ax = plt.subplots()
        fig.suptitle(self.file, fontsize=16, fontweight='bold')
        plt.subplots_adjust(bottom=0.2,top=0.85)
        line, = ax.plot(x_vals, cumulative, label="Cumulative Time (ms)", marker='o')
        ax.set_xlabel("Index")
        ax.set_ylabel("Time (ms)")
        ax.set_title("Cumulative Time Plot")
        ax.grid(True)

        # Tooltip annotation
        tooltip = None
        is_derivative = [False]  # use list to allow modification in nested scope

        # Button callback
        def on_click(event):
            if line.get_label() == "Cumulative Time (ms)":
                line.set_ydata(derivative)
                line.set_xdata(dx_vals)
                line.set_label("Derivative (ms/index)")
                ax.set_ylabel("Rate of Change (ms)")
                ax.set_title("Derivative of Cumulative Time")
                is_derivative[0] = True
            else:
                line.set_ydata(cumulative)
                line.set_xdata(x_vals)
                line.set_label("Cumulative Time (ms)")
                ax.set_ylabel("Time (ms)")
                ax.set_title("Cumulative Time Plot")
                is_derivative[0] = False
            ax.relim()
            ax.autoscale_view()
            ax.legend()
            plt.draw()

        # Add button
        ax_button = plt.axes([0.7, 0.05, 0.2, 0.075])
        button = Button(ax_button, 'Toggle Derivative', color='orange', hovercolor='darkorange')
        button.on_clicked(on_click)

        # Right-click handler
        def on_right_click(event):
            nonlocal tooltip

            if event.button != MouseButton.RIGHT or event.inaxes != ax:
                return

            x_data = dx_vals if is_derivative[0] else x_vals
            y_data = derivative if is_derivative[0] else cumulative

            if event.xdata is None or event.ydata is None:
                return

            # Find closest point
            distances = [(abs(event.xdata - x), abs(event.ydata - y)) for x, y in zip(x_data, y_data)]
            closest_index = min(range(len(distances)), key=lambda i: distances[i][0] + distances[i][1])
            actual_index = x_data[closest_index] - 1  # account for 1-based x_vals

            if actual_index < 0 or actual_index >= len(self.log_lines):
                return

            # Remove existing tooltip
            if tooltip:
                tooltip.remove()

            # Add new tooltip
            tooltip = ax.annotate(
                self.log_lines[actual_index],
                xy=(x_data[closest_index], y_data[closest_index]),
                xytext=(15, 15),
                textcoords='offset points',
                bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.9),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
            )
            self.highlight_log_line_by_index(actual_index)
            plt.draw()

        # Connect mouse event
        fig.canvas.mpl_connect('button_press_event', on_right_click)

        plt.show()




    def highlight_log_line_by_index(self, index):
        try:
            # Check if line number is valid
            if 0 <= index < len(self.log_lines):
                # Instead of reinserting all text, just add highlight tag
                start = f"{index + 1}.0"
                end = f"{index + 1}.end"
                self.log_text.tag_add("highlight", start, end)
                self.log_text.see(start)
            else:
                messagebox.showerror("Error", f"Invalid line number: {index}")
        except Exception as e:
            messagebox.showerror("Error", f"Error in highlighting: {e}")








#---------------------------------------------------------------------------------------------------------------------------------------

    def Show_All_Matches(self, path):
        try:
            # Create main window
            tree_window = tk.Toplevel(self)
            tree_window.title("Find")
            tree_window.geometry("1400x800")

            # Create main frame
            main_frame = ttk.Frame(tree_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Create search frame
            search_frame = ttk.Frame(main_frame)
            search_frame.pack(fill=tk.X, pady=(0, 10))

            search_label = ttk.Label(search_frame, text="Search Content:")
            search_label.pack(side=tk.LEFT, padx=(0, 5))

            search_entry = ttk.Entry(search_frame)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Create tree frame
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            # Create Treeview
            tree = ttk.Treeview(tree_frame)
            
            # Add scrollbars
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            # Layout management
            tree.grid(column=0, row=0, sticky='nsew')
            vsb.grid(column=1, row=0, sticky='ns')
            hsb.grid(column=0, row=1, sticky='ew')
            tree_frame.grid_columnconfigure(0, weight=1)
            tree_frame.grid_rowconfigure(0, weight=1)

            # Configure tree columns
            tree["columns"] = ("content",)
            tree.column("#0", width=200, stretch=tk.YES)
            tree.column("content", width=1000, stretch=tk.YES)
            tree.heading("#0", text="Filename")
            tree.heading("content", text="Found Rows")

            self.Directory_of_all_file_search=path

            def update_tree_content():
                """Update the treeview with search results"""
                try:
                    # Clear existing items
                    for item in tree.get_children():
                        tree.delete(item)

                    # Insert new items
                    for filename, matching_lines in self.lines_found.items():
                        parent = tree.insert("", "end", text=filename, values=("",))
                        
                        # Insert child nodes (matching lines)
                        for line in (matching_lines):
                            tree.insert(parent, "end", text=f"=", values=(f"{line}",))
                        
                        # Expand parent node
                        tree.item(parent, open=True)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            def on_double_click(event):
                """Handle double-click events on tree items"""
                try:
                    item = tree.identify('item', event.x, event.y)
                    if item and not tree.parent(item):  # If it's a parent node
                        if tree.item(item, 'open'):
                            tree.item(item, open=False)
                        else:
                            tree.item(item, open=True)
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            def local_start_search(search_term):
                """Local function to handle search and update tree"""
                self.start_search_all(path, search_term)
                update_tree_content()

            # Add search button with local search function
            search_button = ttk.Button(
                search_frame, 
                text="Search", 
                command=lambda: local_start_search(search_entry.get())
            )
            search_button.pack(side=tk.LEFT, padx=(5, 0))

            # Bind events
            search_entry.bind("<Return>", 
                            lambda event: local_start_search(search_entry.get()))
            tree.bind("<Control-f>", lambda event: search_entry.focus_set())
            tree.bind("<Double-1>", on_double_click)
            tree.bind("<Button-3>", lambda event:self.show_sql_popup_all_files(tree,event))

            # Update tree if results exist
            if hasattr(self, 'lines_found') and self.lines_found:
                update_tree_content()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_search_all(self, path, search_term):
        """Start the search process in all files"""
        try:
            self.lines_found = {}
            if not search_term:
                messagebox.showwarning("Warning", "Please enter a search term")
                return

            for file in os.listdir(path):
                if file.endswith((".txt", ".log")):
                    file_path = os.path.join(path, file)
                    self.lines_found[file] = read_lines_list_for_all(file_path, search_term)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def Top_5(self):
        self.top_5_window()

    def search_in_all_files(self):
        """Open folder selector and initiate search"""
        try:
            path = filedialog.askdirectory(title="Select Folder")
            if path:  # Proceed only if a directory was selected
                path = path.strip()
                self.Show_All_Matches(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def show_sql_popup_all_files(self, tree, event):  # Change coordinates to event
        # Get item at coordinates
        item = tree.identify_row(event.y)
        if item:
            # Get values from the item
            values = tree.item(item)['values']
            if values and len(values) > 0:
                    f = values[0]  # Get SQL text from third column
            if tree.item(item)['text']:
                l=tree.item(item)['text']



            # Create popup window
            popup = tk.Toplevel(self)
            popup.title("Text Values")
            popup.geometry("800x400")
            text_widget = tk.Text(popup, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbars
            vsb = ttk.Scrollbar(popup, orient="vertical", command=text_widget.yview)
            hsb = ttk.Scrollbar(popup, orient="horizontal", command=text_widget.xview)
            text_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            hsb.pack(side=tk.BOTTOM, fill=tk.X)
            if f:
                text_widget.insert(tk.END, f)
            elif l:
                #text_widget.insert(tk.END, l)
                popup.destroy()  # Close the current popup window
                log_tree_view=LogTreeView(f"{self.Directory_of_all_file_search}/{l}", l)
                log_tree_view.mainloop() 

            text_widget.config(state='disabled')  # Make it read-only


####________________________________________________________########################################



    def read_Excel(self, filename):
        try:
            # Read the Excel file
            self.df = pd.read_excel(filename)
            self.show_excel_data()
            return self.df
        except Exception as e:
            messagebox.showerror("Error", f"Error reading the file: {str(e)}")
            return None
    
    def show_excel_data(self):
        excel_window = tk.Toplevel(self)
        excel_window.title("Excel Data Viewer")
        excel_window.geometry("800x600")
        
        main_frame = ttk.Frame(excel_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(main_frame)
        y_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        x_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        
        data_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        
        canvas.create_window((0, 0), window=data_frame, anchor="nw")
        
        # Calculate maximum width for each column
        max_widths = {}
        for col_idx, column in enumerate(self.df.columns):
            # Get maximum width from column name and data
            column_values = self.df[column].astype(str)
            max_width = max(
                len(str(column)),  # Header length
                column_values.str.len().max()  # Maximum data length
            )
            # Set a minimum width of 10 and maximum of 50 characters
            max_widths[col_idx] = min(max(max_width, 10), 50)

        # Create header labels with calculated widths
        for col_idx, column in enumerate(self.df.columns):
            header_label = ttk.Label(data_frame, 
                                text=column, 
                                font=('Arial', 10, 'bold'),
                                background='#e0e0e0', 
                                relief='raised', 
                                padding=5,
                                width=max_widths[col_idx])  # Set width here
            header_label.grid(row=0, column=col_idx, sticky='nsew')
            
            # Configure column weight
            data_frame.grid_columnconfigure(col_idx, weight=1, minsize=max_widths[col_idx]*8)
        
        # Create Entry widgets for each cell with calculated widths
        for row_idx, row in enumerate(self.df.values):
            first_col_value = str(row[0])  # Get first column value
            for col_idx, value in enumerate(row):
                entry = tk.Entry(data_frame, 
                            readonlybackground='white', 
                            justify='left',
                            width=max_widths[col_idx])  # Set width here
                entry.insert(0, str(value))
                entry.configure(state='readonly', relief='flat')
                entry.grid(row=row_idx+1, column=col_idx, sticky='nsew', padx=1, pady=1)
                entry.bind('<Button-3>', 
            lambda event, first_val=first_col_value: 
            self.open_file_from_excel(Structure_Excel.path, first_val))
                
                def select_all(event):
                    event.widget.configure(state='normal')
                    event.widget.select_range(0, tk.END)
                    event.widget.configure(state='readonly')
                
                entry.bind('<Button-1>', select_all)

        # Update scroll region
        data_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        button_frame = ttk.Frame(excel_window)
        button_frame.pack(pady=10)
        
        # Add sorting buttons
        sort_frame = ttk.LabelFrame(button_frame, text="Sort by")
        sort_frame.pack(side=tk.LEFT, padx=10)

        # Duration of TXN sorting
        duration_sort_asc = ttk.Button(sort_frame, 
                                    text="Duration ↑", 
                                    command=lambda: [self.sort_dataframe("Duration of TXN", True), 
                                                    self.refresh_excel_data(data_frame)])
        duration_sort_asc.pack(side=tk.LEFT, padx=2)

        duration_sort_desc = ttk.Button(sort_frame, 
                                    text="Duration ↓", 
                                    command=lambda: [self.sort_dataframe("Duration of TXN", False), 
                                                    self.refresh_excel_data(data_frame)])
        duration_sort_desc.pack(side=tk.LEFT, padx=2)

        # Biggest Gap sorting
        gap_sort_asc = ttk.Button(sort_frame, 
                                text="Gap ↑", 
                                command=lambda: [self.sort_dataframe("Biggest Gap", True), 
                                            self.refresh_excel_data(data_frame)])
        gap_sort_asc.pack(side=tk.LEFT, padx=2)

        gap_sort_desc = ttk.Button(sort_frame, 
                                text="Gap ↓", 
                                command=lambda: [self.sort_dataframe("Biggest Gap", False), 
                                                self.refresh_excel_data(data_frame)])
        gap_sort_desc.pack(side=tk.LEFT, padx=2)

        # Combined sorting
        combined_sort_asc = ttk.Button(sort_frame, 
                                    text="Duration & Gap ↑", 
                                    command=lambda: [self.sort_dataframe(
                                        ["Duration of TXN", "Biggest Gap"], 
                                        [True, True]), 
                                        self.refresh_excel_data(data_frame)])
        combined_sort_asc.pack(side=tk.LEFT, padx=2)

        combined_sort_desc = ttk.Button(sort_frame, 
                                    text="Duration & Gap ↓", 
                                    command=lambda: [self.sort_dataframe(
                                        ["Duration of TXN", "Biggest Gap"], 
                                        [False, False]), 
                                        self.refresh_excel_data(data_frame)])
        combined_sort_desc.pack(side=tk.LEFT, padx=2)
        
        close_button = ttk.Button(button_frame, 
                                text="Close", 
                                command=excel_window.destroy)
        close_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = ttk.Button(button_frame, 
                                text="Refresh", 
                                command=lambda: self.refresh_excel_data(data_frame))
        refresh_button.pack(side=tk.LEFT, padx=5)

    def refresh_excel_data(self, frame):
        # Clear existing widgets
        for widget in frame.winfo_children():
            widget.destroy()
        
        # Calculate maximum width for each column
        max_widths = {}
        for col_idx, column in enumerate(self.df.columns):
            column_values = self.df[column].astype(str)
            max_width = max(
                len(str(column)),
                column_values.str.len().max()
            )
            max_widths[col_idx] = min(max(max_width, 10), 50)

        # Recreate headers with calculated widths
        for col_idx, column in enumerate(self.df.columns):
            header_label = ttk.Label(frame, 
                                text=column, 
                                font=('Arial', 10, 'bold'),
                                background='#e0e0e0', 
                                relief='raised', 
                                padding=5,
                                width=max_widths[col_idx])
            header_label.grid(row=0, column=col_idx, sticky='nsew')
            
            # Configure column weight
            frame.grid_columnconfigure(col_idx, weight=1, minsize=max_widths[col_idx]*8)
        
        # Recreate Entry widgets with calculated widths
        for row_idx, row in enumerate(self.df.values):
            first_col_value = str(row[0])  # Get first column value
            for col_idx, value in enumerate(row):
                entry = tk.Entry(frame, 
                            readonlybackground='white', 
                            justify='left',
                            width=max_widths[col_idx])
                entry.insert(0, str(value))
                entry.configure(state='readonly', relief='flat')
                entry.grid(row=row_idx+1, column=col_idx, sticky='nsew', padx=1, pady=1)
                entry.bind('<Button-3>', 
                        lambda event, first_val=first_col_value: 
                        self.open_file_from_excel(Structure_Excel.path, first_val))
                
                def select_all(event):
                    event.widget.configure(state='normal')
                    event.widget.select_range(0, tk.END)
                    event.widget.configure(state='readonly')
                
                entry.bind('<Button-1>', select_all)

    def sort_dataframe(self, columns, ascending=True):
        """
        Sort the dataframe by the specified column(s)
        columns can be a single column name or a list of column names
        ascending can be a single boolean or a list of booleans
        """
        try:
            # Convert duration and gap columns to numeric, removing any non-numeric characters
            if isinstance(columns, str):
                columns = [columns]
            
            # Create temporary columns for sorting
            for col in columns:
                if col in ["Duration of TXN", "Biggest Gap"]:
                    # Create a temporary column for sorting
                    temp_col = f"{col}_temp"
                    # Convert to string first to ensure .str accessor works
                    self.df[temp_col] = self.df[col].astype(str)
                    # Extract numeric values
                    self.df[temp_col] = pd.to_numeric(
                        self.df[temp_col].str.replace(r'[^\d.]', '', regex=True),
                        errors='coerce'
                    )
                    
            # Replace original columns in the sorting list with temporary columns
            sort_columns = [f"{col}_temp" if col in ["Duration of TXN", "Biggest Gap"] else col 
                        for col in columns]
            
            # Perform the sort
            self.df = self.df.sort_values(by=sort_columns, ascending=ascending)
            
            # Remove temporary columns
            for col in columns:
                if col in ["Duration of TXN", "Biggest Gap"]:
                    temp_col = f"{col}_temp"
                    if temp_col in self.df.columns:
                        self.df = self.df.drop(columns=[temp_col])
                        
        except Exception as e:
            messagebox.showerror("Sorting Error", f"Error while sorting: {str(e)}")

    ################################################################################ 


    def open_file_from_excel(self,path,name):

        log_tree_view=LogTreeView(path+'/'+name, name)
        log_tree_view.mainloop() 



    def open_file(self):
        
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            #new_log_tree_view = LogTreeView(file_path, file_name)  # Create a new instance for the new file
            log_tree_view=LogTreeView(file_path, file_name)
            log_tree_view.mainloop() 


    def call(self):
        try:
        # Run the main function from Structure_Excel.py
            Structure_Excel.main()
            self.read_Excel("_Overview.xlsx")
        except Exception as e:
            messagebox.showerror(f"Error occurred: {e}")


    
    def open_excel(self):
        #self.start_async_processing_()
        self.call()

    

##################################################################

        # Function to handle window closing
    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            root.quit()  # This ensures complete exit
        




    def sync_scroll_tree_log(self,*args):
        """Synchronize scrolling between two text widgets."""
        self.tree.yview(*args)
        self.log_text.yview(*args)


    def delete_search(self):
        self.log_text.tag_remove("search_highlight", "1.0", tk.END)
        self.log_text.tag_remove("highlight", "1.0", tk.END)
        self.Search_Count.config(text="")
        


    def search_log(self):
        self.total_search_found=0

        search_term = self.search_entry.get().lower()
        self.log_text.tag_remove("search_highlight", "1.0", tk.END)

        # Get current cursor position
        current_pos = self.log_text.index(tk.INSERT)
        current_line = int(current_pos.split('.')[0])

        self.search_results = []
        
        # First search from current position to end
        for line_number in range(current_line, len(self.log_lines) + 1):
            line = self.log_lines[line_number - 1]
            if search_term in line.lower():
                start_index = f"{line_number}.0"
                end_index = f"{line_number}.{len(line)}"
                self.search_results.append((start_index, end_index))
                self.log_text.tag_add("search_highlight", start_index, end_index)


        # If no results found after current position, search from beginning to current position
        if not self.search_results:
            for line_number in range(1, current_line):
                line = self.log_lines[line_number - 1]
                if search_term in line.lower():
                    start_index = f"{line_number}.0"
                    end_index = f"{line_number}.{len(line)}"
                    self.search_results.append((start_index, end_index))
                    self.log_text.tag_add("search_highlight", start_index, end_index)

        self.log_text.tag_config("search_highlight", background="light green")
        self.total_search_found=len(self.search_results)
        self.Search_Count.config(text=f"{self.total_search_found}")
        
        if self.search_results:
            
            self.current_result_index = 0
            # Get the first match position
            first_match = self.search_results[self.current_result_index][0]
            
            # Calculate the relative position for scrolling
            total_lines = float(self.log_text.index('end-1c').split('.')[0])
            current_line = float(first_match.split('.')[0])
            relative_position = current_line / total_lines
            
            # Scroll both widgets to the same relative position
            self.log_text.yview_moveto(relative_position)
            self.tree.yview_moveto(relative_position)
            
            # Ensure the matched text is visible
            self.log_text.see(first_match)
            
            # Find and select corresponding tree item
            line_number = int(first_match.split('.')[0])
            self.highlight_corresponding_tree_item(line_number)
            
            self.log_text.focus_set()

    def highlight_corresponding_tree_item(self, line_number):
        # Get all items in the tree
        items = self.tree.get_children()
        
        # Find the corresponding item based on line number
        # You'll need to modify this based on how your tree items correspond to log lines
        for item in items:
            # Assuming you store line numbers in the tree items
            # You might need to adjust this logic based on your actual implementation
            item_text = self.tree.item(item)['values'][0]  # Adjust index as needed
            if str(line_number) in str(item_text):
                # Select and see the item
                self.tree.selection_set(item)
                self.tree.see(item)
                break


    def next_search_result(self):
        if self.search_results:
            # Update the index with wrapping
            self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
            self.Search_Count.config(text=f"{self.total_search_found} \\ {self.current_result_index+1}")

            
            # Get the current match position
            start_index, end_index = self.search_results[self.current_result_index]
            
            # Calculate the relative position for scrolling
            total_lines = float(self.log_text.index('end-1c').split('.')[0])
            current_line = float(start_index.split('.')[0])
            relative_position = current_line / total_lines
            
            # Scroll both widgets to the same relative position
            self.log_text.yview_moveto(relative_position)
            self.tree.yview_moveto(relative_position)
            
            # Ensure the matched text is visible
            self.log_text.see(start_index)
            
            # Find and select corresponding tree item
            line_number = int(start_index.split('.')[0])
            self.highlight_corresponding_tree_item(line_number)
            
            self.log_text.focus_set()


    def prev_search_result(self):
        if self.search_results:
            # Update the index with wrapping
            self.current_result_index = (self.current_result_index - 1) % len(self.search_results)
            
            # Get the current match position
            start_index, end_index = self.search_results[self.current_result_index]
            self.Search_Count.config(text=f"{self.total_search_found} \\ {self.current_result_index+1}")
            # Calculate the relative position for scrolling
            total_lines = float(self.log_text.index('end-1c').split('.')[0])
            current_line = float(start_index.split('.')[0])
            relative_position = current_line / total_lines
            
            # Scroll both widgets to the same relative position
            self.log_text.yview_moveto(relative_position)
            self.tree.yview_moveto(relative_position)
            
            # Ensure the matched text is visible
            self.log_text.see(start_index)
            
            # Find and select corresponding tree item
            line_number = int(start_index.split('.')[0])
            self.highlight_corresponding_tree_item(line_number)
            
            self.log_text.focus_set()


    def close_nodes(self):
        """Close the current level of nodes in the tree view"""
        if self.expanded_levels > 0:
            # Get nodes at the deepest expanded level
            current_level_nodes = self.get_nodes_at_level(self.expanded_levels)
            
            # Close all nodes at the current level
            for node in current_level_nodes:
                self.tree.item(node, open=False)
            
            self.expanded_levels -= 1

    def get_nodes_at_level(self, level):
        """Helper function to get all nodes at a specific level"""
        if level == 1:
            return self.tree.get_children()
        
        nodes = []
        def collect_nodes(parent, current_level):
            if current_level == level:
                nodes.extend(self.tree.get_children(parent))
                return
            for item in self.tree.get_children(parent):
                if self.tree.item(item, "open"):
                    collect_nodes(item, current_level + 1)
        
        collect_nodes('', 1)
        return nodes



    def expand_all_nodes(self):
        """Toggle between expanding all nodes and closing all nodes"""
        if self.expanded_levels == float('inf'):
            # If all nodes are expanded, close them all
            self.recursive_close('')
            self.expanded_levels = 0
        else:
            # If not all expanded, expand all nodes
            self.recursive_expand(self.tree, '')
            self.expanded_levels = float('inf')

    def recursive_close(self, parent):
        """Recursively close all nodes in the tree view"""
        for item in self.tree.get_children(parent):
            self.tree.item(item, open=False)
            self.recursive_close(item)

    def recursive_expand(self, tree, parent):
        """Recursively expand all nodes in the tree view"""
        for item in tree.get_children(parent):
            tree.item(item, open=True)
            self.recursive_expand(tree, item)

####new expand nodes
    def expand_nodes(self):
        """Expand the next level of nodes in the tree view"""
        if self.expanded_levels == 0:
            # First level expansion
            for item in self.tree.get_children():
                self.tree.item(item, open=True)
            self.expanded_levels = 1
        else:
            # Get all nodes at the current level and expand their children
            current_level_nodes = self.get_nodes_at_level(self.expanded_levels)
            has_children = False
            
            for node in current_level_nodes:
                children = self.tree.get_children(node)
                if children:  # If the node has children
                    has_children = True
                    for child in children:
                        self.tree.item(child, open=True)
            
            if has_children:
                self.expanded_levels += 1

    def get_nodes_at_level(self, level):
        """Helper function to get all nodes at a specific level"""
        if level == 1:
            return self.tree.get_children()
        
        nodes = []
        def collect_nodes(parent, current_level):
            if current_level == level:
                nodes.extend(self.tree.get_children(parent))
                return
            for item in self.tree.get_children(parent):
                if self.tree.item(item, "open"):
                    collect_nodes(item, current_level + 1)
        
        collect_nodes('', 1)
        return nodes




    def show_comparison_popup(self, d1, d2, ex_1_in_f2, ex_2_in_f1, i1, i2, file2_name):
        # Create the popup window
        self.popup = tk.Toplevel(self)
        self.popup.title("Comparison Result")
        self.popup.geometry("1200x600")

        # Create a frame to hold the text areas, search components, and the common scrollbar
        main_frame = tk.Frame(self.popup)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame to hold the search components
        search_frame = tk.Frame(main_frame)
        search_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=0)

        
        # Search components for File 1
     # Create a frame to hold the File 1 name label

        self.F1_name = tk.Label(search_frame, text=self.file, font=("impact", 10), bg="#f1f1f1", fg="Black")
        self.F1_name.pack(side=tk.LEFT, fill=tk.Y, anchor="center")

        
        # Search components for File 2
     # Create a frame to hold the File 2 name label

        self.F2_name = tk.Label(search_frame, text=os.path.basename(file2_name), font=("impact", 10), bg="#f1f1f1", fg="Black")
        self.F2_name.pack(side=tk.RIGHT, fill=tk.Y)


        # Create a frame to hold the text areas and the common scrollbar
        frame = tk.Frame(main_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create a common vertical scrollbar
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)

        # Left Text Area (File 1)
        left_text = tk.Text(frame, wrap=tk.WORD, width=60, height=30, yscrollcommand=scrollbar.set)
        left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right Text Area (File 2)
        right_text = tk.Text(frame, wrap=tk.WORD, width=60, height=30, yscrollcommand=scrollbar.set)
        right_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.right_text=right_text
        self.left_text=left_text

        # Attach the scrollbar to the text areas
        scrollbar.config(command=lambda *args: self.sync_scroll(left_text, right_text, *args))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure tags for highlighting
        left_text.tag_configure("foreground", foreground="Orange")
        right_text.tag_configure("foreground", foreground="Orange") #orange foreground

        left_text.tag_configure("blue_highlight", background="white", foreground="Blue")
        right_text.tag_configure("green_highlight", background="yellow", foreground="black")
        right_text.tag_configure("blue_highlight", background="white", foreground="Blue")
        left_text.tag_configure("orange_highlight", background="white", foreground="Orange")
        right_text.tag_configure("orange_highlight", background="white", foreground="Orange")
    #Visual porpouse
        right_text.insert(tk.END, os.path.basename(file2_name)+ "\n")
        right_text.insert(tk.END, "\n")
        left_text.insert(tk.END, self.file + "\n")
        left_text.insert(tk.END, "\n")

# Populate left text area (File 1)
        for idx, line in enumerate(d1):  # Loop through d1
            apply_orange = idx in i2  # Check if the index is in i2

            while "@@" in line or "##" in line:
                if "@@" in line:
                    pre_text, mark, rest = line.partition("@@")
                    left_text.insert(tk.END, pre_text, "foreground" if apply_orange else None)

                    if "@@" in rest:
                        marked_token, _, remaining = rest.partition("@@")
                        left_text.insert(tk.END, marked_token, "green_highlight")
                        line = remaining
                    else:
                        left_text.insert(tk.END, rest, "foreground" if apply_orange else None)
                        break

                elif "##" in line:
                    pre_text, mark, rest = line.partition("##")
                    left_text.insert(tk.END, pre_text, "foreground" if apply_orange else None)

                    if "##" in rest:
                        marked_token, _, remaining = rest.partition("##")
                        left_text.insert(tk.END, marked_token, "blue_highlight")
                        line = remaining
                    else:
                        left_text.insert(tk.END, rest, "foreground" if apply_orange else None)
                        break
            else:
                left_text.insert(tk.END, line + "\n", "foreground" if apply_orange else None)

            # Add an extra newline for spacing
            left_text.insert(tk.END, "\n")


        # Populate right text area (File 2)
        for idx, line in enumerate(d2):
            
            apply_orange = idx in i1  # Check if index is in i1
            
            while "@@" in line or "##" in line:
                if "@@" in line:
                    pre_text, mark, rest = line.partition("@@")
                    right_text.insert(tk.END, pre_text, "foreground" if apply_orange else None)
                    
                    if "@@" in rest:
                        marked_token, _, remaining = rest.partition("@@")
                        right_text.insert(tk.END, marked_token, "green_highlight")
                        line = remaining
                    else:
                        right_text.insert(tk.END, rest, "foreground" if apply_orange else None)
                        break
                elif "##" in line:
                    pre_text, mark, rest = line.partition("##")
                    right_text.insert(tk.END, pre_text, "foreground" if apply_orange else None)
                    
                    if "##" in rest:
                        marked_token, _, remaining = rest.partition("##")
                        right_text.insert(tk.END, marked_token, "blue_highlight")
                        line = remaining
                    else:
                        right_text.insert(tk.END, rest, "foreground" if apply_orange else None)
                        break
            else:
                right_text.insert(tk.END, line + "\n", "foreground" if apply_orange else None)
            right_text.insert(tk.END, "\n")


            
        if ex_1_in_f2:
            for item in ex_1_in_f2:
                right_text.insert(tk.END, "\n")
                if item.startswith("[FOUND"):
                    right_text.insert(tk.END, item.strip('[FOUND]')+"\n", "orange_highlight")
                elif item.startswith("[NOT FOUND]"):
                    right_text.insert(tk.END, item.strip("[NOT FOUND]") +"\n", "blue_highlight")
                    
        if ex_2_in_f1:
            for item in ex_2_in_f1:
                left_text.insert(tk.END,  "\n")
                if item.startswith("[FOUND"):
                    left_text.insert(tk.END, item.strip('[FOUND]') +"\n", "orange_highlight")
                elif  item.startswith("[NOT FOUND]"):
                    left_text.insert(tk.END, item.strip('[NOT FOUND]')+"\n", "blue_highlight")
                
        #popup=Toplevel()




    def sync_scroll(self, text1, text2, *args):
        """Synchronize scrolling between two text widgets."""
        text1.yview(*args)
        text2.yview(*args)




    def select_file_to_compare(self, Tab):
        self.file_to_compare = filedialog.askopenfilename(title="Select file to compare")
        if self.file_to_compare:
          
            file_2 = read_lines_list(self.file_to_compare)
            d1,d2,extra_1_in_file2,extra_2_in_file1,index_found_1,index_found_2= self.compare_(self.log_lines_compare,file_2,Tab)


            # Show differences in a new popup window
            self.show_comparison_popup(d1, d2, extra_1_in_file2, extra_2_in_file1,index_found_1,index_found_2, self.file_to_compare)
            #self.after(0, self.show_comparison_popup, d1, d2, extra_1_in_file2, extra_2_in_file1)

    def compare_(self, file_1, file2,Tab):
        
        file1=[]
        for i in  file_1:
            file1.append(i)

        diff_file2 = []
        diff_rows = []
        diff_file1= []

        e1 = []  # extra rows in file 1
        e2 = []  # extra rows in file 2
        row = 0  # Initialize row


        # Initialize QApplication if it doesn't exist
        if not QApplication.instance():
            app = QApplication(sys.argv)

        # Create QProgressDialog
        progress = QProgressDialog(
            "Processing log lines...",  # labelText
            "Cancel",                   # cancelButtonText
            0,                         # minimum
            100,                       # maximum
            None,                      # parent
            Qt.WindowType.WindowStaysOnTopHint
        )
        progress.setWindowTitle("Progress")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        progress.setValue(0) 
        progress.setMaximum(max(len(file1), len(file2)))
        QApplication.processEvents()


        while row < max(len(file1), len(file2)):  # Continuously check the updated max_length
            
            # Handle extra rows in file2
            if row >= len(file1):
                for extra_row in file2[row:]:
                    e2.append(extra_row)
                break

            # Handle extra rows in file1
            if row >= len(file2):
                for extra_row in file1[row:]:
                    e1.append(extra_row)
                break

            # Tokenize and compare the current rows
            r2, diff_rows, flag = tokenize(file1[row], file2[row], row, diff_rows)

            if flag:
                file1.insert(row, " - ")

            #diff_file1.append(" ")
            diff_file1.append(file1[row])
            #diff_file2.append(" ")
            diff_file2.append(str(file2[row][:29]) + " " + r2)

            row += 1  # Increment row manually
            progress.setValue(row)
            QApplication.processEvents()  # Keep the GUI responsive
            self.update_idletasks()  


        # Filter out timestamps from both files to compare contents without timestamps

        
        if len(e2) != 0:
            e2_r,index_found_2 = find_matching_sublists(file1, e2, diff_rows)
            if Tab !="Main":
                self.ask_rows_text.tag_configure("green", foreground="green")
                self.ask_rows_text.insert(tk.END,("\n Extra rows in File 2 " + compareGPT(e2_r,api_key)),"green")
                self.ask_rows_text.insert(tk.END,"\n" )
            for i in e2:
                diff_file1.append("-")
        else:
            e2_r = []
            index_found_2 = []

        if len(e1) != 0:
            for i in e1:
                diff_file2.append("-")
            e1_r,index_found_1 = find_matching_sublists(file2, e1, diff_rows)
            if Tab !="Main":
                self.ask_rows_text.tag_configure("green", foreground="green")
                self.ask_rows_text.insert(tk.END,("\n Extra rows in File 1 " + compareGPT(e1_r,api_key)),"green")
                self.ask_rows_text.insert(tk.END,"\n" )
        else:
            e1_r = []
            index_found_1=[]

        
        #file1.insert(0, f"File_1: {self.file} \n")
        return diff_file1, diff_file2, e2_r, e1_r, index_found_1,index_found_2
    





    def open_popup(self):
        # Create the popup window
        self.popup = tk.Toplevel()
        self.popup.title("SiemensGPT")
        self.popup.geometry("600x500")
        self.popup.configure(bg="#f1f1f1")
         
        # Add content to the popup window
        popup_frame = tk.Frame(self.popup, bg="#f1f1f1")
        popup_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        popup_label = tk.Label(popup_frame, text="SiemensGPT", font=("Arial", 18, "bold"), bg="#f1f1f1", fg="#333333")
        popup_label.pack(pady=10)

        self.selected_rows_label = tk.Label(popup_frame, text="Insert The Log Rows You Want To Analyze:", font=("Arial", 14), bg="#f1f1f1", fg="#333333")
        self.selected_rows_label.pack(pady=5)

        self.selected_rows_text = tk.Text(popup_frame, height=5, width=60, wrap=tk.WORD, font=("Arial", 12), bg="#f8f8f8", fg="#333333", borderwidth=2, relief="groove")
        self.selected_rows_text.pack(pady=10, fill=tk.BOTH, expand=True)

        self.selected_rows_text_scrollbar = ttk.Scrollbar(self.selected_rows_text, orient=tk.VERTICAL, command=self.selected_rows_text.yview)
        self.selected_rows_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_rows_text.configure(yscrollcommand=self.selected_rows_text_scrollbar.set)

            # Add clear button for selected_rows_text
    # Add clear button for selected_rows_text
        self.selected_rows_clear_button = tk.Button(self.selected_rows_text, text="Clear_Log", font=("Arial", 7), bg="#FF6347", fg="black", command=self.clear_text_log)
        self.selected_rows_clear_button.place(relx=0.95, rely=0.02, anchor="ne")

        self.ask_rows_label = tk.Label(popup_frame, text="Make Your Questions:", font=("Arial", 14), bg="#f1f1f1", fg="#333333")
        self.ask_rows_label.pack(pady=5)

        self.ask_rows_text = tk.Text(popup_frame, height=3, width=60, wrap=tk.WORD, font=("Arial", 12), bg="#f8f8f8", fg="#333333", borderwidth=2, relief="groove")
        self.ask_rows_text.pack(pady=10, fill=tk.BOTH, expand=True)

        self.ask_rows_text_scrollbar = ttk.Scrollbar(self.ask_rows_text, orient=tk.VERTICAL, command=self.ask_rows_text.yview)
        self.ask_rows_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ask_rows_text.configure(yscrollcommand=self.ask_rows_text_scrollbar.set)

    # Add clear button for ask_rows_text
        self.ask_rows_clear_button = tk.Button(self.ask_rows_text, text="Clear_Answer", font=("Arial", 7), bg="#FF6347", fg="black", command=self.clear_text)
        self.ask_rows_clear_button.place(relx=0.95, rely=0.02, anchor="ne")


# Add Time Button
        self.toggle_button = tk.Button(popup_frame, text="Use XML Processing", font=("Arial", 11), bg="White", fg="Blue", command=self.Time_Analysis)
        self.toggle_button.pack(side=tk.BOTTOM, pady=10, padx=20)

        # Add the Compare button
        self.compare_button = tk.Button(popup_frame, text="Compare Files", font=("Arial", 11), bg="#FF8C00", fg="Black", command=lambda: self.select_file_to_compare("Tab2"))
        self.compare_button.pack(side=tk.RIGHT, pady=10, padx=10)


        self.print_button = tk.Button(popup_frame, text="Ask SiemensGPT", font=("Arial", 11), bg="#4CAF50", fg="white", command=self.Ask_SiemensGPT)
        self.print_button.pack(side=tk.LEFT, pady=10, padx=10)

        popup_frame.bind_all('<Return>', lambda event: self.Ask_SiemensGPT())

    def show_Result_popup(self, query_data):
        root = tk.Toplevel()
        root.title(f"Hierarchical Query Analysis of {file_name}")
        root.geometry("1400x900")

        # Create main frame with specific padding
        main_frame = tk.Frame(root, padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Calculate the desired canvas width (70% of window width)
        canvas_width = int(1400 * 0.70)  # 980 pixels

        # Create scrollable canvas with specific dimensions
        canvas = tk.Canvas(
            main_frame, 
            width=canvas_width,
            height=800,  # Fixed height, adjust if needed
            highlightthickness=0  # Removes border
        )
        scrollbar = tk.Scrollbar(main_frame, command=canvas.yview, width=16)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # Configure grid weights for perfect centering
        main_frame.grid_columnconfigure(0, weight=1)  # Left margin
        main_frame.grid_columnconfigure(1, weight=0)  # Canvas column (fixed width)
        main_frame.grid_columnconfigure(2, weight=0)  # Scrollbar column
        main_frame.grid_columnconfigure(3, weight=1)  # Right margin
        main_frame.grid_rowconfigure(0, weight=1)

        # Place canvas and scrollbar
        canvas.grid(row=0, column=1, sticky='ns')
        scrollbar.grid(row=0, column=2, sticky='ns')

        # Create inner frame with specific width
        inner_frame = tk.Frame(canvas, width=canvas_width)
        canvas.create_window(
            (canvas_width//2, 0),  # Center horizontally
            window=inner_frame, 
            anchor='n',  # Top center anchor
            width=canvas_width  # Fix the width
        )

        # Make sure the inner frame maintains its width
        inner_frame.grid_propagate(False)

        def format_time_delta(delta_time_ms):
            """Convert milliseconds to a readable format"""
            seconds = delta_time_ms / 1000
            if seconds < 1:
                return f"{delta_time_ms:.2f}ms"
            elif seconds < 60:
                return f"{seconds:.2f}s"
            else:
                minutes = int(seconds // 60)
                remaining_seconds = seconds % 60
                return f"{minutes}m {remaining_seconds:.2f}s"

        def create_node_display(parent, node_data, level=0):
            """Recursively create display for node and its subnodes"""
            frame = tk.Frame(parent, relief=tk.GROOVE, borderwidth=1)
            frame.pack(fill=tk.X, pady=2, padx=level*10)
                # Create a header frame to contain both the label and button
            header_frame = tk.Frame(frame)
            header_frame.pack(fill=tk.X, padx=5, pady=2)

            # Create header with node type and timing
            header_text = f"{'  ' * level}► {node_data['node_type']}"
            if 'delta_time_ms' in node_data and  '__query' in node_data['node_type'].lower():
                header_text += f" (Time: {format_time_delta(node_data['delta_time_ms'])}"
                if 'percentage_of_total' in node_data:
                    header_text += f", {node_data['percentage_of_total']:.2f}%"
                header_text += ")"

            header = tk.Label(header_frame, text=header_text, anchor='w', justify=tk.LEFT)
            header.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def get_sql_text(node_data):
                """Extract SQL text from node data"""
                if '__query' in node_data['node_type'].lower():
                    
                    # First try to find SQL text in subnodes
                    for subnode in node_data.get('subnodes', []):
                        if subnode['node_type'] == '__parsedSQLText' and 'text' in subnode:
                            return subnode['text']
                        elif subnode['node_type'] == '__rawSQLText' and 'text' in subnode:
                            return subnode['text']
                    
                    # If not found in subnodes, check attributes
                    attributes = node_data.get('attributes', {})
                    if 'rawSQLText' in attributes:
                        return attributes['rawSQLText']
                    elif 'parsedSQLText' in attributes:
                        return attributes['parsedSQLText']
                return None

            def on_find_query():
                sql_text = get_sql_text(node_data)
                if sql_text:
                        self.clipboard_clear()
                        self.clipboard_append(sql_text)
                else:
                    print("No SQL query found in this node.")

            # Only show the Find Query button if this node might contain a query
            if '__query' in node_data['node_type'].lower() and  node_data['node_type'] not in ['__parsedSQLText', '__rawSQLText','__queryParameter','__queryParameters']: 
                find_button = tk.Button(
                    header_frame,
                    text="Copy Query",
                    command=on_find_query,
                    relief=tk.GROOVE,
                    background="Green",
                    padx=5,
                    pady=2,
                    font=('Arial', 8)
                )
                find_button.pack(side=tk.RIGHT, padx=(5, 0))

            # Create collapsible content section
            content_frame = tk.Frame(frame)
            content_frame.pack(fill=tk.X, padx=5, pady=2)


            # Display node text if it exists
            if 'text' in node_data:
                # Determine the height based on node type
                text_height = 15 if node_data['node_type'] in ['__parsedSQLText', '__rawSQLText'] else 5
                
                # Create a frame to hold the Text widget and scrollbar
                text_frame = tk.Frame(content_frame)
                text_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

                # Create a Text widget for the node text with adjusted height
                node_text_widget = tk.Text(text_frame, 
                                        wrap='word', 
                                        height=text_height,  # Using the dynamic height
                                        font=('Courier New', 10))

                # Create and configure scrollbar
                scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=node_text_widget.yview)
                node_text_widget.configure(yscrollcommand=scrollbar.set)

                # Pack the Text widget and scrollbar
                node_text_widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                # Insert the node text
                node_text_widget.insert(tk.END, f"{node_data['text']}")
                node_text_widget.config(state=tk.DISABLED)  # Make the Text widget read-only


            # Display attributes if they exist
            if 'attributes' in node_data:
                attr_text = "Attributes:\n" + "\n".join(f"{k}: {v}" 
                        for k, v in node_data['attributes'].items())
                attr_label = tk.Label(content_frame, 
                                    text=attr_text, 
                                    wraplength=800, 
                                    justify=tk.LEFT)
                attr_label.pack(fill=tk.X)

            # Recursively display subnodes
            if 'subnodes' in node_data and node_data['subnodes']:
                subnodes_frame = tk.Frame(frame)
                subnodes_frame.pack(fill=tk.X, pady=2)
                
                for subnode in node_data['subnodes']:
                    create_node_display(subnodes_frame, subnode, level + 1)
   

        # Display header with total statistics and warning if needed
        total_queries = len(query_data)
        displayed_queries = min(total_queries, 40)
        
        header_text = []
        if query_data:
            total_time_ms = sum((q.get('delta_time_ms', 0) for q in query_data))
            header_text.append(f"Total Analysis Time: {format_time_delta(total_time_ms)}")
            header_text.append(f"Total Queries Found: {total_queries}")
            
            if total_queries > 40:
                header_text.append(f"Displaying top 40 most time-consuming queries")
                header_text.append(f"({total_queries - 40} queries hidden)")
                
                # Add warning in red
                warning_label = tk.Label(inner_frame, 
                                    text="⚠️ Large number of queries detected - showing top 40 only",
                                    fg='red',
                                    font=('Arial', 11, 'bold'))
                warning_label.pack(pady=(5,0))

        header_label = tk.Label(inner_frame, 
                            text="\n".join(header_text), 
                            font=('Arial', 12, 'bold'))
        header_label.pack(pady=10)

        # Display limited number of queries
        real_query_count = 0

        for i,query in enumerate(query_data[:displayed_queries], 1):
            if query['node_type'] not in ['__parsedSQLText', '__rawSQLText','__queryParameter','__queryParameters']: 
                real_query_count+=1
                query_frame = tk.Frame(inner_frame, relief=tk.RAISED, borderwidth=2)
                query_frame.pack(fill=tk.X, pady=5)
                
                # Add query number to the display
                number_label = tk.Label(query_frame, 
                                    text=f"Query #{real_query_count}", 
                                    font=('Arial', 11, 'bold'))
                number_label.pack(anchor='w', padx=5, pady=(5,0))
                
                create_node_display(query_frame, query)

        # Add scrolling functionality
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        root.bind('<Up>', lambda e: canvas.yview_scroll(-1, "units"))
        root.bind('<Down>', lambda e: canvas.yview_scroll(1, "units"))




    def Time_Analysis(self):

            self.file_chosen = filedialog.askopenfilename(title="Select XML file to Analyze")
            if self.file_chosen:

                if self.file_chosen.endswith('.xml'):
                    self.only_show_XML_TreeView(self.file_chosen)
                else:
                    self.show_XML_TreeView(self.file_chosen)


    def Time_Analysis_main(self):
        # First try to load the JSON file
        json_file = f"{self.file.split('.')[0]}_tree_analysis.json"
        xml_file = f"{self.file.split('.')[0]}.xml"
        
        os.chdir(self.log_file.split(f'{self.file}')[0])#position in the folder of the chosen log file, cause at ht begining it is modified by a opened new file
        if  os.path.isdir(self.file.split('.')[0]):
            os.chdir(self.file.split('.')[0])
        if os.path.exists(json_file):
            self.show_XML_TreeView(json_file)
            
        elif os.path.exists(xml_file):
            self.only_show_XML_TreeView(xml_file)
            
        else:
            self.file_chosen = filedialog.askopenfilename(
                title="Select XML file to Analyze",
                filetypes=[
                    ("XML files", "*.json"),
                    ("JSON files", "*.xml"),
                    ("All files", "*.*")
                ]
            )
            
            if self.file_chosen:
                if self.file_chosen.endswith('.xml'):
                    self.only_show_XML_TreeView(self.file_chosen)
                else:
                    self.show_XML_TreeView(self.file_chosen)
            else:
                messagebox.showerror("No Json or Xml Found ")



 #---------------------------------------------------------------------------------------------------------------
    def Analyze_XML(self, file_xml):
        try:
            tree = etree.parse(file_xml)
           
            root = tree.getroot()
            all_query_data = []

            def get_timing_info(node):
                """Extract timing information from a node"""
                start_time_elem = node.find('./__startTime')
                end_time_elem = node.find('./__endTime')
                
                if start_time_elem is not None and end_time_elem is not None:
                    try:
                        start_time_str = start_time_elem.text.strip()
                        end_time_str = end_time_elem.text.strip()
                        
                        start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M:%S.%f')
                        end_time = datetime.strptime(end_time_str, '%Y/%m/%d %H:%M:%S.%f')
                        delta_time = end_time - start_time  # This returns a timedelta object
                        
                        return {
                            'start_time': start_time_str,
                            'end_time': end_time_str,
                            'delta_time': delta_time,
                            'delta_time_ms': delta_time.total_seconds() * 1000  # Convert to milliseconds
                        }
                    except ValueError as e:
                        messagebox.showerror(f"Error parsing datetime: {e}")
                return None

            def analyze_node(node, parent_timing=None):
                """Recursively analyze a node and its children"""
                node_data = {
                    'node_type': node.tag,
                    'subnodes': []
                }
                
                # Get timing information for this node
                timing_info = get_timing_info(node)
                if timing_info:
                    node_data.update(timing_info)
                elif parent_timing:
                    node_data.update(parent_timing)

                # Get node's direct text if it exists
                if node.text and node.text.strip():
                    node_data['text'] = node.text.strip()

                # Get node's attributes
                if node.attrib:
                    node_data['attributes'] = dict(node.attrib)

                # Process all child nodes
                for child in node:
                    child_data = analyze_node(child, timing_info or parent_timing)
                    if child_data:
                        node_data['subnodes'].append(child_data)

                return node_data

            # Find all query nodes and their timing context
            for node in root.findall('.//*'):
                if '__query' in node.tag:
                    # Find the nearest parent with timing information
                    parent = node
                    parent_timing = None
                    while parent is not None:
                        timing = get_timing_info(parent)
                        if timing:
                            parent_timing = timing
                            break
                        parent = parent.getparent()

                    # Analyze the query node and all its subnodes
                    query_data = analyze_node(node, parent_timing)
                    if query_data:
                        all_query_data.append(query_data)

            # Sort queries by delta time (from highest to lowest)
            all_query_data.sort(key=lambda x: x.get('delta_time_ms', 0), reverse=True)

            # Calculate and add percentage of total time for each query
            if all_query_data:
                total_time_ms = sum((q.get('delta_time_ms', 0) for q in all_query_data))
                for query in all_query_data:
                    if 'delta_time_ms' in query:
                        query['percentage_of_total'] = (query['delta_time_ms'] / total_time_ms) * 100

            return all_query_data

        except ET.ParseError as e:
            messagebox.showerror(f"Error parsing XML file: {e}")
            raise


##########################################################

    def only_show_XML_TreeView(self, file_xml):
            try:
                # Create new window
                tree_window = tk.Toplevel()
                tree_window.title("XML Structure Analysis")
                tree_window.geometry("1400x800")

                # Create main frame
                main_frame = ttk.Frame(tree_window)
                main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # Create tree view with scrollbars
                tree_frame = ttk.Frame(main_frame)
                tree_frame.pack(fill=tk.BOTH, expand=True)

                # Create treeview
                tree = ttk.Treeview(tree_frame)
                
                # Add scrollbars
                vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
                hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
                tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

                # Grid layout
                tree.grid(column=0, row=0, sticky='nsew')
                vsb.grid(column=1, row=0, sticky='ns')
                hsb.grid(column=0, row=1, sticky='ew')
                tree_frame.grid_columnconfigure(0, weight=1)
                tree_frame.grid_rowconfigure(0, weight=1)

                # Configure tree columns
                tree["columns"] = ("tag", "time", "attributes")
                tree.column("#0", width=50, stretch=tk.NO)  # Index column
                tree.column("tag", width=200)
                tree.column("time", width=100)
                tree.column("attributes", width=800)  # Increased width for SQL text

                # Configure tree headings
                tree.heading("#0", text="Index")
                tree.heading("tag", text="Node Type")
                tree.heading("time", text="Execution Time")
                tree.heading("attributes", text="SQL Information")
                
                tree.bind('<Button-3>', lambda event: self.show_sql_popup(tree, event))

                def format_time_delta(delta_time_ms):
                    """Convert milliseconds to a readable format"""
                    if delta_time_ms is None:
                        return "N/A"
                    seconds = delta_time_ms / 1000
                    if seconds < 1:
                        return f"{delta_time_ms:.2f}ms"
                    elif seconds < 60:
                        return f"{seconds:.2f}s"
                    else:
                        minutes = int(seconds // 60)
                        remaining_seconds = seconds % 60
                        return f"{minutes}m {remaining_seconds:.2f}s"

                def get_node_timing(node):
                    """Extract timing information from a node"""
                    start_time_elem = node.find('./__startTime')
                    end_time_elem = node.find('./__endTime')
                    
                    if start_time_elem is not None and end_time_elem is not None:
                        try:
                            start_time_str = start_time_elem.text.strip()
                            end_time_str = end_time_elem.text.strip()
                            
                            start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M:%S.%f') 
                            end_time = datetime.strptime(end_time_str, '%Y/%m/%d %H:%M:%S.%f')
                            delta_time = end_time - start_time
                            
                            return {
                                'delta_time_ms': delta_time.total_seconds() * 1000
                            }
                        except ValueError as e:
                            messagebox.showerror(f"Error parsing datetime: {e}")
                    return None

                def insert_node(parent_id, node, index):
                    """Recursively insert nodes into tree with level-based top 3 highlighting"""
                    # Dictionary to store timing information for each level
                    level_timing = {}
                    
                    def process_level(current_node, current_parent_id, current_index, level=0):
                        """Process nodes at each level, tracking timing information"""
                        # Initialize level in level_timing if not exists
                        if level not in level_timing:
                            level_timing[level] = []

                        # Get timing information
                        timing_info = get_node_timing(current_node)
                        
                        # Prepare node attributes display
                        attr_text = ""
                        if '__query' in current_node.tag:
                            sql_info = []
                            
                            # Check for raw SQL
                            raw_sql = current_node.find('./__rawSQLText')
                            if raw_sql is not None and raw_sql.text:
                                sql_info.append(f"Raw SQL: {raw_sql.text.strip()}")
                            
                            # Check for parsed SQL
                            parsed_sql = current_node.find('./__parsedSQLText')
                            if parsed_sql is not None and parsed_sql.text:
                                sql_info.append(f"Parsed SQL: {parsed_sql.text.strip()}")
                            
                            attr_text = " | ".join(sql_info)
                        
                        # Insert node into tree
                        node_id = tree.insert(current_parent_id, 'end',
                                            values=(current_node.tag,
                                                format_time_delta(timing_info['delta_time_ms'] if timing_info else None),
                                                attr_text),
                                            text=str(current_index))

                        # Store timing information if available
                        if timing_info and timing_info['delta_time_ms']:
                            level_timing[level].append({
                                'node_id': node_id,
                                'node_tag': current_node.tag,
                                'time_ms': timing_info['delta_time_ms']
                            })

                        # Process all child nodes at the next level
                        children = list(current_node)
                        for i, child in enumerate(children):
                            process_level(child, node_id, i + 1, level + 1)

                        # After processing all nodes at this level, highlight top 3
                        if level_timing[level]:
                            # Sort nodes at this level by execution time
                            level_nodes = sorted(level_timing[level], 
                                            key=lambda x: x['time_ms'], 
                                            reverse=True)
                            
                            # Highlight top 3 at this level
                            for i, node_info in enumerate(level_nodes[:3]):
                                tree.item(node_info['node_id'], 
                                        tags=(f'level_{level}_top_{i+1}',))
                                # Configure tag with red color
                                tree.tag_configure(f'level_{level}_top_{i+1}', 
                                                foreground='red')

                    # Start processing from the root level
                    process_level(node, parent_id, index)

                # Create bottom frame for search and analyze button
                bottom_frame = ttk.Frame(main_frame)
                bottom_frame.pack(fill=tk.X, pady=(10, 0))

                # Create search frame on the left side
                search_frame = ttk.Frame(bottom_frame)
                search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)


                # Create analyze button frame on the right side
                analyze_frame = ttk.Frame(bottom_frame)
                analyze_frame.pack(side=tk.RIGHT)

                def analyze_queries():
                    query_data = self.Analyze_XML(file_xml)
                    if query_data:
                        self.show_Result_popup(query_data)

                analyze_button = ttk.Button(
                    analyze_frame, 
                    text="Analyze Queries", 
                    command=analyze_queries,
                    style='Accent.TButton'
                )
                analyze_button.pack(side=tk.RIGHT, padx=(10, 0))

                # Parse XML and populate tree
                try:
                    xml_tree = ET.parse(file_xml)
                    root = xml_tree.getroot()
                    
                    # Create header frame for statistics
                    header_frame = ttk.Frame(main_frame)
                    header_frame.pack(fill=tk.X, pady=(0, 10))

                    # Get the first time encountered (total execution time)
                    def get_first_time(node):
                        timing_info = get_node_timing(node)
                        if timing_info and timing_info['delta_time_ms']:
                            return timing_info['delta_time_ms']
                        for child in node:
                            child_time = get_first_time(child)
                            if child_time is not None:
                                return child_time
                        return None

                    total_time_ms = get_first_time(root)
                    total_time = format_time_delta(total_time_ms) if total_time_ms is not None else "N/A"
                    
                    # Update window title
                    tree_window.title(f"XML Structure Analysis - Total Time: {total_time}")

                    # Create and pack statistics label
                    stats_frame = ttk.Frame(header_frame)
                    stats_frame.pack(side=tk.LEFT, fill=tk.X)
                    
                    stats_label = ttk.Label(stats_frame, 
                                        text=f"Total Execution Time: {total_time}",
                                        font=('Arial', 10, 'bold'))
                    stats_label.pack(anchor='w')

                    # Populate tree
                    insert_node('', root, 1)

                    # Add mousewheel scrolling
                    def on_mousewheel(event):
                        tree.yview_scroll(int(-1*(event.delta/120)), "units")
                    tree.bind('<MouseWheel>', on_mousewheel)
                    '''
                    # Bind keyboard shortcuts
                    tree_window.bind('<Control-f>', lambda e: search_entry.focus())
                    search_entry.bind('<Return>', lambda e: search_tree())
                    '''
                except ET.ParseError as e:
                    messagebox.showerror("Error", f"Error parsing XML file: {e}")
                    tree_window.destroy()
                    return

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                if 'tree_window' in locals():
                    tree_window.destroy()






######################################################_________________________________--------------################


    def show_XML_TreeView(self, json_file):
        try:


            xml_filename = json_file.replace('_tree_analysis.json', '.xml')
            
            tree_window = tk.Toplevel()
            tree_window.title("XML Structure Analysis")
            tree_window.geometry("1400x800")

            main_frame = ttk.Frame(tree_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            # Add after creating main_frame and before tree_frame

            #search
            search_frame = ttk.Frame(main_frame)
            search_frame.pack(fill=tk.X, pady=(0, 10))

            search_label = ttk.Label(search_frame, text="Search Content:")
            search_label.pack(side=tk.LEFT, padx=(0, 5))

            search_entry = ttk.Entry(search_frame)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            search_button = ttk.Button(search_frame, text="Search", command=lambda: perform_search())
            search_button.pack(side=tk.LEFT, padx=(5, 0))

            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            tree = ttk.Treeview(tree_frame)
            
            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            tree.grid(column=0, row=0, sticky='nsew')
            vsb.grid(column=1, row=0, sticky='ns')
            hsb.grid(column=0, row=1, sticky='ew')
            tree_frame.grid_columnconfigure(0, weight=1)
            tree_frame.grid_rowconfigure(0, weight=1)

            # Configure tree columns
            tree["columns"] = ("tag", "time", "attribute", "sql")
            tree.column("#0", width=50, stretch=tk.NO)
            tree.column("tag", width=200)
            tree.column("time", width=100)
            tree.column("attribute", width=200)
            tree.column("sql", width=1000, stretch=True)  # Wide column for SQL


            #item=tree.selection()
            #sql_text= tree.item(item)['values']
            tree.bind('<Button-3>', lambda event: self.show_sql_popup(tree, event))
            search_entry.bind("<Return>", lambda event: perform_search())
            tree.bind("<Control-f>", lambda event: search_entry.focus_set())

            tree.heading("#0", text="Index")
            tree.heading("tag", text="Node Type")
            tree.heading("time", text="Execution Time")
            tree.heading("attribute", text="Content")
            tree.heading("sql", text="SQL Query")

            def format_time_delta(delta_time_ms):
                if delta_time_ms is None:
                    return "N/A"
                seconds = delta_time_ms / 1000
                if seconds < 1:
                    return f"{delta_time_ms:.2f}ms"
                elif seconds < 60:
                    return f"{seconds:.2f}s"
                else:
                    minutes = int(seconds // 60)
                    remaining_seconds = seconds % 60
                    return f"{minutes}m {remaining_seconds:.2f}s"

            
            def get_sql_text(node_data):
                """Extract SQL text from node data"""
                if '__query' in node_data['node_type']:
                    # First try to find SQL text in subnodes
                    for subnode in node_data.get('subnodes', []):
                        if subnode['node_type'] == '__parsedSQLText' and 'text' in subnode:
                            return subnode['text']
                        elif subnode['node_type'] == '__rawSQLText' and 'text' in subnode:
                            return subnode['text']
                    
                    # If not found in subnodes, check attributes
                    attributes = node_data.get('attributes', {})
                    if 'rawSQLText' in attributes:
                        return attributes['rawSQLText']
                    elif 'parsedSQLText' in attributes:
                        return attributes['parsedSQLText']
                    
                    # Finally check direct text field
                    if 'text' in node_data:
                        return node_data['text']
                return ""
            
            def get_Content_text(node_data):
                """Extract content text from node data"""
                if  '__startTime' in node_data['node_type'] or '__endTime' in node_data['node_type'] or '__query' in node_data['node_type']:
                    return ""
                    # First try to find SQL text in subnodes
                for subnode in node_data.get('subnodes', []):
                    if '__startTime' not in subnode['node_type'] and '__endTime' not in subnode['node_type'] and '__parsedSQLText' not in subnode['node_type'] and '__rawSQLText' not in subnode['node_type'] and  'text' in subnode:
                        return subnode['text']
                    
                
                # If not found in subnodes, check attributes
                attributes = node_data.get('attributes', {})
                if attributes:
                    return attributes
                
                # Finally check direct text field
                if 'text' in node_data:
                    return node_data['text']
                return ""


            def insert_node(parent_id, node_data, index):
                time_ms = node_data.get('delta_time_ms')
                rank = node_data.get('rank')
                
                # Get SQL text using the get_sql_text function
                sql_text = get_sql_text(node_data)
                content= get_Content_text(node_data)
                
                # Insert node into tree
                node_id = tree.insert(parent_id, 'end',
                                    values=(node_data['node_type'],
                                        format_time_delta(time_ms) if time_ms else "N/A",
                                        content,
                                        sql_text),
                                    text=str(index))

                # Apply red color if node has rank 1, 2, or 3
                if rank in [1, 2, 3]:
                    tree.tag_configure(f'rank_{rank}', foreground='red')
                    tree.item(node_id, tags=(f'rank_{rank}',))

                # Process subnodes
                for i, subnode in enumerate(node_data.get('subnodes', [])):
                    insert_node(node_id, subnode, i + 1)

            def expand_rank1_nodes():
                def traverse_tree(node):
                    # Get all children of the current node
                    children = tree.get_children(node)
                    
                    # Check if current node has rank 1
                    item = tree.item(node)
                    tags = item.get('tags', [])
                    if 'rank_1' in tags:
                        # Expand all parent nodes up to this node
                        parent = tree.parent(node)
                        while parent:
                            tree.item(parent, open=True)
                            parent = tree.parent(parent)
                        # Expand this node
                        tree.item(node, open=True)
                    
                    # Recursively check all children
                    for child in children:
                        traverse_tree(child)
                
                # Start traversal from root nodes
                root_nodes = tree.get_children()
                for root_node in root_nodes:
                    traverse_tree(root_node)


            # Create bottom frame for buttons
            bottom_frame = ttk.Frame(main_frame)
            bottom_frame.pack(fill=tk.X, pady=(10, 0))

            analyze_frame = ttk.Frame(bottom_frame)
            analyze_frame.pack(side=tk.RIGHT)
            expand_frame = ttk.Frame(bottom_frame)
            expand_frame.pack(side=tk.LEFT)


            def analyze_queries():
                query_data = self.Analyze_XML(xml_filename)
                if query_data:
                    self.show_Result_popup(query_data)

            analyze_button = ttk.Button(
                analyze_frame, 
                text="Analyze Queries", 
                command=analyze_queries,
                style='Accent.TButton'
            )
            analyze_button.pack(side=tk.RIGHT, padx=(10, 0))

            expand_rank1_button = ttk.Button(expand_frame, text="Expand Critical nodes", command=lambda: expand_rank1_nodes())
            expand_rank1_button.pack(side=tk.LEFT, padx=(5, 0))

            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)

                header_frame = ttk.Frame(main_frame)
                header_frame.pack(fill=tk.X, pady=(0, 10))

                tree_structure = json_data['tree_structure']
                #total_time_ms = tree_structure.get('delta_time_ms')
                #total_time = format_time_delta(total_time_ms) if total_time_ms else "N/A"

                tree_window.title(f"Tree Structure Analysis")

                stats_frame = ttk.Frame(header_frame)
                stats_frame.pack(side=tk.LEFT, fill=tk.X)

                insert_node('', tree_structure, 1)

                def on_mousewheel(event):
                    tree.yview_scroll(int(-1*(event.delta/120)), "units")
                tree.bind('<MouseWheel>', on_mousewheel)

            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Error parsing JSON file: {e}")
                tree_window.destroy()
                return
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while processing JSON: {e}")
                tree_window.destroy()
                return

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            if 'tree_window' in locals():
                tree_window.destroy()




        def expand_all_nodes(tree, item):
            tree.item(item, open=True)
            for child in tree.get_children(item):
                expand_all_nodes(tree, child)

        def collapse_all_nodes(tree, item):
            tree.item(item, open=False)
            for child in tree.get_children(item):
                collapse_all_nodes(tree, child)

        def clear_highlights(tree):
            # Remove highlighting from all items
            for item in tree.tag_has('search_result'):
                tree.item(item, tags=[t for t in tree.item(item)['tags'] if t != 'search_result'])

        def search_tree(tree, item, search_text, found_items):
            # Get the content value (third column)
            values = tree.item(item)['values']
            if values and len(values) > 2:
                content = str(values[2]).lower()
                if search_text.lower() in content:
                    found_items.append(item)
                    # Preserve existing tags and add search_result
                    current_tags = list(tree.item(item)['tags'] or [])
                    if 'search_result' not in current_tags:
                        current_tags.append('search_result')
                    tree.item(item, tags=current_tags)
            
            # Search through all children
            for child in tree.get_children(item):
                search_tree(tree, child, search_text, found_items)

        def perform_search():
            search_text = search_entry.get()
            if not search_text:
                return
            
            # Clear previous highlights
            clear_highlights(tree)
            
            # Configure the search result highlight style
            tree.tag_configure('search_result', background='yellow')
            
            # Collapse all nodes first
            for item in tree.get_children():
                collapse_all_nodes(tree, item)
            
            # Perform search
            found_items = []
            for item in tree.get_children():
                search_tree(tree, item, search_text, found_items)
            
            # Expand paths to found items
            for item in found_items:
                # Expand all parent nodes
                parent = tree.parent(item)
                while parent:
                    tree.item(parent, open=True)
                    parent = tree.parent(parent)
            
            if found_items:
                # Select and focus on the first found item
                tree.selection_set(found_items[0])
                tree.see(found_items[0])
                messagebox.showinfo("Search Results", f"Found {len(found_items)} matches.")
            else:
                messagebox.showinfo("Search Results", "No matches found.")










    def show_sql_popup(self, tree, event):  # Change coordinates to event
        # Get item at coordinates
        item = tree.identify_row(event.y)
        if item:
            # Get values from the item
            values = tree.item(item)['values']
            if values and len(values) > 2:
                if  len(values) > 3:
                    sql_text = values[3]  # Get SQL text from third column
                    content = values[2]
                else:
                    sql_text=values[2]

                # Create popup window
                popup = tk.Toplevel(self)
                popup.title("Text Values")
                popup.geometry("800x400")
                text_widget = tk.Text(popup, wrap=tk.WORD)
                text_widget.pack(fill=tk.BOTH, expand=True)
                
                # Add scrollbars
                vsb = ttk.Scrollbar(popup, orient="vertical", command=text_widget.yview)
                hsb = ttk.Scrollbar(popup, orient="horizontal", command=text_widget.xview)
                text_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
                
                vsb.pack(side=tk.RIGHT, fill=tk.Y)
                hsb.pack(side=tk.BOTTOM, fill=tk.X)
                if sql_text:
                    text_widget.insert(tk.END, sql_text)
                elif content:
                    text_widget.insert(tk.END, content)

                text_widget.config(state='disabled')  # Make it read-only

#-------------------------------------------------------------------------------------------------------------



    def clear_text(self):
        self.ask_rows_text.delete("1.0", tk.END)

    def clear_text_log(self):
        self.selected_rows_text.delete("1.0", tk.END)



    def Ask_SiemensGPT(self):

        selected_rows_text = self.selected_rows_text.get("1.0", tk.END).strip()
        ask_rows_text = self.ask_rows_text.get("1.0", tk.END).strip()

        if self.selected_rows_text and ask_rows_text:
            self.ask_rows_text.tag_configure("green", foreground="green")
            self.ask_rows_text.insert(tk.END,("\n"+SiemensGPT(selected_rows_text, ask_rows_text, api_key)),"green")
            self.ask_rows_text.insert(tk.END,"\n" )
        else:
            if not selected_rows_text:
                messagebox.showerror("Please Select The Log Rows To Be Analyzed ")
            if not ask_rows_text:
               messagebox.showerror("Please Make A Question")


    
###############################################################################################################

    async def create_xml_file(self, xml_content_list, filename):
        filename = filename.split('.')[0]
        
        if  os.path.isdir(filename):
            os.chdir(filename)
        else:
            os.makedirs(filename)
            os.chdir(filename)

        if xml_content_list:
            try:
                # Original XML creation logic
                root = ET.fromstring(xml_content_list)
                tree = ET.ElementTree(root)
                
                xml_str = ET.tostring(root, encoding='unicode')
                dom = minidom.parseString(xml_str)
                pretty_xml = dom.toprettyxml(indent="  ")
                pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
                
                with open(f"{filename}.xml", "w", encoding="utf-8") as f:
                    f.write(pretty_xml)

                def extract_timing_info(node):
                    start_time = node.find('./__startTime')
                    end_time = node.find('./__endTime')
                    
                    if start_time is not None and end_time is not None:
                        try:
                            start_time_str = start_time.text.strip()
                            end_time_str = end_time.text.strip()
                            start = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M:%S.%f')
                            end = datetime.strptime(end_time_str, '%Y/%m/%d %H:%M:%S.%f')
                            delta = end - start
                            return {
                                'start_time': start_time_str,
                                'end_time': end_time_str,
                                'delta_time_ms': delta.total_seconds() * 1000
                            }
                        except ValueError as e:
                            messagebox.showerror(f"DateTime parsing error: {e}")
                    return None

                def process_node(node, level=0):
                    node_data = {
                        'node_type': node.tag,
                        'level': level,
                        'rank': None,  # Default rank is None
                        'attributes': dict(node.attrib) if node.attrib else {},
                        'subnodes': []
                    }
                    
                    timing = extract_timing_info(node)
                    if timing:
                        node_data.update(timing)
                    
                    if node.text and node.text.strip():
                        node_data['text'] = node.text.strip()

                    # Process children
                    children_at_level = []
                    for child in node:
                        child_data = process_node(child, level + 1)
                        if child_data:
                            children_at_level.append(child_data)
                            node_data['subnodes'].append(child_data)

                    # Sort and rank children at this level if they have timing information
                    if children_at_level:
                        # Filter children with timing information
                        timed_children = [c for c in children_at_level if 'delta_time_ms' in c]
                        if timed_children:
                            # Sort by duration
                            timed_children.sort(key=lambda x: x['delta_time_ms'], reverse=True)
                            
                            # Calculate total time for this level
                            total_level_time = sum(c['delta_time_ms'] for c in timed_children)
                            
                            if total_level_time > 0:  # Only process if there's actual timing data
                                # Assign ranks to top 3
                                for i, child in enumerate(timed_children[:3]):
                                    child['rank'] = i + 1
                                    child['is_top_three'] = True
                                    child['percentage_of_level'] = (child['delta_time_ms'] / total_level_time * 100)

                    return node_data

                # Process the entire tree
                tree_data = process_node(root)

                # Create final JSON structure
                json_data = {
                    'analysis_timestamp': datetime.now().isoformat(),
                    'source_file': f"{filename}.xml",
                    'tree_structure': tree_data
                }

                # Write JSON file
                json_filename = f"{filename}_tree_analysis.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, default=str)

            except ET.ParseError as e:
                messagebox.showerror(f"XML parsing error: {e}")
            except Exception as e:
                messagebox.showerror(f"Error processing files: {e}")
                
                raise  # Add this to see the full error traceback

    def start_async_processing(self):
        """Start async XML file creation in background"""
        def async_worker():
            async def create_xml_files():
                try:
                    await self.create_xml_file(''.join(self.response),self.file)
                except Exception as e:
                    messagebox.showerror(f"Error in XML file creation: {e}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(create_xml_files())
            finally:
                loop.close()

        #Start processing in background thread
        self.processing_thread = threading.Thread(target=async_worker, daemon=True)
        self.processing_thread.start()
    




    def parse_log(self, log_file, file):
        # Pre-compile patterns
        TIMESTAMP_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")
        TIMESTAMP_AND_TOKEN_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+")
        DEPTH_PATTERN = re.compile(r"Depth: (\d+)")
        LEAVING_PATTERN = re.compile(r"Leaving Depth")
        
        # Use deque for better performance with stack operations
        stack = deque()
        parent_map = {}
        node_values = {}  # Store node values in memory
        self.refference=["0000-00-00 00:00:00.000000"]*5
        self.ref_line=[""]*5
        self.delta=[]
        # Initialize QApplication if needed
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # Create and configure progress dialog
        progress = QProgressDialog(
            "Processing log lines...",
            "Cancel",
            0,
            100,
            None,
            Qt.WindowType.WindowStaysOnTopHint
        )
        progress.setWindowTitle("Progress")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0) 
        progress.show()
        QApplication.processEvents()
        
        try:
            # Get log lines
            self.response, self.log_lines = read_lines_list_XML(log_file)
            total_lines = len(self.log_lines)
            progress.setMaximum(total_lines)
            
            # Initialize processing variables
            self.start_async_processing()
            self.previous_timestamp = None
            self.depth_start_time = defaultdict(datetime.now)
            self.depth_delta_times = defaultdict(datetime.now)
            self.current_transaction = []
            
            # Process lines with batch updates
            batch_size = 1000
            current_batch = []
            
            for index, line in enumerate(self.log_lines):
                if progress.wasCanceled():
                    break
                    
                # Process timestamp
                timestamp_match = TIMESTAMP_PATTERN.match(line)
                delta = ""
                cdo_delta = ""
                
                if timestamp_match:
                    current_timestamp = timestamp_match.group(1)
                    curr_dt = datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    if self.previous_timestamp:
                        prev_dt = datetime.strptime(self.previous_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                        delta = str(curr_dt - prev_dt)
                        if len(delta) >= 14:
                            delta = delta[:len(delta) - 3]
                        if delta > self.refference[0]:
                            self.refference[0]=delta
                            self.ref_line[0]=line
                        elif delta > self.refference[1]:
                            self.refference[1]=delta
                            self.ref_line[1]=line
                        elif delta > self.refference[2]:
                            self.refference[2]=delta
                            self.ref_line[2]=line
                        elif delta > self.refference[3]:
                            self.refference[3]=delta
                            self.ref_line[3]=line
                        elif delta > self.refference[4]:
                            self.refference[4]=delta
                            self.ref_line[4]=line
                        self.delta.append(delta)
                    self.previous_timestamp = current_timestamp
                else:
                    #current_timestamp = timestamp_match.group(1)
                    curr_dt = prev_dt
                    prev_dt = datetime.strptime(self.previous_timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    delta = str(curr_dt - prev_dt) #28/05
                    self.delta.append(delta)    #
                    self.previous_timestamp = current_timestamp#
                
                # Extract message
                message = TIMESTAMP_AND_TOKEN_PATTERN.sub("", line)
                display_message = f"{index + 1}:    " + message.strip()
                
                # Handle exceptions
                if "EXCEPTION" in line:
                    error = self.log_lines[index + 3]
                    self.after(0, lambda: tk.messagebox.showwarning(
                        "Warning", 
                        f"Exception found in file: {file}-> \n{error}"
                    ))
                
                # Handle transactions
                elif "starting transaction" in line:
                    self.current_transaction = [display_message]
                elif self.current_transaction:
                    self.current_transaction.append(display_message)
                
                # Process depth information
                depth_match = DEPTH_PATTERN.search(line)
                leaving_match = LEAVING_PATTERN.search(line)
                
                if leaving_match:
                    # Create node for leaving entry regardless of stack state
                    parent = stack[-1] if stack else ""  # If stack is empty, parent will be ""
                    node_id = f"node_{index}"
                    node_values[node_id] = (display_message, delta, "")
                    current_batch.append(('insert', parent, "end", node_id, {
                        'values': (display_message, delta, ""),
                        'tags': ("orange_text",)
                    }))

                    # Handle stack updates if stack is not empty
                    if stack:
                        parent_id = stack[-1]
                        depth = len(stack) - 1
                        if depth in self.depth_start_time:
                            cdo_delta = str(curr_dt - self.depth_start_time[depth])
                            if parent_id in node_values:
                                values = node_values[parent_id]
                                current_batch.append(('item_update', parent_id, {
                                    'values': (values[0], values[1], cdo_delta),
                                    'tags': ("orange_text",)
                                }))
                
                elif depth_match:
                    depth = int(depth_match.group(1))
                    self.depth_start_time[depth] = curr_dt
                    
                    # Update stack
                    while len(stack) > depth:
                        popped_node = stack.pop()
                        if popped_node in self.depth_delta_times:
                            cdo_delta = str(curr_dt - self.depth_delta_times[popped_node])
                            if len(cdo_delta) >= 14:
                                cdo_delta = cdo_delta[:len(cdo_delta) - 3]
                            if popped_node in node_values:
                                values = node_values[popped_node]
                                current_batch.append(('item_update', popped_node, {
                                    'values': (values[0], values[1], cdo_delta),
                                    'tags': ("green_text",)
                                }))
                    
                    # Create new node
                    parent = stack[-1] if stack else ""
                    node_id = f"node_{index}"
                    node_values[node_id] = (display_message, delta, "")
                    current_batch.append(('insert', parent, "end", node_id, {
                        'values': (display_message, delta, ""),
                        'tags': ("green_text",)
                    }))
                    
                    stack.append(node_id)
                    parent_map[depth] = node_id
                    self.depth_delta_times[node_id] = curr_dt
                 
                
                else:
                    if self.current_transaction:
                        parent = stack[-1] if stack else ""
                        node_id = f"trans_{index}"
                        node_values[node_id] = (display_message, delta, "")
                        current_batch.append(('insert', parent, "end", node_id, {
                            'values': (display_message, delta, ""),
                            'tags': (f"line_{index}",)
                        }))
                
                # Batch processing
                if len(current_batch) >= batch_size:
                    self._process_batch(current_batch)
                    current_batch = []
                
                # Update progress
                progress.setValue(index + 1)
                QApplication.processEvents()
                
                # Periodic UI updates
                if index % batch_size == 0:
                    self.update_idletasks()
            
            # Process remaining batch items
            if current_batch:
                self._process_batch(current_batch)
            
            # Update text area efficiently
            self._update_text_area()
            
        finally:
            progress.close()
            if 'app' in locals():
                app.quit()
        

    def top_5_window(self):
        popup = tk.Toplevel()
        popup.title(f"Line Refference of {file_name}")
        popup.geometry("800x400")
        text_widget = tk.Text(popup, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(popup, orient="vertical", command=text_widget.yview)
        hsb = ttk.Scrollbar(popup, orient="horizontal", command=text_widget.xview)
        text_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        for j in range(0,5):

            text_widget.insert(tk.END, f"{self.ref_line[j]} \n time: {self.refference[j]}\n\n" )
    
    
        text_widget.config(state='disabled')  # Make it read-only


    def _process_batch(self, batch):
        """Helper method to process batch updates to the tree"""
        try:
            for operation in batch:
                if operation[0] == 'insert':
                    _, parent, position, node_id, properties = operation
                    self.tree.insert(parent, position, iid=node_id, **properties)
                elif operation[0] == 'item_update':
                    _, node_id, properties = operation
                    try:
                        self.tree.item(node_id, **properties)
                    except tk.TclError:
                        pass  # Skip if item not found
        except Exception as e:
            messagebox.showinfo("Error", f"Error processing batch: {str(e)}")


    def _update_text_area(self):
        """Helper method to efficiently update the text area"""
        try:
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", tk.END)

            self.log_lines_compare = self.log_lines 

            # ✅ Update self.log_lines here (adding line numbers once)
            self.log_lines = [f"{i + 1}: {line}" for i, line in enumerate(self.log_lines)]

            # Configure tags only once
            tag_configs = {
                "line_number": {"foreground": "purple"},
                "depth_entry": {"foreground": "green"},
                "leaving_depth": {"foreground": "#FF8000"},
                "highlight": {"background": "yellow"},
            }
            for tag, options in tag_configs.items():
                self.log_text.tag_configure(tag, **options)

            # Insert all text at once
            insert_text = "\n".join(self.log_lines) + "\n"
            self.log_text.insert(tk.END, insert_text)

            # Now tag line numbers and entries
            for i, line in enumerate(self.log_lines):
                line_start = f"{i + 1}.0"
                line_num_len = len(f"{i + 1}: ")
                num_end = f"{i + 1}.{line_num_len}"

                self.log_text.tag_add("line_number", line_start, num_end)

                content_start = f"{i + 1}.{line_num_len}"

                if "Depth:" in line and "Leaving" not in line:
                    self.log_text.tag_add("depth_entry", content_start, f"{i + 1}.end")
                elif "Leaving Depth:" in line:
                    self.log_text.tag_add("leaving_depth", content_start, f"{i + 1}.end")

            self.log_text.see("1.0")
            self.log_text.config(state="disabled")  # Optional: make readonly

        except Exception as e:
            messagebox.showinfo("Error", f"Error updating text area: {str(e)}")



    def highlight_log_line(self, event):
        try:
            selected_item = self.tree.selection()[0]
            tags = self.tree.item(selected_item, 'tags')

            # Find the tag that starts with "line_" to get the line number
            line_number = None
            for tag in tags:
                if tag.startswith("line_"):
                    line_number = int(tag.split("_")[1])
                    break

            if line_number is None:
                return

            # Clear previous highlights
            self.log_text.tag_remove("highlight", "1.0", tk.END)

            # Check if line number is valid
            if 0 <= line_number < len(self.log_lines):
                # Instead of reinserting all text, just add highlight tag
                start = f"{line_number + 1}.0"
                end = f"{line_number + 1}.end"
                self.log_text.tag_add("highlight", start, end)
                self.log_text.see(start)
            else:
                messagebox.showerror("Error", f"Invalid line number: {line_number}")
        except Exception as e:
            messagebox.showerror("Error", f"Error in highlighting: {e}")
################################################################################################################################################



CONFIG_FILE = "config.json"
DEFAULT_API_KEY = "SIAK-qFpdpe9lWgR6DKm60mbDjchce97f70a13"

def load_config():
    """Load stored config if it exists, otherwise return an empty dict."""
    if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save config to file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

 

if __name__ == "__main__":
    config = load_config()
    stored_api_key = config.get("default_api_key", None)

    root = tk.Tk()
    root.withdraw()  # Hide main window initially

    if not stored_api_key:
        user_api_key = simpledialog.askstring("API Key", "Enter API Key (leave blank for default):", parent=root)
        api_key = user_api_key if user_api_key else DEFAULT_API_KEY

        if user_api_key:
            save_as_default = tk.BooleanVar(value=False)
            check_window = tk.Toplevel(root)
            check_window.title("Save API Key")
            check_window.geometry("300x150")
            

            label = tk.Label(check_window, text="Save this API Key as default?")
            label.pack(pady=10)

            check_button = tk.Checkbutton(check_window, text="Save as default", variable=save_as_default)
            check_button.pack()

            def confirm():
                check_window.destroy()
                if save_as_default.get():
                    config["default_api_key"] = api_key
                    save_config(config)

            confirm_button = tk.Button(check_window, text="Confirm", command=confirm)
            confirm_button.pack(pady=10)

            check_window.wait_window()
    else:
        api_key = stored_api_key

   
    while True:
        file_path = filedialog.askopenfilename(
            title="Select Log File",
            filetypes=[
                ("Log files", "*.log"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            messagebox.showerror("No file selected. Exiting...")
            break

        path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        

        log_tree_view = LogTreeView(file_path, file_name)
        log_tree_view.mainloop() 
        
        # Ask if user wants to open another file

        sys.exit()