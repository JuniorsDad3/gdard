# app/excel_db.py

import pandas as pd
from pathlib import Path

# Point to your single Excel workbook
EXCEL_FILE = Path(r"C:\Users\dell5348\gdard\GDARD.xlsx")
print(pd.ExcelFile(EXCEL_FILE).sheet_names)

def load_sheet(sheet_name: str) -> pd.DataFrame:
    """
    Load a sheet into a DataFrame. 
    If the file or sheet doesn't exist yet, returns an empty DataFrame.
    """
    try:
        return pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, engine="openpyxl")
    except (FileNotFoundError, ValueError):
        # Either the file doesn't exist, or the sheet isn't there yet
        return pd.DataFrame()

def save_sheet(sheet_name: str, df: pd.DataFrame) -> None:
    """
    Write a DataFrame back to the workbook. 
    Replaces the sheet if it already exists.
    """
    # Ensure the directory exists
    EXCEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Append-or-replace mode
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
