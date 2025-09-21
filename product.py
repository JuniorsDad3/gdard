import pandas as pd

# Path to create the Excel file
file_path = r"C:\Users\dell5348\gdard\GDARD.xlsx"

# Sample product data
products_data = {
    "Name": ["Maize Seeds", "Fertilizer X"],
    "Price": [50, 120],
    "Category": ["Agriculture", "Chemicals"]
}

# Create a DataFrame
df = pd.DataFrame(products_data)

# Write to Excel with a sheet named 'Products'
df.to_excel(file_path, sheet_name='Products', index=False)

print("Excel file created with 'Products' sheet at:", file_path)
