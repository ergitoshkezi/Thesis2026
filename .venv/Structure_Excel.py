from nltk.tokenize import word_tokenize
from datetime import datetime
from bs4 import BeautifulSoup
import sys
import chardet
import xml.etree.ElementTree as ET
import os
import pandas as pd
import re
from pathlib import Path
import mmap
from colorama import Fore, Style
from tkinter import Tk
from tkinter.filedialog import askdirectory
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QProgressDialog, QApplication


# Change the recursion limit
#sys.setrecursionlimit(50000000)
#print(sys.getrecursionlimit())



def check_pattern(input_string):
    pattern = r'\d{14}\.\d{3}'  # Define the pattern using regex
    if re.fullmatch(pattern, input_string):
        return True
    else:
        return False



def thread(token):
        
    overview.append(token[1])

    already_there=False

    for item in Threads:
        if token[1] == item :  #posizione 1 c'è  il thread code
            already_there=True

    if already_there == False:
         Threads.append(token[1])


    
                    


def delta_txn():
    return (finish_txn-start_txn)





def time_array(start,end,index_position,tip):
  
    index.append(index_position)   




def start_time(start):

    global start_txn
    start_txn=start
    





def start_counter_chart(value):
    global counterchart
    counterchart=value





def counter_chart_update(value):
     global counterchart
     counterchart +=value

    



def finish_time(finish):

    global finish_txn
    finish_txn=finish
   




def modify_Response(val):
    global Response
    Response=val






def modify_Request(val):
    global Request
    Request=val


            



def convert_to_string(char_list):
    result = ""
    for char in char_list:
        result += char
    return result





def print_List_xml_Response(doc):
    current_directory = os.getcwd()
    tree = ET.XML(BeautifulSoup(convert_to_string(doc), "xml").prettify())
    if not os.path.exists(IR):
        os.makedirs(IR)
    os.chdir(IR)
        # Save the XML tree to a file (e.g., 'output.xml')
    with open('IR_'+ IR +"_Response_Document.xml", "w") as f:
      f.write(ET.tostring(tree, encoding='UTF-8').decode('UTF-8'))
    os.chdir(current_directory)








def print_List_xml(doc):
    current_directory = os.getcwd()
    # Prettify the XML
    tree = ET.XML(BeautifulSoup(convert_to_string(doc), "xml").prettify())
    if not os.path.exists(IR):
        os.makedirs(IR)
    os.chdir(IR)
    # Save the XML tree to a file (e.g., 'IR_'+ IR +"_Request_Document.xml")
    with open('IR_'+ IR +"_Request_Document.xml", "w") as f:
        f.write(ET.tostring(tree, encoding="UTF-8").decode('utf-8'))
    os.chdir(current_directory)








def is_number(string):
    try:
        int_value = int(string)  # Check if it's a valid integer
        if len(int_value) == 18:
            return True
        else:
            return False
        
    except ValueError:
        try:
            float_value = float(string)  # Check if it's a valid float
            if len(string)== 18:
                return True
            else:
                return False
            
        except ValueError:
            return False






def tokenize(text):
    tokens = word_tokenize(text)
    return tokens






def start(token,i):

    if(is_number(token[0])):

        dt = datetime.strptime(token[0], "%Y%m%d%H%M%S.%f")
        date_object=dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        print("Transaction Started at :")
        print(date_object)
        if date_object:
            overview.append(date_object)
        else:
            overview.append("Null")
        start_time(dt)

        print("The Virtual Page involved is : " + token[i] + "  The User is :  "+ token[i+2])
        overview.append(token[i])
        overview.append(token[i+2])
    else:
        overview.append("Null")
        overview.append("Null")
        






def end(token):

    if(is_number(token[0])):
       
        
        dt = datetime.strptime(token[0], "%Y%m%d%H%M%S.%f")
        date_object=dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print("Transaction Ended at :")
        print(date_object)
        overview.append(date_object)
        finish_time(dt)
    else:
        overview.append("Null")
        
   


def xml_Request_funzionante(tokens, position, row_index, document_xml):
    while row_index < len(lines_list):
        if not is_number(tokens[position]):
            document_xml.extend(tokens[position:])
            row_index += 1
            tokens = tokenize(lines_list[row_index])
            position = 0
        else:
            print_List_xml(document_xml)
            return row_index - 1



 # Only return lines that are not empty



def read_lines_list(filename):
    file_size = Path(filename).stat().st_size
    
    # For very small files, use direct reading
    if file_size < 1024 * 1024:  # 1MB threshold
        with open(filename, 'rb') as infile:
            rawdata = infile.read()
            encoding = chardet.detect(rawdata)['encoding']
            return [line.strip() for line in 
                   rawdata.decode(encoding).splitlines() if line.strip()]
    
    # For larger files, use memory mapping
    with open(filename, 'rb') as infile:
        # Sample first 1024 bytes for encoding detection
        sample = infile.read(1024)
        encoding = chardet.detect(sample)['encoding']
        
        # Reset file pointer
        infile.seek(0)
        
        # Use memory mapping for efficient reading
        with mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return [line.strip() for line in 
                   mm.read().decode(encoding).splitlines() if line.strip()]





