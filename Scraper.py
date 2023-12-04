'''
WARNING: Do not execute this script without an secured environment, or atleast, without privilege.

This scraper was developed by Akin Yilmaz, Master of Data and CS Student from University Heidelberg.

ADVANCED GITHUB SCRAPER FOR C CODE - ASSEMBLY Training data.
This scraper is able to scrape multi-source-c files from repositories and compile them if the library is supported.
It will generate two folders: C_COMPILE and COMPILED.
The one contains the relevant source and header files, the other the compiled object files.
Every source file that contains a gcc command at the very first line is compileable. One can use this command to instantly compile the file without bothering about -I(nclude) direcotires.
The Scraper.py will generate the paths with respect to the current OS, so reusing the result in a different OS like Windows requries the paths to be normalized again via os.path.normpath.
The repository structure is maintained while scraping. The script also generates a compiler_errors.txt, to log the error messages for failed compilations.

HOW TO USE:
0.) Please use a virtual environment before executing this script. Compilers may contain exploits. Also compiler bombs can blow up your entire memory : ).
1.) Set GITHUB_TOKEN to your personal Token
2.) In the main function set start and end date. You can also choose keywords if you want to scrape specific repositories like "Malware" for malware analysis.
3.) In the is_c_file_compilable function you can adapt to use specific compilers or optimization levels. By default we use gcc without optimization flags.
4.) In the main function you can also select propagation_level and MAX_C_FILE. The first controlls how deep we look into Repositories, the second how many files per directory we download at most.

TIP:
- You can scrape with your friends. Let them use their own Token, distinct date ranges, or different keywords, ...
- Tons of ways to optimize the script. You can dig deeper in the directories if there exists c files in the master branch or src...or only look for specific folders like default, src and Includes ...
- The more we dig, the more we will find ; ) propagation levels slow the process down, but can find more. Try to optimize it with various techniques to skip repos faster.
MISSING FEATURES:
- If file is not available, eventually search for it it the github repo as a query, and download it then instead of searching every branch for it...
- Timeout on compilation to prevent compiler bombs or in general too heavy binaries
- Checking if a repo has already been downloaded, you could skip this repo - use os.path.exists in the main function

The initial intention of this scraper is to generate huge amount of training data of C-Code and Assembly to train a model for reverse engineering.

TODOS:
- Relative paths should be resolved relatively to the source file
- Download at most LIMIT C files from a repo
- gcc -I all repos that we visited already to make use of our downloaded headers
- Some reasons why some header files are not found for compiling a source file:
     1. Propagation level is too low
     2. The headers are in different branches (not always is everything in the default master/main branch)

FAQ:
Q: Is this scraper secure to execute?
A: No.

Q: Why does the scraper not download all files into one directory and we just compile it from there, why trying to maintain the structure?
A: We would need to relabel every relative path in the #include section. Works, but messy.

Q: Can I use this scraper (modified) for commericial use?
A: This script is under GNU v3.

Q: Do I get IP banned for ignoring Ratelimiting?
A: Github will ban the account connected to the personal Token, not your IP. Do not remove ratelimit-waits in the source code.

Q: Can we accelerate the scraping using different Tokens?
A: Yes. Rotating Tokens can be a smart workaround the ratelimit. Authorized requests cannot get banned by IP, but by the account.

Q: Why does the compiler sometimes fail to compile source files?
A: Multiple reasons might be the cause. Either you do not simply support an external library, or the header was just not found within the propagation limit, or the header is in a different branch than the main.

Q: Should I check different branches for files?
A: Not worth your requests and time on average. Most important files should be in the default branch by common sense.

Possible Exploits:
Since we blindly store files with relative paths, one could save (with privilege) certain files into the systems files with intention of the repository creator.
If one source file for example includes a malicious file header.h, and chooses by purpose a relative path #include "../../../../usr/header.h" (assuming the Repository has the same structure as our Linux file system),
we will blindly store this file there. It might overwrite important functions of already existing headers and interject malicious code to escalate privilege.
'''

import requests
import os
import subprocess
import time
from datetime import datetime, timedelta
import shutil
from urllib.parse import urljoin
import re
# Replace with your GitHub Personal Access Token
GITHUB_TOKEN = 'TOKEN'


# GitHub API base URL
BASE_URL = 'https://api.github.com'

