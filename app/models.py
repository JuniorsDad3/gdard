# app/models.py
import pandas as pd
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.excel_db import load_sheet, save_sheet
from pathlib import Path

EXCEL_FILE = Path(r"C:\Users\dell5348\gdard\GDARD.xlsx")

# A simple base to share load/save by sheet name
class ExcelModel:
    sheet_name: str  # override in subclasses

    @classmethod
    def _df(cls):
        return load_sheet(cls.sheet_name)

    @classmethod
    def _save_df(cls, df):
        save_sheet(cls.sheet_name, df)

    @classmethod
    def all(cls):
        return cls._df().to_dict(orient='records')

    @classmethod
    def find(cls, **kwargs):
        df = cls._df()
        for key, value in kwargs.items():
            df = df[df[key] == value]
        return df.to_dict(orient='records')

    @classmethod
    def get_by_id(cls, id):
        """Return the first matching row as a dict, or None."""
        rows = cls.find(id=id)
        return rows[0] if rows else None

    @classmethod
    def delete_by_id(cls, _id):
        df = cls._df()
        df = df[df.id != _id]
        cls._save_df(df)

    @classmethod
    def _next_id(cls):
        df = cls._df()
        return int(df.id.max() + 1) if not df.empty else 1

class User(UserMixin, ExcelModel):
    sheet_name = "Users"

    def __init__(self, **fields):
        for key, val in fields.items():
            setattr(self, key, val)

    @classmethod
    def find_by_email(cls, email):
        rows = cls.find()
        for row in rows:
            user = cls(**row)
            if user.email.lower() == email.lower():
                return user
        return None

    @classmethod
    def create(cls, username, email, password, user_type, farm_size=0, location="", phone="", avatar_url=""):
        df = cls._df()
        new = {
            "id": cls._next_id(),
            "username": username,
            "email": email,
            "password_hash": generate_password_hash(password),
            "user_type": user_type,
            "farm_size": farm_size,
            "location": location,
            "phone": phone,
            "avatar_url": avatar_url,
            "created_at": datetime.utcnow(),
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return cls(**new)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SupportProgram(ExcelModel):
    sheet_name = "SupportPrograms"

    @classmethod
    def create(cls, title, description, eligibility, deadline, application_link, max_funding):
        df = cls._df()
        new = {
            "id": cls._next_id(),
            "title": title,
            "description": description,
            "eligibility": eligibility,
            "deadline": deadline,
            "application_link": application_link,
            "max_funding": max_funding,
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return new


class FundingApplication(ExcelModel):
    sheet_name = "FundingApplications"

    @classmethod
    def create(cls, farmer_id, program_id, amount_requested, documents, notes=""):
        df = cls._df()
        new = {
            "id": cls._next_id(),
            "farmer_id": farmer_id,
            "program_id": program_id,
            "amount_requested": amount_requested,
            "status": "pending",
            "submitted_date": datetime.utcnow(),
            "documents": documents,
            "notes": notes,
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return new


class Permit(ExcelModel):
    sheet_name = "Permits"

    @classmethod
    def create(cls, permit_type, user_id, impact_assessment, issued_date=None, expiry_date=None):
        df = cls._df()
        new = {
            "id": cls._next_id(),
            "permit_type": permit_type,
            "status": "pending",
            "application_date": datetime.utcnow(),
            "issued_date": issued_date,
            "expiry_date": expiry_date,
            "impact_assessment": impact_assessment,
            "user_id": user_id,
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return new


class ComplianceCase(ExcelModel):
    sheet_name = "ComplianceCases"

    @classmethod
    def create(cls, farm_id, agent_id, issue_type, severity, description, due_date, documents):
        df = cls._df()
        new = {
            "id": cls._next_id(),
            "farm_id": farm_id,
            "agent_id": agent_id,
            "issue_type": issue_type,
            "severity": severity,
            "description": description,
            "due_date": due_date,
            "status": "open",
            "documents": documents,
            "created_at": datetime.utcnow(),
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return new


class SensorDevice(ExcelModel):
    sheet_name = "SensorDevices"

    @classmethod
    def create(cls, device_id, farm_id, sensor_type):
        df = cls._df()
        new = {
            "id":        cls._next_id(),
            "device_id": device_id,
            "farm_id":   farm_id,
            "sensor_type": sensor_type
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return new

class SensorReading(ExcelModel):
    sheet_name = "SensorReadings"

    @classmethod
    def create(cls, device_id, temperature, humidity, soil_moisture, user_id, timestamp=None):
        df = cls._df()
        new = {
            "id":           cls._next_id(),
            "device_id":    device_id,
            "timestamp":    timestamp or datetime.utcnow(),
            "temperature":  temperature,
            "humidity":     humidity,
            "soil_moisture":soil_moisture,
            "user_id":      user_id,
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return new

class ComplianceReport(ExcelModel):
    sheet_name = "ComplianceReports"

    @classmethod
    def create(cls, farm_id, inspection_date, status, report_url, findings, inspector_id):
        df = cls._df()
        new = {
            "id":              cls._next_id(),
            "farm_id":         farm_id,
            "inspection_date": inspection_date,
            "status":          status,
            "report_url":      report_url,
            "findings":        findings,
            "inspector_id":    inspector_id,
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return new

class FarmerTask(ExcelModel):
    sheet_name = "FarmerTasks"

    @classmethod
    def create(cls, farmer_id, title, description, due_date, completed=False):
        df = cls._df()
        new = {
            "id":         cls._next_id(),
            "farmer_id":  farmer_id,
            "title":      title,
            "description":description,
            "due_date":   due_date,
            "completed":  completed,
        }
        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        cls._save_df(df)
        return new

class Product(ExcelModel):
    sheet_name = "Products"

    def __init__(self, **fields):
        for key, val in fields.items():
            setattr(self, key, val)

class ExcelModel:
    sheet_name = None

    @classmethod
    def all(cls):
        df = load_sheet(cls.sheet_name)
        return df.to_dict(orient="records")
