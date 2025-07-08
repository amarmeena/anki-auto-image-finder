#!/usr/bin/env python3
"""
Anki Image Updater

This script reads an Anki deck (either .apkg or CSV format) and automatically
adds images to notes that have empty image fields by searching Bing Image Search.

Requirements:
- requests: For HTTP requests and image downloads
- beautifulsoup4: For HTML parsing
- genanki: For creating Anki deck files
- Pillow: For image processing
- pandas: For CSV handling
"""

import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Third-party imports
import requests
from bs4 import BeautifulSoup
import genanki
import pandas as pd
from PIL import Image
import io
from duckduckgo_search import DDGS
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('anki_image_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AnkiImageUpdater:
    """Main class for updating Anki decks with images."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize the Anki Image Updater.
        
        Args:
            config: Configuration dictionary with field mappings and settings
        """
        self.config = config or {
            'question_field': 'Question',
            'answer_field': 'Answer', 
            'image_field': 'Image',
            'output_dir': 'output',
            'images_dir': 'images',
            'delay_between_searches': 1.0,  # seconds
            'max_image_size': (800, 600),   # width, height
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'search_field': 'answer'  # 'question' or 'answer' - which field to use for image search
        }
        
        # Create output directories
        self.output_path = Path(self.config['output_dir'])
        self.images_path = self.output_path / self.config['images_dir']
        self.output_path.mkdir(exist_ok=True)
        self.images_path.mkdir(exist_ok=True)
        
        # Initialize Anki model
        self.model = self._create_anki_model()
        
    def _create_anki_model(self) -> genanki.Model:
        """Create an Anki model for cards with images."""
        return genanki.Model(
            1607392319,  # Random model ID
            'Image Model',
            fields=[
                {'name': self.config['question_field']},
                {'name': self.config['answer_field']},
                {'name': self.config['image_field']}
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': f'<div class="question">{{{{{self.config["question_field"]}}}}}</div>',
                    'afmt': f'''<div class="question">{{{{{self.config["question_field"]}}}}}</div>
                               <hr id="answer">
                               <div class="answer">{{{{{self.config["answer_field"]}}}}}</div>
                               {{#{{{self.config["image_field"]}}}}}
                               <div class="image"><img src="{{{{{self.config["image_field"]}}}}}"></div>
                               {{/{{{self.config["image_field"]}}}}}'''
                }
            ]
        )
    
    def read_csv_deck(self, csv_path: str) -> List[Dict]:
        """
        Read notes from a CSV file.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            List of dictionaries representing notes
        """
        logger.info(f"Reading CSV deck from {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            required_fields = [self.config['question_field'], self.config['answer_field']]
            
            # Check if required fields exist
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Convert DataFrame to list of dictionaries
            notes = df.to_dict('records')
            logger.info(f"Successfully read {len(notes)} notes from CSV")
            return notes
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise
    
    def read_apkg_deck(self, apkg_path: str) -> List[Dict]:
        """
        Read notes from an Anki .apkg file.
        
        Args:
            apkg_path: Path to the .apkg file
            
        Returns:
            List of dictionaries representing notes
        """
        import zipfile
        import sqlite3
        import tempfile
        import os
        
        logger.info(f"Reading APKG deck from {apkg_path}")
        
        try:
            # Extract the .apkg file (it's a ZIP archive)
            with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
                # Create a temporary directory for extraction
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    # Look for the collection.anki2 file (SQLite database)
                    collection_path = os.path.join(temp_dir, 'collection.anki2')
                    if not os.path.exists(collection_path):
                        raise FileNotFoundError("collection.anki2 not found in APKG file")
                    
                    # Connect to the SQLite database
                    conn = sqlite3.connect(collection_path)
                    cursor = conn.cursor()
                    
                    # First, let's see what tables exist
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]
                    logger.info(f"Available tables: {tables}")
                    
                    # Get the notes from the database
                    cursor.execute("SELECT flds, tags FROM notes LIMIT 1000")
                    
                    rows = cursor.fetchall()
                    conn.close()
                    
                    if not rows:
                        logger.warning("No notes found in APKG file")
                        return []
                    
                    # Parse the notes
                    notes = []
                    for row in rows:
                        flds, tags = row
                        
                        # Split fields (Anki uses 0x1f as field separator)
                        fields = flds.split('\x1f')
                        
                        # Create note dictionary
                        note = {
                            'tags': tags
                        }
                        
                        # Map fields based on common Anki models
                        if len(fields) >= 2:
                            note[self.config['question_field']] = fields[0] if len(fields) > 0 else ''
                            note[self.config['answer_field']] = fields[1] if len(fields) > 1 else ''
                            note[self.config['image_field']] = fields[2] if len(fields) > 2 else ''
                        else:
                            # If we have fewer fields, just use what we have
                            note[self.config['question_field']] = fields[0] if len(fields) > 0 else ''
                            note[self.config['answer_field']] = fields[0] if len(fields) > 0 else ''  # Use same as question if only one field
                            note[self.config['image_field']] = ''
                        
                        notes.append(note)
                    
                    logger.info(f"Successfully read {len(notes)} notes from APKG")
                    return notes
                    
        except Exception as e:
            logger.error(f"Error reading APKG file: {e}")
            raise
    
    def search_duckduckgo_images(self, query: str) -> Optional[str]:
        """
        Search DuckDuckGo Images for a query and return the first image URL using duckduckgo-search library (DDGS().images).
        Args:
            query: Search query string
        Returns:
            URL of the first image found, or None if no image found
        """
        try:
            # Clean up the query: remove HTML entities, sound tags, etc.
            clean_query = html.unescape(query)
            clean_query = clean_query.split('[sound:')[0].strip()
            clean_query = clean_query.replace('\xa0', ' ').replace('&nbsp;', ' ')
            # Use DDGS().images from duckduckgo-search
            logger.info(f"Searching DuckDuckGo Images (DDGS) for query: {clean_query}")
            with DDGS() as ddgs:
                results = ddgs.images(clean_query, max_results=1, safesearch='Moderate')
                for result in results:
                    image_url = result.get('image')
                    if image_url:
                        logger.info(f"Found DuckDuckGo image URL: {image_url}")
                        return image_url
            logger.warning(f"No DuckDuckGo image found for query: {clean_query}")
            return None
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo images (DDGS): {e}")
            return None
    
    def download_image(self, image_url: str, filename: str) -> Optional[str]:
        """
        Download an image from URL and save it locally.
        
        Args:
            image_url: URL of the image to download
            filename: Local filename to save the image as
            
        Returns:
            Local path to the downloaded image, or None if download failed
        """
        try:
            logger.info(f"Downloading image from {image_url}")
            
            # Set headers for image download
            headers = {
                'User-Agent': self.config['user_agent'],
                'Referer': 'https://www.bing.com/',
            }
            
            # Download the image
            response = requests.get(image_url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not point to an image: {content_type}")
                return None
            
            # Save the image
            image_path = self.images_path / filename
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Process the image (resize if needed)
            self._process_image(image_path)
            
            logger.info(f"Successfully downloaded image to {image_path}")
            return str(image_path)
            
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None
    
    def _process_image(self, image_path: Path):
        """
        Process downloaded image (resize, optimize, etc.).
        
        Args:
            image_path: Path to the image file
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                max_width, max_height = self.config['max_image_size']
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    img.save(image_path, 'JPEG', quality=85, optimize=True)
                    logger.info(f"Resized image to {img.width}x{img.height}")
                    
        except Exception as e:
            logger.warning(f"Error processing image {image_path}: {e}")
    
    def generate_filename(self, query: str, index: int) -> str:
        """
        Generate a safe filename for an image based on the search query.
        
        Args:
            query: Search query used to find the image
            index: Index number to ensure uniqueness
            
        Returns:
            Safe filename with extension
        """
        # Clean the query for filename
        safe_query = re.sub(r'[^\w\s-]', '', query.lower())
        safe_query = re.sub(r'[-\s]+', '-', safe_query)
        safe_query = safe_query[:50]  # Limit length
        
        return f"{safe_query}-{index}.jpg"
    
    def update_notes_with_images(self, notes: List[Dict]) -> List[Dict]:
        """
        Update notes by adding images where the image field is empty.
        
        Args:
            notes: List of note dictionaries
            
        Returns:
            Updated list of notes with image paths
        """
        logger.info(f"Processing {len(notes)} notes for image updates")
        
        updated_notes = []
        image_count = 0
        added_images_info = []  # Track which questions got images, their answers, and URLs
        
        for i, note in enumerate(notes):
            logger.info(f"Processing note {i+1}/{len(notes)}")
            
            # Check if image field is empty
            image_field = self.config['image_field']
            current_image = note.get(image_field, '')
            # Handle NaN values from pandas
            if current_image is None or (isinstance(current_image, float) and str(current_image) == 'nan'):
                current_image = ''
            else:
                current_image = str(current_image).strip()
            
            if not current_image:
                # Determine which field to use for search based on configuration
                search_field = self.config.get('search_field', 'answer')
                if search_field == 'question':
                    search_text = note.get(self.config['question_field'], '')
                    field_name = 'question'
                else:  # default to answer
                    search_text = note.get(self.config['answer_field'], '')
                    field_name = 'answer'
                
                # Handle NaN values from pandas
                if search_text is None or (isinstance(search_text, float) and str(search_text) == 'nan'):
                    search_text = ''
                else:
                    search_text = str(search_text)
                
                if search_text:
                    # Extract first part from bullet-separated list if it's an answer
                    if field_name == 'answer':
                        # Split by bullet points and take the first non-empty part
                        text_parts = [part.strip() for part in search_text.split('▪') if part.strip()]
                        search_query_text = text_parts[0] if text_parts else search_text
                    else:
                        # For questions, use the full text
                        search_query_text = search_text
                    
                    # Add delay to be respectful to the search engine
                    if i > 0:
                        time.sleep(self.config['delay_between_searches'])
                    
                    # Construct DuckDuckGo search URL
                    search_query = urllib.parse.quote(search_query_text)
                    search_url = f"https://duckduckgo.com/?q={search_query}&t=h_&iar=images&iax=images&ia=images"
                    # Search for image
                    image_url = self.search_duckduckgo_images(search_query_text)
                    
                    if image_url:
                        # Generate filename and download image
                        filename = self.generate_filename(search_query_text, image_count)
                        local_path = self.download_image(image_url, filename)
                        
                        if local_path:
                            # Update the note with the local image path
                            note[image_field] = filename  # Use relative path for Anki
                            image_count += 1
                            added_images_info.append({
                                'question': note.get(self.config['question_field'], ''),
                                'answer': note.get(self.config['answer_field'], ''),
                                'search_field': field_name,
                                'search_text': search_query_text,
                                'search_url': search_url,
                                'image_url': image_url
                            })
                            logger.info(f"Added image to note: {filename}")
                        else:
                            logger.warning(f"Failed to download image for note {i+1}")
                    else:
                        logger.warning(f"No image found for note {i+1}")
                else:
                    logger.warning(f"Empty {field_name} field for note {i+1}")
            else:
                logger.info(f"Note {i+1} already has an image: {current_image}")
            
            updated_notes.append(note)
        
        logger.info(f"Successfully added {image_count} images to notes")
        # Print summary of added images
        print(f"\nImages added: {image_count}")
        if added_images_info:
            print("Questions that received new images (with search field, search text, search URL, and image URL):")
            for info in added_images_info:
                print(f"- Question: {info['question']}")
                print(f"  Full answer: {info['answer']}")
                print(f"  Search field used: {info['search_field']}")
                print(f"  Text used for DuckDuckGo search: {info['search_text']}")
                print(f"  DuckDuckGo search URL: {info['search_url']}")
                print(f"  Image URL: {info['image_url']}")
        else:
            print("No new images were added.")
        return updated_notes
    
    def create_anki_deck(self, notes: List[Dict], deck_name: str) -> str:
        """
        Create an Anki deck file (.apkg) from the updated notes.
        
        Args:
            notes: List of note dictionaries
            deck_name: Name for the Anki deck
            
        Returns:
            Path to the created .apkg file
        """
        logger.info(f"Creating Anki deck: {deck_name}")
        
        # Create deck
        deck = genanki.Deck(
            2059400110,  # Random deck ID
            deck_name
        )
        
        # Add notes to deck
        for note_data in notes:
            # Create note fields
            fields = [
                str(note_data.get(self.config['question_field'], '') or ''),
                str(note_data.get(self.config['answer_field'], '') or ''),
                str(note_data.get(self.config['image_field'], '') or '')
            ]
            
            # Create note
            note = genanki.Note(
                model=self.model,
                fields=fields
            )
            
            deck.add_note(note)
        
        # Add media files (images)
        media_files = []
        for image_file in self.images_path.glob('*.jpg'):
            media_files.append(str(image_file))
        
        # Create package
        package = genanki.Package(deck)
        package.media_files = media_files
        
        # Save deck
        output_file = self.output_path / f"{deck_name}.apkg"
        package.write_to_file(str(output_file))
        
        logger.info(f"Successfully created Anki deck: {output_file}")
        return str(output_file)
    
    def process_deck(self, input_path: str, deck_name: str = "Updated Deck") -> str:
        """
        Main method to process an entire deck.
        
        Args:
            input_path: Path to input file (.csv or .apkg)
            deck_name: Name for the output deck
            
        Returns:
            Path to the created .apkg file
        """
        logger.info(f"Starting deck processing: {input_path}")
        
        # Read the deck
        if input_path.lower().endswith('.csv'):
            notes = self.read_csv_deck(input_path)
        elif input_path.lower().endswith('.apkg'):
            notes = self.read_apkg_deck(input_path)
        else:
            raise ValueError("Input file must be .csv or .apkg")
        
        # Update notes with images
        updated_notes = self.update_notes_with_images(notes)
        
        # Create the new Anki deck
        output_path = self.create_anki_deck(updated_notes, deck_name)
        
        logger.info(f"Deck processing completed. Output: {output_path}")
        return output_path


def main():
    """Main function to run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Anki deck with images from Bing search')
    parser.add_argument('input_file', help='Path to input CSV or APKG file')
    parser.add_argument('--deck-name', default='Updated Deck', help='Name for the output deck')
    parser.add_argument('--config', help='Path to JSON config file')
    parser.add_argument('--search-field', choices=['question', 'answer'], default='answer', 
                       help='Which field to use for image search (default: answer)')
    
    args = parser.parse_args()
    
    # Default config
    default_config = {
        'question_field': 'Question',
        'answer_field': 'Answer',
        'image_field': 'Image',
        'output_dir': 'output',
        'images_dir': 'images',
        'delay_between_searches': 1.0,
        'max_image_size': (800, 600),
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'search_field': 'answer'
    }
    # Load config if provided
    user_config = {}
    if args.config:
        import json
        with open(args.config, 'r') as f:
            user_config = json.load(f)
    # Merge configs: default <- user_config <- CLI args
    config = default_config.copy()
    config.update(user_config)
    config['search_field'] = args.search_field
    
    try:
        # Create updater and process deck
        updater = AnkiImageUpdater(config)
        output_path = updater.process_deck(args.input_file, args.deck_name)
        
        print(f"\n✅ Success! Updated deck saved to: {output_path}")
        print(f"📁 Images saved to: {updater.images_path}")
        
    except Exception as e:
        logger.error(f"Error processing deck: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 