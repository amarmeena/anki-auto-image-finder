@echo off
setlocal

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
python -m pip install -r requirements.txt

REM Copy config_example.json to config.json if not present
if not exist config.json (
    copy config_example.json config.json
    echo Created config.json from config_example.json.
)

echo.
echo Setup complete!
echo To activate the virtual environment, run:
echo     venv\Scripts\activate

echo To run the script on an APKG or CSV file, use:
echo     python anki_auto_image_finder.py <input_file> [--deck-name <name>] [--config config.json]
endlocal 