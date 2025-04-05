import os
import sys
import requests
from getopt import getopt
import urllib.request

runfile_setup_string = """#!/usr/bin/env python3
import os
import time
import requests
import urllib.request
import json
server_path = "$RUNPY_PATH"
desired_version = "$RUNPY_VERSION"
run_server_string = f"java -Xmx$RUNPY_MEMORY -Xms$RUNPY_MEMORY -jar {os.path.join(server_path, $RUNPY_PATH)} nogui"

def get_latest_build(version):
    def write_current_version(_version, build, file, endpoint):
        with open(os.path.join(server_path, "current-version.json"), "w") as f:
            json.dump({
                "version": _version,
                "build": build
            }, f)
        
        endpoint = endpoint.replace("$VERSION", _version)
        endpoint = endpoint.replace("$BUILD", build)
        endpoint = endpoint.replace("$FILE", file)
        return urllib.request.urlretrieve(endpoint, os.path.join(server_path, "server.jar")[1] 
"""

runfile_paper_string = """    
    print("Getting the latest build from papermc.io...")
    response = requests.get(f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds")
    if response.status_code != 200:
        raise Exception("Getting latest build from papermc.io failed, did you specify a correct version, are their servers down, do you have connection to the internet?")
    response = response.json()
    last_build = response["builds"][len(response["builds"]) - 1]["build"]
    file_name = response["builds"][len(response["builds"]) - 1]["downloads"]["application"]["name"]
"""

runfile_fabric_string = """
    print("Getting the latest build from fabricmc.net...")
    response = requests.get(f"https://meta.fabricmc.net/v2/versions/loader/{version}")
    if response.status_code != 200:
        raise Exception("Getting latest build from fabricmc.net failed, did you specify a correct version, are their servers down, do you have connection to the internet?")
    build_response = response.json()
    last_build = build_response[0]["loader"]["version"]
    response = requests.get(f"https://meta.fabricmc.net/v2/versions/installer")
    installer_response = response.json()
    last_installer = installer_response[0]["version"]
    url = f"https://meta.fabricmc.net/v2/versions/loader/{version}/{last_build}/{last_installer}/server/jar"
"""

runfile_check_build_update_logic_string = """
    if os.path.exists(os.path.join(server_path, "current-version.json")):
        with open(os.path.join(server_path, "current-version.json"), "r") as f:
            last = json.load(f)
        if last["version"] == version and last["build"] == build:
            print("No new updates were found to this version from server flavor vendor.")
            return False
        print("Update to server jarfile build from server flavor vendor available.")
        return write_current_version(version, build, file_name, url)
    else:
        print("No previous build found, downloading latest build.")
        return write_current_version(version, build, file_name, url)
        
"""

runfile_get_latest_version_paper_string = """
def get_latest_version():
    latest = requests.get("https://api.papermc.io/v2/projects/paper/").json()
    return latest["versions"][len(latest["versions"]) - 1]
"""

runfile_get_latest_version_fabric_string = """
def get_latest_version():
    latest = requests.get("https://meta.fabricmc.net/v2/versions").json()
    index = 0
    while "w" in latest["game"][index]["version"]:
        index += 1
        if index >= len(latest["game"]):
            raise Exception("Could not find stable version of Minecraft for fabric?")
    return latest["game"][index]["version"]
"""

runfile_run_script_string = """
if __name__ == "__main__":
    os.chdir(server_path)
    while True:
        print("Checking for updates to server jarfile")
        get_latest_build(desired_version)
        print("Starting server...")
        os.system(run_server_string)
        print("Server stopped, press CTRL+C to stop the server from restarting.")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
"""

options = {}

def parseargs():
    global options
    opts, args = getopt(sys.argv[1:], "h", ["help"])
    for opt, arg in opts:
        if opt in ("-h", "--help") or len(opts) == 0 or opt in ("-E", "--agree-eula"):
            print("Usage: python3 paper-pi.py [options]")
            print("Options:")
            print("  -h, --help        Show this help message and exit")
            print("  -E, --agree-eula  Agree to the Minecraft EULA. If not specified, the script will show this message and exit.")
            print("  -f, --flavor      Flavor of Minecraft server to install (paper/fabric)")
            print("  -p, --path        Path to the Minecraft server directory (default: ~/minecraft)")
            print("  -v, --version     Version of Minecraft server to install (default: newest, keep updated)")
            print("  -m, --memory      Amount of RAM to allocate to the server (Xmx and Xms) (default: 2048M)")
            sys.exit(0)
        elif opt in ("-f", "--flavor"):
            options["flavor"] = arg
        elif opt in ("-p", "--path"):
            options["path"] = arg
        elif opt in ("-v", "--version"):
            options["version"] = arg
        elif opt in ("-m", "--memory"):
            options["memory"] = arg

