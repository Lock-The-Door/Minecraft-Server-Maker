"""
A cool script to quickly get a minecraft server up and running.
"""

import os
import sys
import subprocess
import requests
import regex
import asyncio
import threading
import configparser

# Constants
SERVER_URL = "https://quiltmc.org/api/v1/download-latest-installer/java-universal"
CONFIGURED_SERVER_PROPERTIES = {
    "motd": True,
    "enforce-secure-profile": True,
    "difficulty": True,
    "max-players": True,
    "online-mode": True,
    "allow-flight": True,
    "view-distance": True,
    "server-port": True,
    "sync-chunk-writes": True,
    "entity-broadcast-range-percentage": True,
    "simulation-distance": True,
    "spawn-protection": True,
    "snooper-enabled": True,
    "enable-jmx-monitoring": False,
    "rcon.port": False,
    "level-seed": False,
    "gamemode": False,
    "enable-command-block": False,
    "enable-query": False,
    "generator-settings": False,
    "level-name": False,
    "query.port": False,
    "pvp": False,
    "generate-structures": False,
    "max-chained-neighbor-updates": False,
    "network-compression-threshold": False,
    "max-tick-time": False,
    "require-resource-pack": False,
    "use-native-transport": False,
    "enable-status": False,
    "initial-disabled-packs": False,
    "broadcast-rcon-to-ops": False,
    "server-ip": False,
    "resource-pack-prompt": False,
    "allow-nether": False,
    "enable-rcon": False,
    "op-permission-level": False,
    "prevent-proxy-connections": False,
    "hide-online-players": False,
    "resource-pack": False,
    "rcon.password": False,
    "player-idle-timeout": False,
    "force-gamemode": False,
    "rate-limit": False,
    "hardcore": False,
    "white-list": False,
    "broadcast-console-to-ops": False,
    "spawn-npcs": False,
    "spawn-animals": False,
    "function-permission-level": False,
    "initial-enabled-packs": False,
    "level-type": False,
    "text-filtering-config": False,
    "spawn-monsters": False,
    "enforce-whitelist": False,
    "resource-pack-sha1": False,
    "max-world-size": False,
}

# Globals
server_configuration = {
    "name": None,
    "location": None,
    "version": None,
    "properties": {},
    "mods_config": None,
}

def get_server_info():
    # Get the parent directory for the server
    server_location = None
    while server_location is None:
        server_location = input("Enter the location of the server: ")
        if not os.path.isdir(server_location):
            print("That is not a valid directory.")
            server_location = None
    server_configuration["location"] = server_location

    # Get the server version
    server_version = None
    while server_version is None:
        server_version = input("Enter the server version: ")
        if regex.match(r"^1\.[1-9]\d*(\.[1-9]\d*)?$", server_version) is None:
            print("That is not a valid version.")
            server_version = None
    server_configuration["version"] = server_version

    # Get the server name
    server_name = None
    while server_name is None:
        server_name = input("Enter the server name: ")
        if len(server_name) > 20:
            print("That name is too long.")
            server_name = None
    server_configuration["name"] = server_name

    # Get the server properties
    server_properties = {"motd": None, "max-players": None, "server-port": None, "online-mode": None}
    server_property = None
    while server_property != "done":
        server_property = None
        for property_key, value in server_properties.items():
            if value is None:
                server_property = property_key
                break
        while server_property is None:
            server_configuration["properties"] = server_properties
            server_property = input("You have entered all the required properties. Anything you want to add? [(property key)/done]: ")
            if server_property == "done":
                break
            if server_property not in CONFIGURED_SERVER_PROPERTIES:
                print("That is not a valid property.")
                server_property = None

        if server_property == "done":
            break
        server_properties[server_property] = input(f"Enter the value for the property {server_property}: ")
    server_configuration["properties"] = server_properties

    # Get the server mods
    server_mods = None
    while server_mods is None:
        # List mod configs in the modpacks folder
        modpacks_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), "modpacks")
        modpacks = os.listdir(modpacks_folder)
        # Strip the .ini extension
        modpacks = [modpack[:-4] for modpack in modpacks]
        print("Available mod configurations:")
        for modpack in modpacks:
            print(f" - {modpack}")
        # Get the mod config
        server_mods = input("Enter the name of the mod configuration you want to use: ")
        if server_mods not in modpacks:
            print("That mod configuration does not exist.")
            server_mods = None
    server_configuration["mods_config"] = server_mods

    print("Server configuration complete, please wait for the configurator to finish...")