visited_include_folders = set() #
def wait_for_ratelimit_reset(response):
    #print(response.headers)
    #total_requests = int(response.headers.get('x-ratelimit-limit', 0))
    remaining_requests = int(response.headers.get('x-ratelimit-remaining', 0))
    reset_time = int(response.headers.get('x-ratelimit-reset', 0))
    if remaining_requests == 0:
        # Rate limit exceeded, wait until reset
        wait_time = max(0, reset_time - time.time())
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds...")
        time.sleep(wait_time)


# Function to search for C programs on GitHub with pagination
def search_github_for_c_programs(keyword,created_date, page=1):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {
        'q': f'{keyword} created:{created_date}',
        'language': 'C',
        'per_page': 100,
        'page': page
    }
    response = requests.get(f'{BASE_URL}/search/repositories', headers=headers, params=params)
    wait_for_ratelimit_reset(response)
    if response.status_code == 200:
        return response.json()['items']
    else:
        print(f"Response Status Error")
        return 0  # ERROR


# Create a folder named 'C_COMPILE' to store C files for compilation
if not os.path.exists('C_COMPILE'):
    os.makedirs('C_COMPILE')


# Function to check if a C file is compilable
def is_c_file_compilable(repo_owner,repo_name,base_path_arr,file_name,file_path, error_log_file='compile_errors.txt'):
    '''
    This function checks if a source.c is compileable using GCC, and stores the object files in a directory COMPILED its structure is equal to repos on Github.
    If a source file is compiled in reponame_repoowner/master/src/source.c,
    we store the object file in COMPILED/reponame_repoowner/src/source.o.
    We make in addition sure, the compiler checks Include directory for missing headers, since we manually download Include directories from Github without any interaction with source files.
    We make sure the compilation time takes less than two minutes and consumes less than 100MB of storage, to avoid compiler bombs, and in general too much waiting time per repo.
    '''
    compile_destination_directory= os.path.join('COMPILED',repo_name+'_'+repo_owner,*base_path_arr)
    os.makedirs(compile_destination_directory, exist_ok=True)
    # Final compile destination by turning filename.c to filename.o, so we will store gccs output at compile_destination_directory/filename.o
    compile_destination = os.path.join(compile_destination_directory,file_name.rsplit('.', 1)[0] + '.o')
    # Some Github repositories use #includes in the /include subdirectory, but do not mention it in #include "test.h" (instead "/subdirectory/test.h)
    # These repositories command the gcc (e.g. by makefile) to additionally look into these directories for missing headers
    # We try to add the most common one as example, but one could add ALL subdirectories

    folder_path = os.path.join('C_COMPILE', f'{repo_name}_{repo_owner}',
                               *base_path_arr)
    INCLUDE_PATH = os.path.join(folder_path,'Include') # Example to include additionally local Include folder automatically, in case gcc cannot find header at relative path
    visited_include_folders.add(INCLUDE_PATH)

    all_include_folders = ' '.join(['-I'+folder for folder in visited_include_folders])


    # Note: -I argument takes directory path without space. If we run gcc -c source.c with subdir "Include" we use -IInclude to pass Include directory
    compile_cmd = f'gcc -c -o {compile_destination} {file_path} {all_include_folders}'  # Try to compile without producing an output binary by gcc -c /dev/null if you want
    compile_result = subprocess.run(compile_cmd, shell=True, capture_output=True)

    if compile_result.returncode != 0:
        error_message = compile_result.stderr.decode('utf-8',errors='ignore')
        with open(error_log_file, 'a') as error_file:
            error_file.write(f"{compile_cmd}\n{file_path}\n{error_message}\n")
    elif compile_result.returncode == 0:
        with open(file_path, 'r') as c_file:
            c_code = c_file.read()
        with open(file_path, 'w') as c_file:
            c_file.write(f'//{compile_cmd}\n{c_code}')


    # Reset resource limits to default
    #resource.setrlimit(resource.RLIMIT_CPU, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    #resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

    return compile_result.returncode == 0

# Function to filter the #include "header.h" files names from Code
def extract_included_headers(c_code):
    '''Assure the c_code is in utf-8 format. The Github-API delivers bytes as response'''
    # Define a regular expression pattern to match #include statements
    pattern = re.compile(r'#include\s*\"(.*?)\"')
    # Find all matches in the C code
    header_files = pattern.findall(c_code)
    return header_files

