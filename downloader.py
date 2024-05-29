import os
from tqdm import tqdm
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageMediaDocument, DocumentAttributeFilename
import asyncio
import re

# Function to sanitize filenames
def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', filename)

# Function to download a file
async def download_file(message_id, original_file_name, channel, semaphore, download_path):
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
async def list_and_download_files():
    await client.start()
    print("Client Created - Listing all channels and groups")

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

        download_path = input("Enter the download path: ").strip().strip('\'"')
        os.makedirs(download_path, exist_ok=True)

        semaphore = asyncio.Semaphore(4)
        tasks = [download_file(selected_file[0], selected_file[1], channel.entity, semaphore, download_path)
                 for selected_file in selected_files]
        await asyncio.gather(*tasks)

    except Exception as e:
        print(f"Error accessing channel or downloading files: {e}")

if __name__ == "__main__":
    api_id = input("Enter your API ID: ").strip()
    api_hash = input("Enter your API hash: ").strip()
    session_name = input("Enter a name for your session: ").strip()

    client = TelegramClient(session_name, api_id, api_hash)
    
    with client:
        client.loop.run_until_complete(list_and_download_files())
