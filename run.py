from app import create_app

# The factory keeps the same entry point usable by Flask's CLI and local runs.
app = create_app()


if __name__ == "__main__":
    app.run()
