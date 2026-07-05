# Credentials Folder

Place your **Google Service Account JSON key file** here.

## Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the **Google Sheets API** and **Google Drive API**.
3. Create a **Service Account** and download the JSON key.
4. Save the file as `service-account.json` in this folder.
5. Share your target Google Sheet with the service account email (found in the JSON as `client_email`).

## Security

- **Do not** upload `service-account.json` to Google Drive, GitHub, or any public location.
- **Do not** commit this file to version control (it is listed in `.gitignore`).
- When sharing the project folder, exclude this directory or use a placeholder file only.