def download_quilt():
    # Grab the latest quilt jar
    quilt_jar_request = requests.get(SERVER_URL, stream=True)
    if quilt_jar_request.status_code != 200:
        print("Could not download the latest server jar.")
        sys.exit(1)
    # Save the jar in the same directory as this script
    jar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "quilt-installer.jar")
    with open(jar_path, "wb") as jar_file:
        jar_file.write(quilt_jar_request.content)

async def download_server(version, location):
    # Run the quilt installer
    jar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "quilt-installer.jar")
    status = await asyncio.create_subprocess_exec(["java", "-jar", jar_path, "install", "server", version, "--download-server"],
                            cwd=location, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if status.returncode != 0:
        print("Could not download the server jar.")
        sys.exit(1)

def accept_eula(server_location):
    eula_path = os.path.join(server_location, "eula.txt")
    with open(eula_path, "w") as eula_file:
        eula_file.write("eula=true")

async def copy_start_script(server_location):
    # There should be scripts located in the same directory as this script under the scripts folder
    scripts_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "scripts")
    threads = list()
    for path in os.listdir(scripts_path):
        source_path = os.path.join(scripts_path, path)
        dest_path = os.path.join(server_location, os.path.basename(path))
        threads.append(threading.Thread(target=copy_file, args=(source_path, dest_path)))
        threads[-1].start()

    for thread in threads:
        while thread.is_alive():
            await asyncio.sleep(0.1)
        

