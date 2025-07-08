# Anki Image Updater

A Python script that automatically adds images to Anki flashcards by searching DuckDuckGo Image Search and downloading relevant images for notes with empty image fields.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add your deck to `input/`:**
   ```bash
   cp your_deck.apkg input/
   ```

3. **Run the script:**
   ```bash
   python anki_image_updater.py input/your_deck.apkg --search-field answer
   ```

4. **Import to Anki:**
   Open `output/your_deck_updated.apkg` in Anki

## Features

- 📚 Reads Anki decks from CSV files and .apkg files
- 🔍 Searches DuckDuckGo Image Search for relevant images based on answer content
- 💾 Downloads and optimizes images locally
- 🎴 Creates new Anki deck files (.apkg) with embedded images
- ⚙️ Configurable field mappings and settings
- 🛡️ Error handling and graceful failure recovery
- 📝 Comprehensive logging

## Requirements

- Python 3.7 or higher
- Internet connection for image searches
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Place your deck file in the input/ directory first
python anki_image_updater.py input/your_deck.csv
```

### Advanced Usage

```bash
python anki_image_updater.py input/your_deck.apkg --deck-name "My Updated Deck" --search-field answer
```

### Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `input_file` | Path to your CSV or APKG file (required) | `input/my_deck.apkg` |
| `--deck-name` | Name for the output deck | `--deck-name "Vocabulary with Images"` |
| `--config` | Path to JSON configuration file (optional) | `--config my_config.json` |
| `--search-field` | Which field to use for image search | `--search-field answer` or `--search-field question` |

### Search Field Parameter Explained

The `--search-field` parameter determines which text the script uses to search for images:

- **`--search-field answer`** (default): Uses the answer text to find images
  - Good for: Vocabulary words, concepts, objects, places
  - Example: If answer is "Paris", searches for "Paris" images
  
- **`--search-field question`**: Uses the question text to find images
  - Good for: Questions about specific topics, when questions are more descriptive
  - Example: If question is "What is the capital of France?", searches for "capital of France" images

**Which should you choose?**
- Use `answer` if your answers are specific terms (e.g., "Jupiter", "Photosynthesis")
- Use `question` if your questions are more descriptive (e.g., "What is the largest planet in our solar system?")

## Input Directory

Place your Anki deck files in the `input/` directory for processing.

### Supported Formats
- **`.apkg`** - Anki package files (recommended)
- **`.csv`** - Comma-separated values files

### File Structure
```
input/
├── your_deck.apkg          # Your Anki deck file
├── another_deck.csv        # Your CSV deck file
└── sample_deck.csv         # Example file included
```

### Usage Examples
```bash
# Process an APKG file using answer field for image search
python anki_image_updater.py input/vocabulary.apkg --search-field answer

# Process a CSV file using question field for image search
python anki_image_updater.py input/study_notes.csv --search-field question

# Custom deck name
python anki_image_updater.py input/my_deck.apkg --deck-name "My Deck with Images"
```

### Examples
- `input/my_vocabulary.apkg`
- `input/study_notes.csv`
- `input/language_cards.apkg`

### Notes
- The script will create output files in the `output/` directory
- Downloaded images will be saved in `output/images/`
- Original files remain unchanged

## Output Directory

This directory contains all generated files from the Anki Image Updater.

### Generated Files
```
output/
├── your_deck_updated.apkg    # Updated Anki deck with images
├── images/                   # Downloaded images
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── anki_image_updater.log    # Processing log
```

### What Gets Created
- **Updated Anki decks** (`.apkg` files) - Ready to import into Anki
- **Downloaded images** - All images found and downloaded during processing
- **Log files** - Detailed processing information and error logs

### Usage
1. **Import to Anki**: Open the generated `.apkg` file in Anki
2. **Review images**: Check `images/` directory for downloaded images
3. **Check logs**: Review `anki_image_updater.log` for processing details

### Notes
- This directory is automatically created when you run the script
- Files are overwritten on subsequent runs
- Original input files remain unchanged
- All generated files are ready for use

## Input Format

### CSV Format

Your CSV file should have at least these columns:
- `Question`: The question text
- `Answer`: The answer text (used for image search)
- `Image`: Image field (can be empty)

Example:
```csv
Question,Answer,Image
"What is the capital of France?","Paris",
"What is the largest planet?","Jupiter",
```

### APKG Format

The script can read Anki .apkg files directly. Place your .apkg files in the `input/` directory for processing.

### Custom Field Names

If your CSV uses different column names, you can configure them in a JSON config file:

```json
{
    "question_field": "Front",
    "answer_field": "Back", 
    "image_field": "Picture"
}
```

## Configuration

Create a `config.json` file to customize the behavior:

```json
{
    "question_field": "Question",
    "answer_field": "Answer",
    "image_field": "Image",
    "output_dir": "output",
    "images_dir": "images",
    "delay_between_searches": 1.0,
    "max_image_size": [800, 600],
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

### Configuration Options

- `question_field`: Name of the question column in your CSV
- `answer_field`: Name of the answer column in your CSV  
- `image_field`: Name of the image column in your CSV
- `output_dir`: Directory for output files
- `images_dir`: Subdirectory for downloaded images
- `delay_between_searches`: Delay between searches (seconds) to be respectful to servers
- `max_image_size`: Maximum image dimensions [width, height]
- `user_agent`: User agent string for web requests

## How It Works

1. **Read Deck**: Parses your CSV or APKG file and validates required fields
2. **Process Notes**: For each note with an empty image field:
   - Searches DuckDuckGo Image Search using the specified field (question or answer)
   - Downloads the first relevant image found
   - Optimizes and resizes the image
   - Updates the note with the local image filename
3. **Create Deck**: Generates a new Anki deck file with all images embedded
4. **Logging**: Records all actions and errors for debugging

## Error Handling

The script handles various error conditions gracefully:

- **Network errors**: Continues with next note if image search/download fails
- **Invalid images**: Skips non-image files
- **Missing fields**: Logs warnings and continues
- **File permission issues**: Logs errors and stops gracefully

## Limitations

- **DuckDuckGo Search**: Uses DuckDuckGo Image Search scraping (no API key required)
- **Rate Limiting**: Includes delays between searches to be respectful
- **Image Quality**: Downloads first available image (no quality filtering)

## Troubleshooting

### Common Issues

1. **"No image found" warnings**: 
   - Check your internet connection
   - Try more specific answer text
   - DuckDuckGo may have changed their API structure

2. **Permission errors**:
   - Ensure write permissions in output directory
   - Check if files are open in other applications

3. **Import errors in Anki**:
   - Verify the generated .apkg file is complete
   - Check log file for any errors during processing

### Debugging

Check the log file `anki_image_updater.log` for detailed information about:
- Which notes were processed
- Image search results
- Download successes/failures
- Any errors encountered

## Legal and Ethical Considerations

- **Respectful Scraping**: The script includes delays between requests
- **Image Usage**: Downloaded images may be subject to copyright
- **Terms of Service**: Ensure compliance with DuckDuckGo's terms of service
- **Educational Use**: Intended for personal educational use only

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the script.

## License

This project is provided as-is for educational purposes. Use responsibly and in compliance with applicable laws and terms of service. 