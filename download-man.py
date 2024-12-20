import re
import os
from typing import List, Tuple
import glob
import time
import shutil
import subprocess
import json

# Starting assumptions
# current directory will include a source file with all desired download links. This file will be manually created. File name must be links-main-XXXXX
# curent directory will include one and only file named download_information.json (This file can be created manually or with the parallel_download.py script)

def download_with_parallel(file_with_links):
    """ expects a file with download link(s) and uses GNU paralel to start downloads."""

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


def is_download_complete(file_path : str) -> Tuple[bool,str]:

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
    

def decrease_remaining_links_by1(file_path, key='number_of_remaining_links'):
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

def increase_auto_starts_by1(file_path, key='number_of_auto_starts'):
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


def remove_link_with_filename(filename : str, links_file_path = 'links-main'):

    """ASSUMES that the input file for the links will start with links-main-XXXX"""

    #this can be outside so doesn't run everytime. Download link file will the the same. Will updates break it?

    links_file_pattern = f"{links_file_path}*"
    links_file_path_search = glob.glob(os.path.join(os.curdir,links_file_pattern))
    links_file_path = links_file_path_search[0]

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
            decrease_remaining_links_by1("download_information.json")

    except FileNotFoundError:
        print(f"The file {links_file_path} does not exist.")
    except PermissionError:
        print(f"Permission denied: Unable to write to {links_file_path}.")
    except Exception as e:
        print(f"An error occurred: {e}")




def adjust_downloaded(log_file_path,file_name):
    """Adjusts the download information file, log files and the actual file after a download is completed."""

    remove_log_file(log_file_path)
    remove_link_with_filename(file_name)
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
        file_path = os.path.join(current_directory, file_name)
        print(file_path,"from while") 
        result =  is_download_complete(file_path)
        if result[0] == True: #if download is successfull
            adjust_downloaded(file_path,result[1])
            
# after adjusments are done, this line below will decide if download needs to be restarted.
if get_remaining_download_links() > 0 and not active_download:
    print("should not see this")

    links_file_pattern = "links-main-*"
    links_file_path_search = glob.glob(os.path.join(os.curdir,links_file_pattern))
    links_file_path = links_file_path_search[0]
    increase_auto_starts_by1("download_information.json") #if this line was after the download_function_call ? 
    print('download auto restarted')
    download_with_parallel(links_file_path)
elif get_remaining_download_links() == 0 and not active_download:
    print("Download is complete")



# later concerns below for just note taking purposes. Won't effect the script.

def find_phrase_in_log(file_path, phrase):
    try:
        with open(file_path, 'r') as file:
            log_contents = file.read()
            if re.search(phrase, log_contents):
                return True
            else:
                return False
    except FileNotFoundError:
        print("The specified file was not found.")
        return False
    

def search_log(file_name : str): 
    # Construct the log file pattern
    log_file_pattern = f"*{file_name}.log" 
    log_file_paths = glob.glob(os.path.join(os.curdir, log_file_pattern))
    if not log_file_paths: 
        print(f"No log files found matching pattern: {log_file_pattern}") 
        return None 
    # Assuming there's only one log file matching the pattern 
    log_file_path = log_file_paths[0]
    print(log_file_paths[0],"from search log")
    return log_file_path


#download did not start
# if the log file doesn't have saved to ... there is a problem
# Make sure about other error messages saving to (Maybe out of disk space etc.)
# wget tried and gave up
# look for the string 
#grab the file name
#difference between one link vs multiple links 


