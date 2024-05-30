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
- Ensures the configuration file is saved in all scenarios except when an `errors.ApiIdInvalidError` is raised.
- Handles invalid channel selection inputs by re-prompting the user to enter a valid channel number.
- Allows for previous session reuse to avoid repeated logins.

## Requirements

- Python 3.10.x recommended (feel free to try and test other Python versions)
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

2. Follow the prompts:

    - If previous sessions are found, you can choose to reuse a previous login or log in with a new number.
    - If logging in with a new number, enter your mobile number, API ID, and API hash. You can obtain these from [my.telegram.org](https://my.telegram.org).
    - Enter the name for your session. This will be used to save the session file.

3. After logging in:

    - Select the channel or group by its number from the listed channels/groups.
    - The script will list all media files available in the selected channel or group.
    - Enter the file IDs you want to download, `all` to download all files, or a range (e.g., `110-120`) to download specific files within that range.
    - Enter the download path where you want to save the files.
    - Enter the number of files to download concurrently (recommended: 4).
    - 
## Notes

- **Reusing Previous Login**: In case you have successfully logged in once using the script, the next time you start the script, you don't have to enter API details or your mobile number. You can simply select the previous login and start again.
- **Error Handling with Saved API Details**: The API details are saved so that in case of any error while logging in, such as entering the wrong mobile number or incorrect login code, you won't have to enter the API details again next time. You only have to enter your mobile number, and the script will look for the configuration details associated with that number.
- **Session File Management**: The Telethon library saves a session file (named as `mobile_number.session` where your mobile number is used to name the session file). This file allows you to start downloading files without logging in again if you have logged in successfully once. The script handles situations where the session file is created even if the login was unsuccessful, ensuring that the session file is only used if the login was successful.

## Script Details

- **API ID and API Hash**: The script requires your API ID and API hash, which can be obtained from [my.telegram.org](https://my.telegram.org). These are needed to authenticate your Telegram client.
- **Session Name**: The script will ask for a session name to save the session file. This allows you to reuse the session without needing to log in again.
- **Sanitizing Filenames**: The script sanitizes filenames to ensure they are valid on your file system.
- **Concurrent Downloads**: The script uses asyncio and semaphores to download multiple files concurrently.
- **Skip Existing Files**: If a file with the same name and size already exists locally, the script will skip downloading it again.
- **Configuration Handling**: The script ensures the configuration file is saved in all scenarios except when an `errors.ApiIdInvalidError` is raised.
- **Input Validation**: The script handles invalid inputs for channel selection and file ID selections by re-prompting the user.

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