def download_c_files_headers(repo_owner,repo_name,base_path_arr,content,git_headers,default_branch,propagation_limit):
    '''
    This function downloads necessary headers, and even propagates trough nested includes.
    It maintains the same directory structure as in github locally to allow easy compiling of the source files later.
    It will not redownload any files that already exists.

    Regarding nested includes:
    If source.c includes header.h, and header.h includes header2.h ... we need to download all of them.
    Most compilers allow nesting with atleast 8 layers. We will limit our nested downloads upto 8 layers, propagation_limit will gurantee this.
    '''
    if propagation_limit <= 0:
        return
    else:
        propagation_limit = propagation_limit - 1

    headers = extract_included_headers(content) # ['header.h', '../headers/header.h', '/header/header.h'], Note: Githubs api delivers contents in bytes, we decode it first
    #If there is no more neccessary headers, we terminate basically our recursion
    for header_file in headers:  # Iterate trough headers and download them if they dont exist
        #Warning, do not reuse path_normalized. It gets modified within the while-Loop.

        '''IMPORTANT: INCLUDES ARES RELATIVE TO SOURCE FILE.'''
        #src/../dir/header.h becomes /dir/header.h
        path_normalized = os.path.normpath(os.path.join(*base_path_arr, header_file)) # We normalize to append to our github url, the relative path is resolved from the #include "../header.h"
        #We want to break down this path into its elements, will become handy
        path_elements= []
        while 1:
            path_normalized, directory = os.path.split(path_normalized)

            if directory != "":
                path_elements.append(directory)
            else:
                if path_normalized != "":
                    path_elements.append(path_normalized)
                break
        path_elements.reverse() # Format is ["dir1", "dir2", ..., "header.h"]

        file_name = path_elements[-1]  # Get header file name (equivalent to header_file.split("/")[-1] )
        directory_elements = path_elements[0:-1]  # Get the neccessary directory structure /directory1/directory2 of the header
        folder_path = os.path.join('C_COMPILE', f'{repo_name}_{repo_owner}',*directory_elements)  # Prepare directory structure for local storage

        h_file_path = os.path.join(folder_path,file_name)
        visited_include_folders.add(folder_path)

        if os.path.exists(h_file_path): # No need to redownload the file if it exists
            print(f'The header file alreayd exists {file_name}')
            continue #No need to handle the recursive case here, it was already handled : )
        else:
            header_file_url = f'https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{default_branch}/'+'/'.join(path_elements)
            download_result = requests.get(header_file_url, headers=git_headers) #We download the header
            #wait_for_ratelimit_reset(download_result) RAW REQUESTS are different and contain no ratelimit information in the response
            os.makedirs(folder_path, exist_ok=True)
            if download_result.status_code == 200:
                with open(h_file_path, 'w',encoding="utf-8") as h_file:
                    h_file.write(download_result.content.decode('utf-8',errors='ignore'))
            else:
                print(f'Failed to download header {file_name}: {download_result.content.decode("utf-8",errors="ignore")}')
                return #We gotta leave our recursive calls if we fail to download it
        #At this point we have our header file downloaded, and would like to download nested headers
        with open(h_file_path, 'r',encoding="utf-8") as file:
            content = file.read() #already in utf-8 format

            print("FOLLOWING FILE CAUSED THE HEADER RECURSION: " + file_name)
            #Its important to keep the base_path_arr towards the original source file, since the include paths are relative to it!
            download_c_files_headers(repo_owner, repo_name, base_path_arr, content, git_headers, default_branch, propagation_limit) #Only the content changed for recursive call


