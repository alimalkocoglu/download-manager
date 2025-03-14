import re
import os
from typing import List, Tuple
import glob
import time
import shutil
import subprocess
import json

# Starting assumptions
# curent directory will include one and only file named download_information.json

def download_with_parallel(file_with_links):
    """ expects a file with download link(s) and uses GNU paralel to start downloads.Not recursive"""

    command = (
        f"cat {file_with_links} | "
        f"parallel 'filename=$(basename {{}}); "
        # each file being downloaded will have corresponding log files in the format of 'name_of_file.extension.log'
        f"logname=$filename.log; "
        f"torify wget -c --user-agent=\"Mozilla\" -a $logname {{}}'"
    )
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("Downloads initiated with torify wget.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def recursive_parallel_download(file_with_links):
    """To be used with file tree style recursive downloads."""
    command = (
        f"cat {file_with_links} | "
        f"parallel 'filename=$(basename {{}}); "
        f"logname=$filename.log; "
        #log files will be created for each download link not for each file Each files download log will in those link based log files.
        f"torify wget -c -r -np --user-agent=\"Mozilla\" -a $logname {{}}'"
    )
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("Downloads initiated with torify wget.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

def is_download_active(directory='.'):
    """ checks if any log file in the directory was recently updated which might indicate an ongoing download. """
    current_time = time.time()
    threshold_time = 10  # seconds

    for file_name in os.listdir(directory):
        if file_name.endswith('.log'):
            file_path = os.path.join(directory, file_name)
            file_mod_time = os.path.getmtime(file_path)
            if current_time - file_mod_time <= threshold_time:
                return True
    
    return False


def is_file_download_complete(file_path : str) -> Tuple[bool,str]:

    ''' Searches the given log file for the pattern "saved [n bytes / n bytes]"
        returns a tuple with the boolean value of download completion status and name of the file.
        Assumes that standart log file formatting was used from GNU wget as it uses the "saved [ n bytes / n bytes]" format.
    '''

    file_name =None
    is_downladed = False
    try:
        with open(file_path, 'r') as file:
            log_contents = file.read()
            pattern = r'\‘(.+)\’\s+saved\s+\[(\d+)/(\d+)\]'
            regex_match = re.search(pattern, log_contents)
            if regex_match is None:
                print('match is None')
                return [is_downladed,file_name]
            if regex_match.group(2) == regex_match.group(3):
                is_downladed = True
                file_name = regex_match.group(1)
                print("saved match found")
                return [is_downladed,file_name]
            else:
                return [is_downladed,file_name]
            
    except FileNotFoundError:
        print("The specified file was not found.")
        return [False,file_name]


def process_recursive_logs(logfile,link_file,base_link=None):

    # Regex pattern to match lines starting with "Downloaded"
    pattern = re.compile(r'^Downloaded:\s\d+\sfiles,.*$',re.MULTILINE)
    
    # Read the contents of the links file
    with open(link_file, 'r') as lf:
        links = lf.readlines()
        #updated_links = links.copy()

    with open(logfile, 'r') as lf:
        log_content = lf.read()
                
        # Search for the pattern in the log file
        match = pattern.search(log_content)
        if match:
            link_to_remove = os.path.basename(logfile)
            link_to_remove = os.path.splitext(link_to_remove)[0]
            regex_pattern = re.compile(f"{base_link}{link_to_remove}/$")  # Match link_to_remove at the end of the string

            # Remove the link with the exact match from the links file content
            updated_links = [link for link in links if not regex_pattern.search(link)] 

            # Write the updated content back to the links file 
            with open(link_file, 'w') as lf:
                lf.writelines(updated_links) #link is removed from the download file.
                decrease_remaining_links_by1()
        else:
            return
    



def decrease_remaining_links_by1(file_path='download_information.json', key='number_of_remaining_links'):
    """ looks at the download_information.json file and adjusts the key:value pair"""

    # Check if the JSON file exists
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    # Load existing data
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Update the specific key with the new value
    if key in data:
        data[key] = data[key] - 1
    else:
        print(f"Key '{key}' not found in the JSON file.")
        return

    # Save modified data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def get_download_links(file_path='./download_information.json', key='download_links'):  #HARDCODED TARGET VARIABLE NAME
    """ Assumes that download_information.json file exists and returns the download link file path"""

    # Check if the JSON file exists
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    # Load existing download_information_file
    with open(file_path, 'r') as file:
        data = json.load(file)

    if key in data:
        return data[key]
    else:
        print(f"Key '{key}' not found in the JSON file.")
        return

def get_url(file_path='./download_information.json', key='Recursive_url'):  #HARDCODED TARGET VARIABLE NAME
    """ Assumes that download_information.json file exists and returns the download link file path"""

    # Check if the JSON file exists
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    # Load existing download_information_file
    with open(file_path, 'r') as file:
        data = json.load(file)

    if key in data:
        return data[key]
    else:
        print(f"Key '{key}' not found in the JSON file.")
        return

def is_recursive(file_path='./download_information.json', key='Recursive_file_structure'):  #HARDCODED TARGET VARIABLE NAME
    """ Assumes that download_information.json file exists and returns the download link file path"""

    # Check if the JSON file exists
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    # Load existing download_information_file
    with open(file_path, 'r') as file:
        data = json.load(file)

    if key in data:
        return data[key]
    else:
        print(f"Key '{key}' not found in the JSON file.")
        return

def increase_auto_starts_by1(file_path="download_information.json", key='number_of_auto_starts'):
    """ looks at the download_information.json file and adjusts the key:value pair"""

    # Check if the JSON file exists
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    # Load existing data
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Update the specific key with the new value
    if key in data:
        data[key] = data[key] + 1
    else:
        print(f"Key '{key}' not found in the JSON file.")
        return

    # Save modified data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    

def get_remaining_download_links (file_path="./download_information.json"):
    #HARDCODED for file path. Assuming this file is already created in the current directory script is being ran.
    """searches the download_information.json file -- assumes files exists and it's an integer key:pair value and only one json file exists."""

    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return

    # Load existing data
    with open(file_path, 'r') as file:
        data = json.load(file)

    return int(data["number_of_remaining_links"])


def remove_log_file(file_path):
    """removes a log file when download is completed.""" 
    
    try: 
        os.remove(file_path)
    except FileNotFoundError: 
        print(f"The file {file_path} does not exist.") 
    except PermissionError: 
        print(f"Permission denied: Unable to delete {file_path}.") 
    except Exception as e:
        print(f"Error: {e}")


def move_to_complete_downloads(file_path):
    """creates a dir for complete downloads and moves the files as needed."""
    # Define the target directory
    target_dir = os.path.join(os.path.dirname(file_path), 'complete_downloads')

    # Create the target directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Define the target file path
    target_file_path = os.path.join(target_dir, os.path.basename(file_path))

    # Move the file to the target directory
    shutil.move(file_path, target_file_path)

    return


def remove_link_with_filename(filename : str, links_file_path):

    """ removes the completed link from the links source file."""

    if not links_file_path: 
        print(f"No main link file found matching pattern: {links_file_path}") 
        return None

    try:
        with open(links_file_path, 'r') as file:
            log_contents = file.read()

        # Create a pattern to match lines containing the filename
        pattern = rf'.*{re.escape(filename)}.*\n'
        updated_log_contents = re.sub(pattern, '', log_contents)

        with open(links_file_path, 'w') as file:
            file.write(updated_log_contents)
            decrease_remaining_links_by1()

    except FileNotFoundError:
        print(f"The file {links_file_path} does not exist.")
    except PermissionError:
        print(f"Permission denied: Unable to write to {links_file_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")




def adjust_downloaded(log_file_path,file_name):
    """Adjusts the download information file, log files and the actual file after a download is completed."""

    remove_log_file(log_file_path)
    remove_link_with_filename(file_name,get_download_links())
    move_to_complete_downloads(file_name)

    return None 

current_directory = os.getcwd()
active_download = is_download_active()


for file_name in os.listdir(current_directory):
    
    if active_download:
        #if an active download is going on script won't do anything.
        print("active download")
        break

    if file_name.endswith('.log'): 
        file_path = os.path.join(current_directory, file_name) #logfile
        if is_recursive():
            process_recursive_logs(file_path,get_download_links(),get_url())
        else:
            result =  is_file_download_complete(file_path)
            if result[0] == True: #if download is successfull
                adjust_downloaded(file_path,result[1],)
            
# after adjusments are done, this line below will decide if download needs to be restarted if yes recursive or not.
if get_remaining_download_links() > 0 and not active_download: 
    links_file_pattern = get_download_links()
    increase_auto_starts_by1() #if this line was after the download_function_call ? 
    print('download auto restarting')
    if is_recursive():
        recursive_parallel_download(links_file_pattern)
    else:
        download_with_parallel(links_file_pattern)
elif get_remaining_download_links() == 0 and not active_download:
    print("Download is complete")