def Xml_Response(tokens_of_row,position,row_index_log,document_xml):
    
    for i in range(position, len(tokens_of_row)):
        # print(line_gap.split('\t')[0])
        if row_index_log <= len(lines_list)-1:
            document_xml.extend(tokens_of_row[i])
            if(i == len(tokens_of_row)-1):
                if(row_index_log < len(lines_list)-1):
                    Tokenized_row=tokenize(lines_list[row_index_log+1]) 
                    Xml_Response(Tokenized_row,0,row_index_log+1,document_xml)
                elif row_index_log == len(lines_list)-1:
                        
                    print_List_xml_Response(document_xml)

                    return row_index_log 
                        #return Xml_Response(Tokenized_row,0,row_index_log+1,document_xml)       
            
       





def Time_stamp(token):
    #codifica del token con lo standart time 
    # r
     if(is_number(token)):

        dt = datetime.strptime(token, "%Y%m%d%H%M%S.%f")

        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]





def time_chart(token):

    dt = datetime.strptime(token, "%Y%m%d%H%M%S.%f")

    return dt






def gap_time(token,index):
     
    
    global line_one
    global line_two
    global Gap
    global line_gap


    if(check_pattern(token)):

        dt=datetime.strptime(token, "%Y%m%d%H%M%S.%f")
        if line_one=="0000-00-00 00:00:00":
            line_one=dt
        else:
            if line_two=="0000-00-00 00:00:00":
                line_two=dt

        # Convert dt to a string with the desired format
        if line_one != "0000-00-00 00:00:00" and line_two != "0000-00-00 00:00:00":
           
            g=line_two-line_one
            line_one=line_two
            line_two="0000-00-00 00:00:00"

            if str(g) > str(Gap):
                Gap=g
                line_gap=convert_to_string(lines_list[index])
        




def Analyse(token_of_row,row_index_log):
    
    global ERROR
    global Description
    global Total_CDO

    for i, item in enumerate(token_of_row):       
        
        gap_time(token_of_row[0],row_index_log)
        

        if (item == '<' and Request==True ):  #This means that This is the start of Request Document xml 
            if token_of_row[i+1] == '?' :
                modify_Request(False)
                return xml_Request_funzionante(token_of_row,i,row_index_log ,document_xml = [])
                

        elif item == 'starting':
            thread(token_of_row)
            if token_of_row[i+1] =='transaction' :
                start(token_of_row,i+2)
                return row_index_log


        elif item == 'Depth' : #Log should start with Depth first and Leaving after 
           if [token_of_row[i-1]] != 'Leaving':            
            Total_CDO += 1



        elif item == 'Response' and  token_of_row[i+1] == 'Document' :
            modify_Response(True)
            return row_index_log
        

        elif  item == 'Request' and token_of_row[i+1] == 'Document'  :
            modify_Request(True)
            return row_index_log


        elif (Response==True and  item == '<'   ) : # this means Response Starts
            if token_of_row[i+1] == '?':
                modify_Response(False)
             
                return row_index_log
        

        elif item == "deleting"  and  token_of_row[i+1]=="transaction"  : # nel caso non ci fosse Request document            
            end(token_of_row)
            print(" The Transaction duration was :")
            print(delta_txn())
            overview.append(str(delta_txn()))
            Time_podium.append(str(delta_txn())+","+IR)
            return len(lines_list)-1
        
        elif item == 'EXCEPTION' or item =='csiXMLEXception' or item =='csiException':
            ERROR=True
            
        elif item == 'Description':
            Error_Description(token_of_row)
            

            

def Error_Description(row):
    global Description
    
    for i, item in enumerate(row):
        if item == 'Description':
            Description = " ".join(row[i:])
            break



def optimize_overview():
   

    if len(overview) < 12:
        for i in range (len(overview), 12):
            overview.append("Null") 
    else:
        del overview[12:]  
        
        # Delete elements starting from the 13th index onwards



def append_to_excel():
   

    #optimize_overview()


    file_path = '_Overview.xlsx'
    # Check if the Excel file exists
    file_exists = os.path.exists(file_path)

    if file_exists:
        # Load existing DataFrame from Excel file
        df_existing = pd.read_excel(file_path)
    else:
        # Create a new DataFrame if the file does not exist
        df_existing = pd.DataFrame(columns=['File Name','ProcessID', 'ThreadID', 'Start Time', 'Virtual Page', 'User', 'End Time', 'Duration of TXN', 'Exception', 'Biggest Gap', 'Line Refference ','Total CDO'])

    # Append new data to the existing DataFrame
    df_new = pd.DataFrame([overview], columns=['File Name', 'ProcessID', 'ThreadID', 'Start Time', 'Virtual Page', 'User', 'End Time', 'Duration of TXN', 'Exception', 'Biggest Gap','Line Refference ','Total CDO'])
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)

    # Write the updated DataFrame to the Excel file
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
        df_updated.to_excel(writer, index=False)
       