async def create_ferium_profile(name, location, version):
    mod_path = os.path.join(location, "mods")
    status = await asyncio.create_subprocess_exec(["ferium",  "profile",  "create", "-v", version, "-m", "quilt", "-n", name, "-o", mod_path], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if status.returncode != 0:
        print("Could not create the ferium profile.")
        sys.exit(1)

async def write_server_properties(server_location):
    # Write the server.properties file
    written_server_properties = []
    server_properties_path = os.path.join(server_location, "server.properties")
    with open(server_properties_path, "w") as server_properties_file:
        server_properties_file.writelines([
            "enforce-secure-profile=false", 
            "difficulty=hard",
            "allow-flight=true",
            "view-distance=32",
            "sync-chunk-writes=false",
            "entity-broadcast-range-percentage=500",
            "simulation-distance=32",
            "spawn-protection=0"])

        # Wait for server.properties to be entered (4 settings)
        while len(server_configuration["properties"]) < 4:
            await asyncio.sleep(1)
            # Write the server.properties file
            for key, value in server_configuration["properties"].items():
                if key not in written_server_properties:
                    server_properties_file.write(f"{key}={value}")
                    written_server_properties.append(key)

def write_additional_server_properties(server_location, properties):
    server_properties_path = os.path.join(server_location, "server.properties")
    # Read the server.properties file
    server_properties = {}
    with open(server_properties_path, "r") as server_properties_file:
        for line in server_properties_file.readlines():
            pair =line.split("=")
            key = pair[0]
            value = pair[1]
            server_properties[key] = value

    # Filter out the 4 properties that are already in the file
    written = ["motd", "max-players", "server-port", "online-mode"]
    for property in written:
        properties.pop(property)

    # Merge the properties
    server_properties.update(properties)

    # Write the additional properties
    with open(server_properties_path, "w") as server_properties_file:
        for key, value in server_properties.items():
            server_properties_file.write(f"{key}={value}")

async def download_mods(server_name, mods_config):
    # Mods config is a file in the modpacks directory in the same directory as this script
    mods_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "modpacks", mods_config + ".ini")
    if not os.path.isfile(mods_config_path):
        print("Could not find the mods config file.")
        sys.exit(1)

    # Read the mods config file
    # The mod list is located under the [General] section in the mods key, command separated
    mods = mods_config["General"]["mods"].split(",")

    # Ensure on the correct profile
    await asyncio.create_subprocess_exec(["ferium", "profile", "switch", server_name], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # Add the mods
    for mod in mods:
        await asyncio.create_task(download_mod(mod))

    # Actually download them now
    subprocess.run(["ferium", "upgrade"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

async def download_mod(mod):
    await asyncio.create_subprocess_exec(["ferium", "add", mod], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

async def download_skin_mod(server_name):
    await asyncio.create_subprocess_exec(["ferium", "profile", "switch", server_name], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    await asyncio.create_task(download_mod("skinpls"))

async def read_dependencies(server_name, server_path, mods_config):
    additional_mod_configs = mods_config["Dependencies"].get("modConfigs", "").split(",")
    for mod_config_src in additional_mod_configs:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "modpacks", mod_config_src + ".ini"), "r") as mod_config_file:
            mod_config = configparser.ConfigParser()
            mod_config.read_file(mod_config_file)
            await asyncio.create_task(read_dependencies(server_name, server_path, mod_config))
            await asyncio.create_task(download_mods(server_name, mod_config))
            await asyncio.create_task(copy_configuration_files(server_path, mod_config))

async def copy_configuration_files(server_path, mods_config):
    # Configs to copy are listed under the mods section under the key "configs"
    # They are split by commas and each config is sourcename:destpath
    mods_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "modpacks", mods_config + ".ini")
    if not os.path.isfile(mods_config_path):
        print("Could not find the mods config file.")
        sys.exit(1)

    # Read the mods config file
    configs = mods_config["General"]["configs"].split(",")
    threads = list()
    for config in configs:
        threads.add(threading.Thread(target=copy_config, args=(server_path, config)))
        threads[-1].start()
    
    # Wait for all the threads to finish
    for thread in threads:
        while thread.is_alive():
            await asyncio.sleep(1)

def copy_config(server_path, config):
    pair = config.split(":")
    source = os.path.join(os.path.dirname(os.path.realpath(__file__)), "configs", pair[0])
    dest = os.path.join(server_path, "config", pair[1])

    # Ensure the destination directory exists
    dest_dir = os.path.dirname(dest)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)

    # Copy the file
    copy_file(source, dest)

def copy_file(source, dest):
    with open(source, "r") as source_file:
        with open(dest, "w") as dest_file:
            dest_file.write(source_file.read())

async def main():
    # Get the server info asynchronously
    threading.Thread(target=get_server_info).start()
    # Download the quilt jar
    quilt_thread = threading.Thread(target=download_quilt)
    quilt_thread.start()

    # Wait for the location to be entered
    while server_configuration["location"] is None:
        await asyncio.sleep(1)

    # Ensure the server directory exists
    server_path = os.path.join(server_configuration["location"], "server")
    if not os.path.isdir(server_path):
        os.mkdir(server_path)

    # Start writing the server.properties file
    write_server_properties_task = asyncio.create_task(write_server_properties(server_path))

    # Copy the start scripts
    copy_start_script_task = asyncio.create_task(copy_start_script(server_path))

    # Agree to the eula
    accept_eula(server_path)

    # Wait for the server version to be entered
    while server_configuration["version"] is None:
        await asyncio.sleep(1)

    # Ensure quilt is downloaded
    quilt_thread.join()

    # Download the server jar
    download_server_task = asyncio.create_task(download_server(server_configuration["version"], server_configuration["location"]))

    # Wait for the server's name to be entered
    while server_configuration["name"] is None:
        await asyncio.sleep(1)

    # Wait for the server jars to be downloaded and start scripts to be copied
    await download_server_task
    await copy_start_script_task

    # Wait for the server's properties to be entered
    await write_server_properties_task

    # Rename the folder
    server_path = os.path.join(server_configuration["location"], server_configuration["name"])
    os.rename(os.path.join(server_configuration["location"], "server"), server_path)

    # Create ferium profile
    create_ferium_profile_task = asyncio.create_task(create_ferium_profile(server_configuration["name"], server_path, server_configuration["version"]))

    # Wait for the ferium profile to be created
    await create_ferium_profile_task

    # Download the skin mod if online-mode is false
    if server_configuration["properties"]["online-mode"] == "false":
        await download_skin_mod(server_configuration["name"])

    # Wait for mods to be chosen
    while server_configuration["mods_config"] is None:
        await asyncio.sleep(1)

    # Read full configuration file
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "modpacks", server_configuration["mods_config"] + ".ini"), "r") as mods_config_file:
        mods_config = configparser.ConfigParser()
        mods_config.read_file(mods_config_file)
        server_configuration["mods_config"] = mods_config

    # Read dependencies
    read_dependencies_task = asyncio.create_task(read_dependencies(server_configuration["name"], server_path, server_configuration["mods_config"]))

    # Download the mods
    download_mods_task = asyncio.create_task(download_mods(server_configuration["name"], server_configuration["mods_config"]))

    # Copy the configuration files
    copy_configuration_files_task = asyncio.create_task(copy_configuration_files(server_path, server_configuration["mods_config"]))

    # Configure additional server properties
    additional_server_property_thread = threading.Thread(target=write_additional_server_properties, args=(server_path, server_configuration["properties"]))
    additional_server_property_thread.start()

    # Wait for the configuration files to be copied
    await copy_configuration_files_task

    # Wait for the mods to be downloaded
    await download_mods_task

    # Wait for the dependencies to be read
    await read_dependencies_task

    # Wait for the additional server properties to be written
    additional_server_property_thread.join()
    
    # All done, waiting for user to exit
    input("All done! Press enter to exit...")

asyncio.run(main())