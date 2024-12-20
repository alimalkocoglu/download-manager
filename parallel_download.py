import subprocess
import sys
import os
import json


def download_with_parallel(file_with_links):
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

def create_initial_json(download_links, json_file):
    # Count the number of links in the download file
    with open(download_links, 'r') as f:
        total_links = len(f.readlines())

    # Create initial JSON data
    data = {
        "number_of_auto_starts": 0,
        "number_of_total_links": total_links,
        "number_of_remaining_links": total_links,
    }

    # Write the initial data to the JSON file
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_download_file>")
        sys.exit(1)

    file_with_links = sys.argv[1]

    if not os.path.exists(file_with_links):
        print(f"Error: The file '{file_with_links}' does not exist.")
        sys.exit(1)
    
    json_file = "download_information.json"
    create_initial_json(file_with_links,json_file)

    download_with_parallel(file_with_links)

if __name__ == "__main__":
    main()