def convert_time_of_reff_line(line):
    parts = re.split(r'(\s+)', line, maxsplit=1)  # Split only at the first space/tab
    if parts:
        t = Time_stamp(parts[0])  # Convert only the first element
        parts[0] = str(t)  # Replace it with the timestamp result
    return ''.join(parts)




# MAIN:

def main():
    #init()  # Initialize colorama

    global IR, lines_list, path, index, Threads, error_line_number, ERROR, Description, Time_podium, Total_CDO, Gap, line_one, line_two, line_gap, Dir, file_counter, overview, ProcessID

    index = [[]]
    Threads = []
    error_line_number = 0
    ERROR = False
    Description = ""
    Time_podium = []
    Gap = "0000-00-00 00:00:00"
    line_one = "0000-00-00 00:00:00"
    line_two = "0000-00-00 00:00:00"
    line_gap = ""
    Dir = "_No_Error"
    file_counter = 0
    ProcessID = ""
    overview = []
    Total_CDO = 0
    c=0

    # Initialize a Tkinter window and withdraw it so it doesn't appear
    root = Tk()
    root.withdraw()

    #print(f"{Fore.YELLOW}Please Select Folder Path:{Style.RESET_ALL}")

    # Open a folder selector dialog
    path = askdirectory(title="Select Folder")

    # Strip whitespace and proceed if a valid directory is selected
    path = path.strip()

    if not path:
        print(f"{Fore.RED}No folder was selected. Exiting...{Style.RESET_ALL}")
        return

    os.chdir(path)
    for file in os.listdir(path):
        if file.endswith((".txt", ".log")):
            c+=1
    
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
    progress.setMaximum(2*c)
    QApplication.processEvents()
    contatore=0
    for file in os.listdir(path):
        if file.endswith((".txt", ".log")):
            contatore+=1
            try:
                ERROR = False
                file_path = os.path.join(path, file)
                lines_list = read_lines_list(file_path)

                modify_Response(False)
                modify_Request(False)
                start_counter_chart(0)
                i = 0
                file_counter += 1

                if len(os.path.basename(file_path).split("_")) > 2:
                    ProcessID = os.path.basename(file_path).split("_")[2]
                else:
                    ProcessID = "Null"

                IR = os.path.basename(file_path)#.split('.')[0]

                print(f"{Fore.BLUE}{str(file_counter)}):{Style.RESET_ALL}")
                print(f"{Fore.GREEN}File name:{Style.RESET_ALL}")
                print(IR)

                if IR:
                    overview.append(IR)
                    IR = os.path.basename(file_path).split('.')[0]

                else:
                    overview.append("Null")
                if ProcessID:
                    overview.append(ProcessID)
                else:
                    overview.append("Null")

                try:
                    while i <= len(lines_list) - 1:
                        Tokenized_row = tokenize(lines_list[i])
                        value = Analyse(Tokenized_row, i)

                        if value is not None:
                            i = value
                        i += 1
                        progress.setValue(contatore)
                except Exception as e:
                    print(f"{Fore.RED}Error occurred with {IR}, {e}{Style.RESET_ALL}")

                if ERROR:
                    overview.append(str(convert_to_string(Description)))
                else:
                    overview.append("Null")

                if str(Gap):
                    overview.append(str(Gap))
                else:
                    overview.append("Null")

                if line_gap:
                    overview.append(convert_time_of_reff_line(line_gap))
                else:
                    overview.append("Null")
                if Total_CDO:
                    overview.append(Total_CDO)
                else:
                    overview.append("Null")

                Gap = "0000-00-00 00:00:00"
                line_one = "0000-00-00 00:00:00"
                line_two = "0000-00-00 00:00:00"
                line_gap = ""
                Total_CDO = 0

                append_to_excel()
                overview.clear()
                print(f"{Fore.BLUE}******---------------------------------------------------END---------------------------------------------------******{Style.RESET_ALL}")
                
                progress.setValue(contatore)
                QApplication.processEvents()  # Keep the GUI responsive
                #self.update_idletasks()      # Keep Tkinter GUI responsive
                
            except Exception as e:
                overview.clear()
                print(f"{Fore.RED}Error occurred with {IR}, {e}{Style.RESET_ALL}")
                Gap = "0000-00-00 00:00:00"
                line_one = "0000-00-00 00:00:00"
                line_two = "0000-00-00 00:00:00"
                line_gap = ""
                Total_CDO = 0

    print(f"{Fore.GREEN}FINISHED:{Style.RESET_ALL}")
    print("\n")
    

if __name__ == '__main__':
    main()
#### Fine parser
##commando per creare .exe : python -m auto_py_to_exe