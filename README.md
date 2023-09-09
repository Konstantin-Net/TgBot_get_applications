## **Instruction for Setting Up and Running the Telegram Bot**

This guide will help you set up and run a Telegram bot that utilizes Google Sheets for data storage and management.

### **Prerequisites:**
- Python environment.
- Google account.

### **Steps:**

#### **1. Clone the GitHub Repository**

First, clone the repository to your local machine:

```bash
git clone <repository_url>
```

Navigate to the directory:

```bash
cd <repository_name>
```

#### **2. Set Up Virtual Environment (Recommended)**


```bash
python -m venv venv
```

Activate it:

* On Windows:
```bash
.\venv\Scripts\activate
```

* On Linux/Mac:
```bash
source venv/bin/activate
```

#### **3. Install the Dependencies**

Install the necessary Python packages using `requirements.txt`:

```bash
pip install -r requirements.txt
```

#### **4. Google Sheets Setup**

##### **4.1 Create a New Google Sheet:**

1. Open [Google Sheets](https://sheets.google.com).
2. Click on `Blank` to create a new spreadsheet.
3. Name the first sheet `application` and the second sheet `admins`.

##### **4.2 Structure the Sheets:**

For the `application` sheet:
- Columns from A to H: `telegram_id`, `username`, `language`, `description`, `terms`, `budget`, `phone`, `date`.
- Cell J2: This will store the manager's contact.

For the `admins` sheet:
- Cell A2: This will store the admin's ID.

##### **4.3 Get Google Sheets API Credentials:**

1. Navigate to [Google Developers Console](https://console.developers.google.com/).
2. Create a new project.
3. Enable the Google Sheets API for the project.
4. Create service account credentials.
5. Download the `credentials.json` file.
6. Share your Google Sheet with the email address associated with the service account (found in the `credentials.json` file). Grant it "Editor" permissions.

#### **5. Configuration**

##### **5.1 `.env` File:**

Create a `.env` file in the root directory of the project. This file should be structured based on `.env.example`. Fill in the following:

- `TOKEN`: Your Telegram bot token (obtained from [@BotFather](https://t.me/botfather)).
- `CREDENTIALS_PATH`: Path to your `credentials.json` file.
- `SPREADSHEET_ID`: The ID of your Google Sheet (can be found in the URL of the sheet).

```plaintext
TOKEN=YOUR_TELEGRAM_BOT_TOKEN
CREDENTIALS_PATH=path/to/your/credentials.json
SPREADSHEET_ID=YOUR_GOOGLE_SHEET_ID
```

#### **6. Running the Bot**

Run the `main.py` file:

```bash
python main.py
```

Your bot should now be running and ready to receive messages!

### **Conclusion:**

With these steps completed, your Telegram bot is set up and integrated with Google Sheets. Whenever a user interacts with the bot, the data will be stored and managed in your Google Sheet. The bot also notifies the admin whenever a new application is filled out.