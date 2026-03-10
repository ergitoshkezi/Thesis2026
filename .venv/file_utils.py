"""
File Utilities — Log File Readers & Text Chunkers
====================================================

Functions for reading log files with automatic encoding detection
and splitting text into manageable chunks for LLM processing.

Author : Ergito Shkëzi
Project: Master's Thesis 2026
"""

# ──────────────────────────────────────────────────────────────────────
# Standard Library
# ──────────────────────────────────────────────────────────────────────
import re
from tkinter import messagebox

# ──────────────────────────────────────────────────────────────────────
# Third-Party Libraries
# ──────────────────────────────────────────────────────────────────────
import chardet
from nltk.tokenize import word_tokenize


# ══════════════════════════════════════════════════════════════════════
#  Text Splitting
# ══════════════════════════════════════════════════════════════════════


def split_text_no_overlap(text, max_tokens=7500):
    """Split *text* into chunks of at most *max_tokens* words (no overlap).

    Chunks are built back-to-front and then reversed so the natural
    reading order is preserved.
    """
    words = word_tokenize(text)
    chunks = []
    for i in range(len(words), 0, -max_tokens):
        start = max(i - max_tokens, 0)
        chunks.append(" ".join(words[start:i]))
    chunks.reverse()
    return chunks



def split_text_no_overlap_compare(text, max_tokens=7500):
    """Split *text* into forward-order chunks for comparison prompts."""
    if isinstance(text, list):
        text = ' '.join(text)

    words = word_tokenize(text)
    chunks = []
    for i in range(0, len(words), max_tokens):
        chunks.append(" ".join(words[i:i + max_tokens]))
    return chunks


# ══════════════════════════════════════════════════════════════════════
#  Log File Readers
# ══════════════════════════════════════════════════════════════════════


def read_lines_list_for_all(filename, search_term):
    """Read a log file and return lines matching *search_term* (for multi-file search)."""
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


def read_lines_list(filename):
    """Read a log file and return formatted transaction lines (for comparison)."""
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
    """Read a log file and return (Response_Document, formatted_lines) tuple.

    Separates XML response-document content from formatted transaction
    lines, used by the main log parser.
    """
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
