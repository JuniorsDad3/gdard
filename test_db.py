import pyodbc

server = "licensebookingsystem.database.windows.net"
database = "SA Drivers License Booking System"
username = "gerald.mandebvu"  # Corrected username
password = "Sgb3@1017"

try:
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};"
        f"UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;"
    )
    print("✅ Connection Successful!")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
