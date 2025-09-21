from app import create_app  # Import from app package

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
