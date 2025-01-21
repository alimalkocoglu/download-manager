import subprocess
import os
import json
import argparse
import re
import sys

# with the extract function maybe check if space is available
# If password is correct or not
# write these warnings to the download information json.

#optional file password
#change the download_information.json file according to these files.

def parallel_download(file_with_links):
    """To be used with non recursive dowloads."""
    command = (
        f"cat {file_with_links} | "
        f"parallel 'filename=$(basename {{}}); "
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

def create_initial_json(download_links,password,recursive_download, json_file='download_information.json',Recursive_url = None):

    # Count the number of links in the download file
    with open(download_links, 'r') as f:
        total_links = len(f.readlines())

    # Create initial JSON data based on password protection

    data = {
            "number_of_auto_starts": 0,
            "number_of_total_links": total_links,
            "number_of_remaining_links": total_links,
            "file_password": password,
            "files_extracted": False,
            "download_links": download_links,
            "Recursive_file_structure":recursive_download,
            "Recursive_url": Recursive_url
    }

    # Write the initial data to the JSON file
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def extract_links(url, output_file=None):

    """ receives an url, gets the links on that page, creates a file and returns the created files' name"""
    # Fetch the HTML content of the given url
    wget_command = f'torify wget -qO- --user-agent="Mozilla" {url}'
    
    # Extract links, exclude parent directory and symbolic links
    grep_command = "grep -oP '(?<=href=\")[^\\\"]*(?=\")' | grep -v '^#' | grep -v '^../$'"
    
    # Combine wget and grep commands
    combined_command = f"{wget_command} | {grep_command}"
    
    # Execute the command
    process = subprocess.Popen(combined_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    
    if process.returncode == 0:
        # Determine the output file name
        if not output_file:
            output_file = f"dowload_links_for_{os.path.basename(os.getcwd())}.txt"
        
        # Write the links to the file with the base link prepended
        with open(output_file, 'w') as f:
            for link in output.decode().splitlines():
                f.write(f"{url}{link}\n")
        
        print(f"Links saved to {output_file}")
        return output_file
    else:
        print(f"Error: {error.decode()}")


def main():

    parser = argparse.ArgumentParser(
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                    description="""

                    Pass a download url using -sl or --singlelink options followed by the url.

                    If you want rescursive download option use the -r or --recursive   (can be used with -sl or --singlelink or -lf , --linkfile)

                    When called with the option -lf or --linkfile  an input file including multiple links can be passed
                    
                    After script is called a file with download links will be created using the directory name. If you want to override this naming use -clfname or --customlinkfilename followed by the desired file name.
                    
                    Considering you have space in your environment and have the correct software installed this script can also extract your files when the download is completed.An optional password can be supplied. !!Feature update!!
                    """,
                    epilog='Help was NOT so HELPFUL? Send your feedback or question via Slack to alimalkocoglu')

    #parser.add_argument(-link-file)
    parser.add_argument("-pwd","--password", help="will be used to extract the files when the download is completed. -- This iteration does not have this feature.")
    parser.add_argument("-sl","--singlelink", help="This url will be crawled and links on the given url will be added to a file called download_links_for_DIRECTORY_NAME")
    parser.add_argument("-clfname","--customlinkfilename", help="If this option is chosen instead of the default download_links_for_DIRECTORY_NAME format will be overriden by the user input -- Follow linux naming conventions..")
    parser.add_argument("-lf","--linkfile", help="This will be the name of the file with links to pass to wget -- Follow linux naming conventions. ")
    parser.add_argument("-r","--recursive",action='store_true',help="For directory style links use this.")

    args = parser.parse_args()

    file_with_links = ''
    url = None

    if args.singlelink:
        if args.customlinkfilename:
            file_with_links = extract_links(args.singlelink,args.customlinkfilename)
            url = args.singlelink
        else:
            file_with_links = extract_links(args.singlelink)
    
    if args.linkfile:
        file_with_links = args.linkfile
    if not os.path.exists(file_with_links):
        print(f"Error: The file '{file_with_links}' does not exist.")
        sys.exit(1)
    
    json_file = "download_information.json"
    create_initial_json(file_with_links,args.password,args.recursive,json_file,url)

    #start downloads based on recursiveness or not. 
    if args.recursive:
        recursive_parallel_download(file_with_links)
    else:
        parallel_download(file_with_links)

if __name__ == "__main__":
    main()
