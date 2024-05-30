import os
import re
import json
import time
import asyncio
from tqdm import tqdm
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename

# Constants
CONFIG_DIR = "configurations"
SESSION_DIR = "sessions"

# Create directories if they don't exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

# Function to save API credentials to a configuration file
def save_config(mobile_number, api_id, api_hash):
    config_path = os.path.join(CONFIG_DIR, f"{mobile_number}.json")
    config_data = {
        "api_id": api_id,
        "api_hash": api_hash
    }
    with open(config_path, 'w') as config_file:
        json.dump(config_data, config_file)

# Function to load API credentials from a configuration file
def load_config(mobile_number):
    config_path = os.path.join(CONFIG_DIR, f"{mobile_number}.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    return None

# Function to sanitize filenames
def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', filename)

# Function to download a file
async def download_file(client, message_id, original_file_name, channel, semaphore, download_path):
    async with semaphore:
        try:
            sanitized_file_name = sanitize_filename(original_file_name)
            file_name, file_extension = os.path.splitext(sanitized_file_name)
            unique_file_name = f"{file_name}_{message_id}{file_extension}"
            local_file_path = os.path.join(download_path, unique_file_name)

            if os.path.exists(local_file_path):
                local_file_size = os.path.getsize(local_file_path)
                remote_file_size = await client.get_messages(channel, ids=message_id)
                remote_file_size = remote_file_size.file.size
                if local_file_size == remote_file_size:
                    print(f"Skipping download, local file {unique_file_name} is the same size as remote file.")
                    return

            message = await client.get_messages(channel, ids=message_id)
            progress = tqdm(total=100, desc=f"Downloading {unique_file_name}")
            path = await message.download_media(file=local_file_path, progress_callback=lambda d, t: progress.update((d / t) * 100 - progress.n))
            progress.close()
            print(f'Downloaded {unique_file_name} to {path}')

            time_difference = progress.last_print_t - progress.start_t
            if time_difference > 0:
                size_in_bytes = os.path.getsize(path)
                speed = size_in_bytes / time_difference
                print(f'Completed {unique_file_name}. Speed: {speed / 1024:.2f} KB/s')
            else:
                print(f'Completed {unique_file_name}. Download was too fast to measure speed.')
        except Exception as e:
            print(f"Error downloading file {unique_file_name}: {e}")

# Function to list and download files
async def list_and_download_files(client):
    await client.start()
    print("\nClient Created - Listing all channels and groups\n")

    try:
        dialogs = await client.get_dialogs()
        channels = [d for d in dialogs if d.is_channel or d.is_group]

        if not channels:
            print("No channels or groups found.")
            return

        for i, channel in enumerate(channels, 1):
            print(f"{i}. {channel.name}")

        while True:
            try:
                channel_index = int(input("\nSelect a channel or group by number: ")) - 1
                if channel_index < 0 or channel_index >= len(channels):
                    print("Invalid selection. Please enter a valid channel number.")
                else:
                    break
            except ValueError:
                print("Invalid input. Please enter a number.")

        channel = channels[channel_index]
        print(f"Selected channel: {channel.name}\n")

        files = []
        total_size_bytes = 0
        offset_id = 0
        limit = 100

        while True:
            history = await client(GetHistoryRequest(
                peer=channel.entity,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))
            if not history.messages:
                break

            for message in history.messages:
                if message.media and isinstance(message.media, MessageMediaDocument):
                    file_name = "Unknown"
                    file_size = message.media.document.size
                    for attribute in message.media.document.attributes:
                        if isinstance(attribute, DocumentAttributeFilename):
                            file_name = attribute.file_name
                            break
                    files.append((message.id, file_name, message.date, file_size))
                    total_size_bytes += file_size

            offset_id = history.messages[-1].id

        for file in files:
            print(f"ID: {file[0]}, Name: {file[1]}, Date: {file[2]}")

        print(f"\nTotal number of files found: {len(files)}")
        
        total_size_mb = total_size_bytes / (1024 * 1024)
        total_size_gb = total_size_mb / 1024
        print(f"Total size: {total_size_mb:.2f} MB ({total_size_gb:.2f} GB)")

        while True:
            file_ids_input = input("\nEnter 'all' to download all files, provide the IDs of the files to download (comma-separated), or a range (e.g., 110-120): ")
            if file_ids_input.lower() == 'all':
                file_ids = [file[0] for file in files]
                selected_files = files
                break
            elif '-' in file_ids_input:
                range_start, range_end = map(int, file_ids_input.split('-'))
                file_ids = [file_id for file_id in range(range_start, range_end + 1)]
                selected_files = [file for file in files if file[0] in file_ids]
                break
            else:
                try:
                    file_ids = [int(fid.strip()) for fid in file_ids_input.split(',')]
                    selected_files = [file for file in files if file[0] in file_ids]
                    non_existent_ids = [fid for fid in file_ids if not any(file[0] == fid for file in files)]
                    if non_existent_ids:
                        print(f"The following file IDs are not present: {', '.join(map(str, non_existent_ids))}")
                    else:
                        break
                except ValueError:
                    print("Invalid input. Please enter valid file IDs.")

        total_selected_size_bytes = sum(file[3] for file in selected_files)
        total_selected_size_mb = total_selected_size_bytes / (1024 * 1024)
        total_selected_size_gb = total_selected_size_mb / 1024

        print(f"\nTotal number of files to download: {len(selected_files)}")
        print(f"\nTotal size of download: {total_selected_size_mb:.2f} MB ({total_selected_size_gb:.2f} GB)\n")

        while True:
            try:
                concurrency_limit = int(input("Enter the number of files to download concurrently (4 is recommended): "))
                if concurrency_limit < 1:
                    print("Concurrency limit must be at least 1.")
                else:
                    break
            except ValueError:
                print("Invalid input. Please enter a number.")

        download_path = input("\nEnter the download path: ").strip().strip('\'"')
        print()
        os.makedirs(download_path, exist_ok=True)

        semaphore = asyncio.Semaphore(concurrency_limit)

        start_time = time.time()
        tasks = [download_file(client, selected_file[0], selected_file[1], channel.entity, semaphore, download_path)
                 for selected_file in selected_files]
        await asyncio.gather(*tasks)
        end_time = time.time()

        total_time_taken = end_time - start_time
        print(f"\nTotal files downloaded: {len(selected_files)}")
        print(f"Total data downloaded: {total_selected_size_mb:.2f} MB ({total_selected_size_gb:.2f} GB)")
        print(f"Total time taken: {total_time_taken:.2f} seconds")

    except Exception as e:
        print(f"Error accessing channel or downloading files: {e}")

# Function to start the client with the stored configuration
async def start_client(mobile_number):
    config = load_config(mobile_number)
    if config:
        api_id = config["api_id"]
        api_hash = config["api_hash"]
        session_path = os.path.join(SESSION_DIR, mobile_number)
        client = TelegramClient(session_path, api_id, api_hash)
        try:
            await client.start()
        except errors.SessionPasswordNeededError:
            password = input("Two-step verification is enabled. Please enter your password: ")
            await client.sign_in(password=password)
        except Exception as e:
            print(f"An error occurred: {e}")
            await client.disconnect()
            os.remove(session_path + ".session")
            raise e
        return client
    else:
        print("Configuration not found for this mobile number.")
        return None

# Function to handle login and validation of API credentials
async def validate_and_save_config(mobile_number, api_id, api_hash):
    # Ensure api_id is a positive integer
    while True:
        if isinstance(api_id, str):
            api_id = api_id.strip()
            if not api_id:
                api_id = input("API ID cannot be left blank. Please enter your API ID: ").strip()
            else:
                try:
                    api_id = int(api_id)
                    if api_id <= 0:
                        print("Invalid API ID. It must be a positive integer.")
                    else:
                        break
                except ValueError:
                    print("API ID cannot contain alphabets. Please enter a valid API ID.")
        elif isinstance(api_id, int):
            if api_id <= 0:
                print("Invalid API ID. It must be a positive integer.")
                api_id = input("Please enter your API ID: ").strip()
                continue
            break

    # Ensure api_hash is a non-empty string
    while not api_hash:
        api_hash = input("API hash cannot be left blank. Please enter your API hash: ").strip()

    session_path = os.path.join(SESSION_DIR, mobile_number)
    client = TelegramClient(session_path, api_id, api_hash)
    try:
        await client.start()
        save_config(mobile_number, api_id, api_hash)
        return client
    except errors.ApiIdInvalidError:
        print("Invalid API ID or API hash.")
        await client.disconnect()
        os.remove(session_path + ".session")
        return None
    except errors.SessionPasswordNeededError:
        password = input("Two-step verification is enabled. Please enter your password: ")
        await client.sign_in(password=password)
        save_config(mobile_number, api_id, api_hash)
        return client
    except Exception as e:
        print(f"An error occurred: {e}")
        save_config(mobile_number, api_id, api_hash)
        await client.disconnect()
        os.remove(session_path + ".session")
        return None

# Main function to handle user inputs and sessions
async def main():
    session_files = [f for f in os.listdir(SESSION_DIR) if f.endswith('.session')]

    if session_files:
        print("Previous logins found.")
        print("1. Use previous login\n2. Login with new number")
        use_previous = input("\nSelect an option (1/2): ").strip()
        print()

        if use_previous == '1':
            print("Available sessions:")
            for i, session_file in enumerate(session_files, 1):
                print(f"{i}. {session_file[:-8]}")

            while True:
                try:
                    session_index = int(input("\nSelect a session by number: ")) - 1
                    if session_index < 0 or session_index >= len(session_files):
                        print("Invalid selection. Please enter a valid session number.")
                    else:
                        mobile_number = session_files[session_index][:-8]
                        client = await start_client(mobile_number)
                        if client:
                            break
                        else:
                            print("Failed to start client. Check configuration.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            while True:
                mobile_number = input("Enter your mobile number (with + sign if applicable): ").strip()
                print(mobile_number)
                if not mobile_number:
                    print("Mobile number cannot be blank. Please enter your mobile number.")
                elif not re.match(r'^\+\d+$', mobile_number):
                    print("Invalid mobile number. Please enter a valid mobile number.")
                else:
                    break

            # Check if configuration exists for the entered mobile number
            config = load_config(mobile_number)
            if config:
                api_id = config["api_id"]
                api_hash = config["api_hash"]
                print(f"Found configuration for {mobile_number}.")
                print(f"Using API ID: {api_id} and API Hash: {api_hash}.")
                client = await validate_and_save_config(mobile_number, api_id, api_hash)
                if not client:
                    print("Failed to start client. Please check your API credentials.")
            else:
                while True:
                    api_id = input("Enter your API ID: ").strip()
                    if not api_id:
                        print("API ID cannot be left blank. Please enter your API ID.")
                    else:
                        try:
                            api_id = int(api_id)
                            if api_id > 0:
                                break
                            else:
                                print("Invalid API ID. It must be a positive integer.")
                        except ValueError:
                            print("API ID cannot contain alphabets. Please enter a valid API ID.")
                api_hash = ""
                while not api_hash:
                    api_hash = input("Enter your API hash: ").strip()
                    if not api_hash:
                        print("API hash cannot be left blank. Please try again.")
                client = await validate_and_save_config(mobile_number, api_id, api_hash)
                if not client:
                    print("Failed to start client. Please check your API credentials.")
    else:
        while True:
            mobile_number = input("Enter your mobile number (with + sign if applicable): ").strip()
            if not mobile_number:
                print("Mobile number cannot be blank. Please enter your mobile number.")
            elif not re.match(r'^\+\d+$', mobile_number):
                print("Invalid mobile number. Please enter a valid mobile number.")
            else:
                break

        # Check if configuration exists for the entered mobile number
        config = load_config(mobile_number)
        if config:
            api_id = config["api_id"]
            api_hash = config["api_hash"]
            print(f"Found configuration for {mobile_number}.")
            print(f"Using API ID: {api_id} and API Hash: {api_hash}.")
            client = await validate_and_save_config(mobile_number, api_id, api_hash)
            if not client:
                print("Failed to start client. Please check your API credentials.")
        else:
            while True:
                api_id = input("Enter your API ID: ").strip()
                if not api_id:
                    print("API ID cannot be left blank. Please enter your API ID.")
                else:
                    try:
                        api_id = int(api_id)
                        if api_id > 0:
                            break
                        else:
                            print("Invalid API ID. It must be a positive integer.")
                    except ValueError:
                        print("API ID cannot contain alphabets. Please enter a valid API ID.")
            api_hash = ""
            while not api_hash:
                api_hash = input("Enter your API hash: ").strip()
                if not api_hash:
                    print("API hash cannot be left blank. Please try again.")
            client = await validate_and_save_config(mobile_number, api_id, api_hash)
            if not client:
                print("Failed to start client. Please check your API credentials.")

    if client:
        async with client:
            await list_and_download_files(client)

if __name__ == "__main__":
    asyncio.run(main())
