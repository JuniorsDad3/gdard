# app/excel_db.py

import pandas as pd
from pathlib import Path
from flask import current_app

def _get_excel_path() -> Path:
    return Path(current_app.config['EXCEL_DB_PATH'])

def load_sheet(sheet_name: str) -> pd.DataFrame:
    path = _get_excel_path()
    try:
        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
    except (FileNotFoundError, ValueError):
        # workbook or sheet doesn’t exist yet
        return pd.DataFrame()

def save_sheet(sheet_name: str, df: pd.DataFrame) -> None:
    path = _get_excel_path()
    # ensure directory
    path.parent.mkdir(parents=True, exist_ok=True)
    # write (creates file or replaces sheet)
    with pd.ExcelWriter(path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
