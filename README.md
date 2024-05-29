# Telegram File Downloader

This repository contains a script to download files from Telegram channels and groups. The script uses the Telethon library to interact with the Telegram API, allowing users to list and download media files from their selected channels or groups.

## Features

- Lists all channels and groups the user is a member of.
- Allows the user to select a channel or group to download files from.
- Lists all media files available in the selected channel or group.
- Allows the user to select specific files, a range of files, or all files to download.
- Downloads selected files concurrently.
- Skips downloading files that already exist locally with the same size.
- Provides download speed information.

## Requirements

- Python 3.10.x recommended (feel free to try and test other python versions)
- Telethon library
- tqdm library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/telegram-file-downloader.git
    cd telegram-file-downloader
    ```

2. Install the required libraries:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the script:
    ```sh
    python downloader.py
    ```

2. When prompted, enter your Telegram API ID and API hash. You can obtain these from [my.telegram.org](https://my.telegram.org).

3. Enter a name for your session. This will be used to save the session file.

4. Select the channel or group by its number from the listed channels/groups.

5. Enter the file IDs you want to download, or enter `all` to download all files, or enter a range (e.g., `110-120`) to download specific files within that range.

6. Enter the download path where you want to save the files.

## Script Details

- **API ID and API Hash**: The script requires your API ID and API hash, which can be obtained from [my.telegram.org](https://my.telegram.org). These are needed to authenticate your Telegram client.
- **Session Name**: The script will ask for a session name to save the session file. This allows you to reuse the session without needing to log in again.
- **Sanitizing Filenames**: The script sanitizes filenames to ensure they are valid on your file system.
- **Concurrent Downloads**: The script uses asyncio and semaphores to download multiple files concurrently.
- **Skip Existing Files**: If a file with the same name and size already exists locally, the script will skip downloading it again.

## Credits

This script is built using the [Telethon](https://github.com/LonamiWebs/Telethon) library. Telethon is a Python library to interact with Telegram's API to build custom Telegram clients.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read the [CONTRIBUTING](CONTRIBUTING.md) file for more information.

## Issues

If you encounter any issues or have any questions, please open an issue on this repository.

---

Feel free to customize this description further to fit your needs.
