'''
WARNING: Do not execute this script without an secured environment. We blindly compile files from Github!

HOW TO USE:
python3 Scraper.py

The scraper will find keyword related repositories and look for simple compilable C files.
It creates a directory C_COMPILE with all the compilable .c files it found.

This scraper was developed by Akin Yilmaz.
'''

import requests
import os
import subprocess
import random
import time

# Replace with your GitHub Personal Access Token
GITHUB_TOKEN = 'TOKEN'

# GitHub API base URL
BASE_URL = 'https://api.github.com'

# Function to search for C programs on GitHub with pagination
def search_github_for_c_programs(query, created_date, page=1):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {
        'q': f'{query} created:{created_date}',
        'language': 'C',
        'per_page': 40,  # Adjust the number of results per page as needed
        'page': page  # Specify the page number
    }
    response = requests.get(f'{BASE_URL}/search/repositories', headers=headers, params=params)

    if response.status_code == 200:
        return response.json()['items']
    else:
        print(f"Response Status Error")
        return 0  # ERROR

# Create a folder named 'C_COMPILE' to store C files for compilation
if not os.path.exists('C_COMPILE'):
    os.makedirs('C_COMPILE')

# Function to check if a C file is compilable
def is_c_file_compilable(file_path):
    compile_cmd = f'gcc -o /dev/null {file_path}'  # Try to compile without producing an output binary
    compile_result = subprocess.run(compile_cmd, shell=True, capture_output=True)
    return compile_result.returncode == 0

