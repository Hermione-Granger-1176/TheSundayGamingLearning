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
            key=lambda p: int(re.search(r'^(\d+)', p.name).group(1) or 0)
        )
        if (folder/'video.txt').exists()  # Only process folders with video files
    ]

    # 3. Combine all entries with separators
    Path('index.md').write_text(
        output_header + '\n\n---\n\n'.join(processed_entries)
    )

def process_folder(folder: Path) -> list[str]:
    """Transform folder contents into markdown components"""
    
    # 1. Clean title from folder name
    title = re.sub(r'^\d+-', '', folder.name).replace('-', ' ')
    
    # 2. Core video link component
    components = [
        f"## 🎬 {title}",
        f"📺 Watch: [YouTube Link]({(folder/'video.txt').read_text().strip()})"
    ]
    
    # 3. Conditional ZIP file inclusion using walrus operator
    if (zip_file := folder/'Files.zip').exists():
        components.append(
            f"📥 Download: [Session Materials]"
            f"(https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/main/{zip_file})"
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

if __name__ == "__main__":
    generate_site()
