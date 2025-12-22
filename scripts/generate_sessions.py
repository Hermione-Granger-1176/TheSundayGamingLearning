from pathlib import Path
import re
import os

def generate_site():
    """Generate markdown index from structured session folders"""
    
    # 1. Directory setup using pathlib for modern path handling
    sessions_dir = Path('sessions')
    output_header = "# 📺 Video Sessions\n\n"
    
    # 2. Process folders in sorted order using numerical prefix
    processed_entries = [
        '\n\n'.join(process_folder(folder))
        for folder in sorted(
            filter(Path.is_dir, sessions_dir.iterdir()),
            key=session_sort_key
        )
        if (folder/'video.txt').exists()  # Only process folders with video files
    ]

    # 3. Combine all entries with separators
    Path('index.md').write_text(
        output_header + '\n\n---\n\n'.join(processed_entries)
    )

def session_sort_key(folder: Path) -> int:
    """Sort sessions by numeric prefix stored in metadata or folder name"""
    original_name = get_original_name(folder)
    if match := re.match(r'^(\d+)', original_name):
        return int(match.group(1))
    if match := re.match(r'^session_(\d+)$', folder.name):
        return int(match.group(1))
    return 0

def process_folder(folder: Path) -> list[str]:
    """Transform folder contents into markdown components"""
    
    # 1. Clean title from folder name
    title = re.sub(r'^\d+-', '', get_original_name(folder)).replace('-', ' ')
    
    # 2. Core video link component
    components = [
        f"## 🎬 {title}",
        f"📺 Watch: [YouTube Link]({(folder/'video.txt').read_text().strip()})"
    ]
    
    # 3. Conditional ZIP file inclusion using walrus operator
    if (zip_file := folder/'Files.zip').exists():
        components.append(
            f"📥 Download: [Session Materials]"
            f"(https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY', 'Hermione-Granger-1176/TheSundayGamingLearning')}/main/{zip_file})"
        )
    
    # 4. Process URLs with generator expression
    if (urls_file := folder/'urls.txt').exists():
        components.extend([
            "🔗 Additional Resources:",
            *(
                f"- [{t}]({u})" 
                for t, u in (line.strip().split(':', 1) 
                            for line in urls_file.read_text().splitlines() 
                            if ':' in line)
            )
        ])
    
    return components

def get_original_name(folder: Path) -> str:
    """Fetch the stored original session folder name"""
    name_file = folder / 'name.txt'
    return name_file.read_text().strip() if name_file.exists() else folder.name

if __name__ == "__main__":
    generate_site()
