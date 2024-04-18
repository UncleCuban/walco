import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

CREDS_FILE_PATH = os.getenv("CREDS_FILE_PATH")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(CREDS_FILE_PATH, scopes=SCOPES)
client = gspread.authorize(creds)

def append_to_file(file_id, sheet_name, *args):
    try:
        sheet = client.open_by_key(file_id).worksheet(sheet_name)
        sheet.append_row([*args])
        print("Data appended successfuly")
        return True
    except Exception as e:
        print(f"Error appending data to Google Drive: {type(e).__name__}, {e}")
        return False
    
def get_user_ids(file_id, sheet_name):
    sheet = client.open_by_key(file_id).worksheet(sheet_name)
    current_user_ids = sheet.col_values(3)
    return current_user_ids

def get_current_wallets(file_id, sheet_name):
    sheet = client.open_by_key(file_id).worksheet(sheet_name)
    current_wallets_submitted = sheet.col_values(2)
    return current_wallets_submitted

def find_user_on_file(file_id, sheet_name, user_id):
    try:
        sheet = client.open_by_key(file_id).worksheet(sheet_name)
        user_ids = sheet.col_values(3)
        row_number = user_ids.index(user_id) + 1
        row_data = sheet.row_values(row_number)
        return row_data
    except Exception as e:
        print(f"Error finding user data: {type(e).__name__}, {e}")
        return False
    
def update_user_wallet(file_id, sheet_name, user_id, new_wallet):
    try:
        sheet = client.open_by_key(file_id).worksheet(sheet_name)
        user_ids = sheet.col_values(3)  # Assuming the user_id is stored in the third column
        if user_id in user_ids:
            row_number = user_ids.index(user_id) + 1
            sheet.update_cell(row_number, 2, new_wallet)  # Assuming the wallet is stored in the second column
            return True
        return False
    except Exception as e:
        print(f"Error updating wallet in file: {e}")
        return False