# Function to download C files recursively from a repository
def download_c_files_recursive(repo_owner, repo_name, base_path_arr, git_headers, default_branch,propagation_limit, MAX_C_FILE):
    '''We start and default branch and download c files, going recursively propagation_limit levels deep.
    By convention we also download all header files in the Include folder.
    Furthermore, we download all relevant headers, by reading out the include preprocessor of the c files.
    '''
    if propagation_limit <= 0: # How many layers deep we look for c files
        return
    else:
        propagation_limit = propagation_limit - 1
    contents_url = f'{BASE_URL}/repos/{repo_owner}/{repo_name}/contents/'+'/'.join(base_path_arr) #base_path_arr has the format [dir,dir2, ...]
    contents_response = requests.get(contents_url, headers=git_headers)
    wait_for_ratelimit_reset(contents_response)
    if contents_response.status_code == 200:
        contents = contents_response.json()
        for file in contents:
            if (file['type'] == 'file' and (file['name'].endswith('.c') or file['name'].endswith('.h'))):#
                MAX_C_FILE = MAX_C_FILE - 1
                if MAX_C_FILE < 0:  # How many C files we download at most
                    return
                folder_path = os.path.join('C_COMPILE',f'{repo_name}_{repo_owner}',*base_path_arr) #We avoid name conflicts by adding repo owner to directory name. Repos can have same name by different users.
                visited_include_folders.add(folder_path) # We need gcc to check this folder later for missing headers. #include <h1.h> in a subdirectory header file h2.h, uses the header from ../ source files directory.
                #Furthermore, with *base_path_arr we unpack the arguments
                os.makedirs(folder_path,exist_ok=True)
                c_file_path = os.path.join(folder_path,file["name"])
                download_url = file['download_url']
                # Download the C file
                download_result = requests.get(download_url, headers=git_headers)
                #wait_for_ratelimit_reset(download_result)
                if download_result.status_code == 200:
                    with open(c_file_path, 'wb') as c_file:
                        c_file.write(download_result.content)
                    print(f'Downloaded {file["name"]} as {c_file_path}')
                    # Check if we work with static-libraries 
                    # 1. We store relevant header files
                    # 2. We recursively download the relevant header files before compiling without linker
                    print("FOLLOWING FILE CAUSED THE HEADER RECURSION: "+file["name"])
                    download_c_files_headers(repo_owner,repo_name,base_path_arr,download_result.content.decode('utf-8', errors='ignore'),git_headers,default_branch, 8) # Here we set the propagation limit of 8

                    # Check if the downloaded C file is compilable
                    if file['name'].endswith('.c') and is_c_file_compilable(repo_owner,repo_name,base_path_arr,file["name"],c_file_path):
                        print(f'File {c_file_path} is compilable.')
                    elif file['name'].endswith('.c'):
                        print(f'File {c_file_path} is not compilable. Removing...')
                        #os.remove(c_file_path) We better not remove the files and keep them, and later analyse what headers we need on average to install the libraries manually
                        #shutil.rmtree(folder_path)  # For removing the folder
                else:
                    print(f'Failed to download {file["name"]}: {download_result.content.decode("utf-8", errors="ignore")}')
            elif file['type'] == 'dir': # and file['name']=='src': and add ['src']
                # Recursively download files from the subdirectory
                download_c_files_recursive(repo_owner, repo_name, base_path_arr + [file['name']], git_headers,default_branch,propagation_limit, MAX_C_FILE)
    else:
        print(f'Failed to retrieve contents for {contents_url}')


# Specify the date ranges you want to search, to bypass the 1000 repository limit per query
def generate_date_intervals(start_year, end_year, day_steps):
    date_intervals = []
    current_date = datetime(start_year, 1, 1)

    while current_date.year <= end_year:
        next_date = current_date + timedelta(days=day_steps)
        date_intervals.append(f"{current_date.strftime('%Y-%m-%d')}..{next_date.strftime('%Y-%m-%d')}")
        current_date = next_date

    return date_intervals

def get_supported_libraries(): #One could check if we can provide the libraries before even attempting to download the headers ect.
    ...
    '''Returns an array of the libraries our device supports, by listing all .h files in the /usr/ space.'''
    

if __name__ == '__main__':
    start_year = 2016
    end_year = 2016
    day_steps = 30
    propagation_level = 2
    MAX_C_FILE = 100
    keywords = ['C programming'] #Empty Keyword '' to scrape broad and widely (is slow)
    date_ranges = generate_date_intervals(start_year, end_year, day_steps)
    for keyword in keywords:
        for date_index, created_date in enumerate(date_ranges):
            page = 1
            while True:
                results = search_github_for_c_programs(keyword, created_date, page)

                if not results:
                    print(f'No more repositories found on GitHub for {created_date}.')
                    break

                for result_index, result in enumerate(results): #Here we iterate the repositories
                    visited_include_folders = set() # We gotta reset this, to keep track which folders we visited and let gcc use these for finding missing headers later.
                    repo_owner = result['owner']['login']
                    repo_name = result['name']
                    default_branch = result['default_branch'] # Some humans make life hard, we need to assure masters? main?
                    print(f'Checking {repo_name} for C files...')

                    git_headers = {
                        'Authorization': f'token {GITHUB_TOKEN}',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                    try:
                        download_c_files_recursive(repo_owner, repo_name, [], git_headers,default_branch,propagation_level,MAX_C_FILE)
                    except Exception as e:
                        time.sleep(6000)
                        print(f"Eventually Networkerror... {e}")
                    # Propagation Level: 1 Main directory only, 2 one subdirectory deep, 3 two subdirecotires deep...
                    # MAX_C_FILE the amount of c files we download at most from a directory

                page += 1