keywords = [
    "C programming"
]
# Specify the date ranges you want to search, to bypass the 1000 repository limit per query
date_ranges = [ #The more fine tuned the date ranges the more repositories you can search for with the same query keyword
    "2016-01-01..2016-01-15",
    "2016-01-16..2016-01-31",
    "2016-02-01..2016-02-15",
    "2016-02-16..2016-02-29",
    "2016-03-01..2016-03-15",
    "2016-03-16..2016-03-31",
    "2016-04-01..2016-04-15",
    "2016-04-16..2016-04-30",
    "2016-05-01..2016-05-15",
    "2016-05-16..2016-05-31",
    "2016-06-01..2016-06-15",
    "2016-06-16..2016-06-30",
    "2016-07-01..2016-07-15",
    "2016-07-16..2016-07-31",
    "2016-08-01..2016-08-15",
    "2016-08-16..2016-08-31",
    "2016-09-01..2016-09-15",
    "2016-09-16..2016-09-30",
    "2016-10-01..2016-10-15",
    "2016-10-16..2016-10-31",
    "2016-11-01..2016-11-15",
    "2016-11-16..2016-11-30",
    "2016-12-01..2016-12-15",
    "2016-12-16..2016-12-31",
    "2017-01-01..2017-01-15",
    "2017-01-16..2017-01-31",
    "2017-02-01..2017-02-15",
    "2017-02-16..2017-02-28",
    "2017-03-01..2017-03-15",
    "2017-03-16..2017-03-31",
    "2017-04-01..2017-04-15",
    "2017-04-16..2017-04-30",
    "2017-05-01..2017-05-15",
    "2017-05-16..2017-05-31",
    "2017-06-01..2017-06-15",
    "2017-06-16..2017-06-30",
    "2017-07-01..2017-07-15",
    "2017-07-16..2017-07-31",
    "2017-08-01..2017-08-15",
    "2017-08-16..2017-08-31",
    "2017-09-01..2017-09-15",
    "2017-09-16..2017-09-30",
    "2017-10-01..2017-10-15",
    "2017-10-16..2017-10-31",
    "2017-11-01..2017-11-15",
    "2017-11-16..2017-11-30",
    "2017-12-01..2017-12-15",
    "2017-12-16..2017-12-31",
    "2018-01-01..2018-01-15",
    "2018-01-16..2018-01-31",
    "2018-02-01..2018-02-15",
    "2018-02-16..2018-02-28",
    "2018-03-01..2018-03-15",
    "2018-03-16..2018-03-31",
    "2018-04-01..2018-04-15",
    "2018-04-16..2018-04-30",
    "2018-05-01..2018-05-15",
    "2018-05-16..2018-05-31",
    "2018-06-01..2018-06-15",
    "2018-06-16..2018-06-30",
    "2018-07-01..2018-07-15",
    "2018-07-16..2018-07-31",
    "2018-08-01..2018-08-15",
    "2018-08-16..2018-08-31",
    "2018-09-01..2018-09-15",
    "2018-09-16..2018-09-30",
    "2018-10-01..2018-10-15",
    "2018-10-16..2018-10-31",
    "2018-11-01..2018-11-15",
    "2018-11-16..2018-11-30",
    "2018-12-01..2018-12-15",
    "2018-12-16..2018-12-31",
    "2019-01-01..2019-01-15",
    "2019-01-16..2019-01-31",
    "2019-02-01..2019-02-15",
    "2019-02-16..2019-02-28",
    "2019-03-01..2019-03-15",
    "2019-03-16..2019-03-31",
    "2019-04-01..2019-04-15",
    "2019-04-16..2019-04-30",
    "2019-05-01..2019-05-15",
    "2019-05-16..2019-05-31",
    "2019-06-01..2019-06-15",
    "2019-06-16..2019-06-30",
    "2019-07-01..2019-07-15",
    "2019-07-16..2019-07-31",
    "2019-08-01..2019-08-15",
    "2019-08-16..2019-08-31",
    "2019-09-01..2019-09-15",
    "2019-09-16..2019-09-30",
    "2019-10-01..2019-10-15",
    "2019-10-16..2019-10-31",
    "2019-11-01..2019-11-15",
    "2019-11-16..2019-11-30",
    "2019-12-01..2019-12-15",
    "2019-12-16..2019-12-31",
    "2020-01-01..2020-01-15",
    "2020-01-16..2020-01-31",
    "2020-02-01..2020-02-15",
    "2020-02-16..2020-02-29",
    "2020-03-01..2020-03-15",
    "2020-03-16..2020-03-31",
    "2020-04-01..2020-04-15",
    "2020-04-16..2020-04-30",
    "2020-05-01..2020-05-15",
    "2020-05-16..2020-05-31",
    "2020-06-01..2020-06-15",
    "2020-06-16..2020-06-30",
    "2020-07-01..2020-07-15",
    "2020-07-16..2020-07-31",
    "2020-08-01..2020-08-15",
    "2020-08-16..2020-08-31",
    "2020-09-01..2020-09-15",
    "2020-09-16..2020-09-30",
    "2020-10-01..2020-10-15",
    "2020-10-16..2020-10-31",
    "2020-11-01..2020-11-15",
    "2020-11-16..2020-11-30",
    "2020-12-01..2020-12-15",
    "2020-12-16..2020-12-31",
    "2021-01-01..2021-01-15",
    "2021-01-16..2021-01-31",
    "2021-02-01..2021-02-15",
    "2021-02-16..2021-02-28",
    "2021-03-01..2021-03-15",
    "2021-03-16..2021-03-31",
    "2021-04-01..2021-04-15",
    "2021-04-16..2021-04-30",
    "2021-05-01..2021-05-15",
    "2021-05-16..2021-05-31",
    "2021-06-01..2021-06-15",
    "2021-06-16..2021-06-30",
    "2021-07-01..2021-07-15",
    "2021-07-16..2021-07-31",
    "2021-08-01..2021-08-15",
    "2021-08-16..2021-08-31",
    "2021-09-01..2021-09-15",
    "2021-09-16..2021-09-30",
    "2021-10-01..2021-10-15",
    "2021-10-16..2021-10-31",
    "2021-11-01..2021-11-15",
    "2021-11-16..2021-11-30",
    "2021-12-01..2021-12-15",
    "2021-12-16..2021-12-31",
    "2022-01-01..2022-01-15",
    "2022-01-16..2022-01-31",
    "2022-02-01..2022-02-15",
    "2022-02-16..2022-02-28",
    "2022-03-01..2022-03-15",
    "2022-03-16..2022-03-31",
    "2022-04-01..2022-04-15",
    "2022-04-16..2022-04-30",
    "2022-05-01..2022-05-15",
    "2022-05-16..2022-05-31",
    "2022-06-01..2022-06-15",
    "2022-06-16..2022-06-30",
    "2022-07-01..2022-07-15",
    "2022-07-16..2022-07-31",
    "2022-08-01..2022-08-15",
    "2022-08-16..2022-08-31",
    "2022-09-01..2022-09-15",
    "2022-09-16..2022-09-30",
    "2022-10-01..2022-10-15",
    "2022-10-16..2022-10-31",
    "2022-11-01..2022-11-15",
    "2022-11-16..2022-11-30",
    "2022-12-01..2022-12-15",
    "2022-12-16..2022-12-31",
    "2023-01-01..2023-01-15",
    "2023-01-16..2023-01-31",
    "2023-02-01..2023-02-15",
    "2023-02-16..2023-02-28",
    "2023-03-01..2023-03-15",
    "2023-03-16..2023-03-31",
    "2023-04-01..2023-04-15",
    "2023-04-16..2023-04-30",
    "2023-05-01..2023-05-15",
    "2023-05-16..2023-05-31",
    "2023-06-01..2023-06-15",
    "2023-06-16..2023-06-30",
    "2023-07-01..2023-07-15",
    "2023-07-16..2023-07-31",
    "2023-08-01..2023-08-15",
    "2023-08-16..2023-08-31"
]

