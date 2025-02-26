#!/usr/bin/env python3
"""
Session Index Generator
Scans session folders and generates an attractive, navigable index.md file
with enhanced formatting, navigation features, and performance optimizations.
"""
import os
import re
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Generator, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("index-generator")

# Constants
CACHE_FILE = Path(".cache/session_data.json")
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "Hermione-Granger-1176/TheSundayGamingLearning")
DEFAULT_ENCODING = "utf-8"

class SessionProcessor:
    """Processes session folders and generates markdown index content"""
    
    def __init__(self, sessions_dir: Path = Path("sessions")):
        self.sessions_dir = sessions_dir
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cached session data if available"""
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, "r", encoding=DEFAULT_ENCODING) as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache: {e}")
        return {}

    def _save_cache(self) -> None:
        """Save session data to cache"""
        try:
            CACHE_FILE.parent.mkdir(exist_ok=True)
            with open(CACHE_FILE, "w", encoding=DEFAULT_ENCODING) as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _get_folder_hash(self, folder: Path) -> str:
        """Generate a hash for folder contents to detect changes"""
        hasher = hashlib.md5()
        
        # Hash folder name
        hasher.update(folder.name.encode(DEFAULT_ENCODING))
        
        # Hash video.txt if it exists
        video_path = folder / "video.txt"
        if video_path.exists():
            hasher.update(video_path.read_bytes())
        
        # Hash urls.txt if it exists
        urls_path = folder / "urls.txt"
        if urls_path.exists():
            hasher.update(urls_path.read_bytes())
        
        # Check if zip exists and its timestamp
        zip_path = folder / "Files.zip"
        if zip_path.exists():
            hasher.update(str(zip_path.stat().st_mtime).encode(DEFAULT_ENCODING))
        
        return hasher.hexdigest()
    
    def _read_file_safely(self, file_path: Path) -> str:
        """Safely read file contents with error handling"""
        try:
            return file_path.read_text(encoding=DEFAULT_ENCODING).strip()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return ""
    
    def _extract_session_number(self, folder_name: str) -> int:
        """Extract session number from folder name"""
        match = re.search(r'^(\d+)', folder_name)
        return int(match.group(1)) if match else 0
    
    def _clean_title(self, folder_name: str) -> str:
        """Clean title from folder name"""
        return re.sub(r'^\d+-', '', folder_name).replace('-', ' ')
    
    def _parse_urls_file(self, urls_file: Path) -> List[Tuple[str, str]]:
        """Parse URLs file into title/URL pairs"""
        try:
            content = self._read_file_safely(urls_file)
            return [
                (title.strip(), url.strip()) 
                for line in content.splitlines() 
                if ':' in line
                for title, url in [line.split(':', 1)]
            ]
        except Exception as e:
            logger.error(f"Error parsing URLs file {urls_file}: {e}")
            return []
    
    def _extract_date_from_title(self, title: str) -> Optional[str]:
        """Try to extract a date from the title if present"""
        date_match = re.search(r'(\d{2}[-/]\d{2}[-/]\d{2,4}|\w+ \d{1,2},? \d{4})', title)
        return date_match.group(1) if date_match else None
    
    def get_session_folders(self) -> List[Path]:
        """Get sorted list of valid session folders"""
        try:
            return sorted(
                [
                    folder for folder in self.sessions_dir.iterdir()
                    if folder.is_dir() and (folder / "video.txt").exists()
                ],
                key=lambda p: self._extract_session_number(p.name)
            )
        except Exception as e:
            logger.error(f"Error reading session folders: {e}")
            return []
    
    def process_folder(self, folder: Path) -> Dict[str, Any]:
        """Process a session folder and return structured data"""
        folder_hash = self._get_folder_hash(folder)
        
        # Check cache first
        if folder.name in self.cache and self.cache[folder.name]["hash"] == folder_hash:
            logger.info(f"Using cached data for {folder.name}")
            return self.cache[folder.name]["data"]
        
        logger.info(f"Processing folder: {folder}")
        
        session_num = self._extract_session_number(folder.name)
        title = self._clean_title(folder.name)
        date = self._extract_date_from_title(title)
        
        video_url = self._read_file_safely(folder / "video.txt")
        
        # Get video ID for thumbnail
        video_id = None
        if "youtu" in video_url:
            match = re.search(r'(?:v=|\.be/)([a-zA-Z0-9_-]+)', video_url)
            if match:
                video_id = match.group(1)
        
        zip_exists = (folder / "Files.zip").exists()
        
        urls = []
        if (folder / "urls.txt").exists():
            urls = self._parse_urls_file(folder / "urls.txt")
        
        # Build session data
        session_data = {
            "id": session_num,
            "title": title,
            "date": date,
            "video_url": video_url,
            "video_id": video_id,
            "has_materials": zip_exists,
            "materials_url": f"https://raw.githubusercontent.com/{REPOSITORY}/main/{folder}/Files.zip" if zip_exists else None,
            "resources": urls
        }
        
        # Update cache
        self.cache[folder.name] = {
            "hash": folder_hash,
            "data": session_data
        }
        
        return session_data
    
    def generate_markdown(self) -> str:
        """Generate complete markdown content"""
        session_folders = self.get_session_folders()
        if not session_folders:
            logger.error("No valid session folders found")
            return "# 📺 Video Sessions\n\nNo sessions available."
        
        sessions = [self.process_folder(folder) for folder in session_folders]
        
        # Save cache after processing
        self._save_cache()
        
        # Build markdown
        md = ["# 📺 The Sunday Gaming Learning Sessions\n"]
        
        # Add current date
        md.append(f"*Index last updated: {datetime.now().strftime('%B %d, %Y')}*\n")
        
        # Generate table of contents
        md.append("## 📋 Table of Contents\n")
        for session in sessions:
            session_id = f"session-{session['id']}"
            md.append(f"- [#{session['id']} {session['title']}](#{session_id})")
        
        # Generate session entries
        for session in sessions:
            session_id = f"session-{session['id']}"
            md.append(f"\n---\n\n## 🎬 {session['title']} <a id='{session_id}'></a>")
            
            # Add date if available
            if session['date']:
                md.append(f"*Recorded: {session['date']}*")
            
            # Add video thumbnail if we have an ID
            if session['video_id']:
                md.append(f"[![Session Thumbnail](https://img.youtube.com/vi/{session['video_id']}/0.jpg)]({session['video_url']})")
            
            md.append(f"📺 **Watch**: [View on YouTube]({session['video_url']})")
            
            if session['has_materials']:
                md.append(f"📥 **Download**: [Session Materials]({session['materials_url']})")
            
            if session['resources']:
                md.append("\n🔗 **Additional Resources**:")
                for title, url in session['resources']:
                    md.append(f"- [{title}]({url})")
            
            # Add back to top link
            md.append("\n[⬆️ Back to Table of Contents](#-table-of-contents)")
            
        return "\n\n".join(md)
    
    def generate_site(self) -> None:
        """Generate and save the index.md file"""
        try:
            content = self.generate_markdown()
            with open("index.md", "w", encoding=DEFAULT_ENCODING) as f:
                f.write(content)
            logger.info("Successfully generated index.md")
        except Exception as e:
            logger.error(f"Error generating index.md: {e}")
            raise

def main() -> None:
    """Main entry point"""
    logger.info("Starting session index generation")
    processor = SessionProcessor()
    processor.generate_site()
    logger.info("Finished session index generation")

if __name__ == "__main__":
    main()