def apply_defaults():
    global options
    option_defaults = {
        "path": os.path.expanduser("~/minecraft"),
        "version": "latest",
        "memory": "2048M"
    }

    for key, default in option_defaults.items():
        if key not in options:
            options[key] = default


def get_jar():
    if options["flavor"] == "paper":
        print("Getting the latest build from papermc.io...")
        response = requests.get(f"https://api.papermc.io/v2/projects/paper/versions/{options['version']}/builds")
        if response.status_code != 200:
            raise Exception("Getting latest build from papermc.io failed, did you specify a correct version, are their servers down, do you have connection to the internet?")
        response = response.json()
        last_build = response["builds"][len(response["builds"]) - 1]["build"]
        file_name = response["builds"][len(response["builds"]) - 1]["downloads"]["application"]["name"]
        url = f"https://api.papermc.io/v2/projects/paper/versions/{options['version']}/builds/{last_build}/downloads/{file_name}"
    elif options["flavor"] == "fabric":
        print("Getting the latest build from fabricmc.net...")
        response = requests.get(f"https://meta.fabricmc.net/v2/versions/loader/{options['version']}")
        if response.status_code != 200:
            raise Exception("Getting latest build from fabricmc.net failed, did you specify a correct version, are their servers down, do you have connection to the internet?")
        build_response = response.json()
        last_build = build_response[0]["loader"]["version"]
        response = requests.get(f"https://meta.fabricmc.net/v2/versions/installer")
        installer_response = response.json()
        last_installer = installer_response[0]["version"]
        url = f"https://meta.fabricmc.net/v2/versions/loader/{options['version']}/{last_build}/{last_installer}/server/jar"
    else:
        raise Exception("Unknown/invalid flavor specified. Use -h or check docs for a list of supported flavors.")
    print("Downloading...")
    urllib.request.urlretrieve(url, os.path.join(options["path"], "server.jar"))


def create_runfile():
    global runfile_setup_string
    if os.path.exists(os.path.join(options["path"], "run.py")):
        os.remove(os.path.join(options["path"], "run.py"))

    runfile_setup_string = runfile_setup_string.replace("$RUNPY_MEMORY", options["memory"])
    runfile_setup_string = runfile_setup_string.replace("$RUNPY_PATH", options["path"])
    runfile_setup_string = runfile_setup_string.replace("$RUNPY_VERSION", options["version"])

    if options["flavor"] == "paper":
        runfile_server_string = runfile_paper_string
        runfile_get_latest_version_string = runfile_get_latest_version_paper_string
    elif options["flavor"] == "fabric":
        runfile_server_string = runfile_fabric_string
        runfile_get_latest_version_string = runfile_get_latest_version_fabric_string
    else:
        raise Exception("????")

    with open(os.path.join(options["path"], "run.py"), "a") as f:
        f.write(runfile_setup_string)
        f.write(runfile_server_string)
        f.write(runfile_check_build_update_logic_string)
        f.write(runfile_get_latest_version_string)
        f.write(runfile_run_script_string)



def setup():
    print("---Paper Pi v2---")
    print("A Minecraft server run file generator")

    try:
        os.makedirs(options["path"], exist_ok=False)
    except FileExistsError:
        yn = input(f"Directory {options['path']} already exists. Are you sure you want to write into it?(y/n): ")
        if yn.lower() != "y":
            print("Exiting...")
            sys.exit(1)
        os.makedirs(options["path"], exist_ok=True)
    except:
        print("Error creating directory. Did you misspell the path?")
        sys.exit(1)

    with open(os.path.join(options["path"], "eula.txt"), "w") as f:
        f.write("eula=true")

    get_jar()

if __name__ == "__main__":
    print("---Paper Pi v2---")
    print("A Minecraft server run file generator")
    parseargs()
    setup()
    create_runfile()