if __name__ == '__main__':
    for keyword_index, query in enumerate(keywords):
        for date_index, created_date in enumerate(date_ranges):
            page = 1
            # Limit the number of pages to search (e.g., 20 pages)
            while True:
                results = search_github_for_c_programs(query, created_date, page)
                if not results:
                    print(f'No more matching repositories found on GitHub for {created_date}.')
                    break

                for result_index, result in enumerate(results): # Iterating trough repos
                    repo_url = result['html_url']
                    repo_name = result['name']
                    print(f'Checking {repo_name} for C files...')

                    # Get the contents of the repository
                    contents_url = f'{BASE_URL}/repos/{result["owner"]["login"]}/{repo_name}/contents'
                    headers = {
                        'Authorization': f'token {GITHUB_TOKEN}',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                    contents_response = requests.get(contents_url, headers=headers)

                    if contents_response.status_code == 200:
                        contents = contents_response.json()
                        c_files = [file['name'] for file in contents if file['name'].endswith('.c')]

                        if c_files:
                            print(f'C files found in {repo_url}')
                            for index, c_file_url in enumerate(c_files):
                                c_file_path = os.path.join('C_COMPILE',
                                                           f'file_{result_index}_{date_index}_{keyword_index}_{created_date}_{page}_{index}.c')  # New name with a counter
                                download_url = f'https://raw.githubusercontent.com/{result["owner"]["login"]}/{repo_name}/master/{c_file_url}'

                                # Download the C file
                                headers = {
                                    'Authorization': f'token {GITHUB_TOKEN}',
                                    'Accept': 'application/vnd.github.v3.raw'  # Request raw content directly
                                }
                                download_result = requests.get(download_url, headers=headers)

                                if download_result.status_code == 200:
                                    with open(c_file_path, 'wb') as c_file:
                                        c_file.write(download_result.content)
                                    print(f'Downloaded {c_file_url} as {c_file_path} from {repo_url}')

                                    # Check if the downloaded C file is compilable
                                    if is_c_file_compilable(c_file_path):
                                        print(f'File {c_file_path} is compilable.')
                                    else:
                                        print(f'File {c_file_path} is not compilable. Removing...')
                                        os.remove(c_file_path)  # Remove the non-compilable file
                                else:
                                    print(f'Failed to download {c_file_url} from {repo_url}:')
                                    print(download_result.content)
                        else:
                            print(f'No C files found in {repo_url}')
                    else:
                        print(f'Failed to retrieve contents for {repo_url}')
                page = page + 1
