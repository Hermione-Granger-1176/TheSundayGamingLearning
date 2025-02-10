from pathlib import Path
import re
import os
from functools import lru_cache

# Pre-compiled patterns
SESSION_PATTERN = re.compile(r'^(\d+)-')
URL_SPLITTER = re.compile(r':\s*')

@lru_cache(maxsize=None)
def repo_path():
    return os.environ['GITHUB_REPOSITORY']

def generate_site():
    """Generate markdown index using optimized patterns"""
    entries = [
        process_folder(folder) 
        for folder in sorted(
            (p for p in Path('sessions').iterdir() if p.is_dir()),
            key=lambda x: int(SESSION_PATTERN.search(x.name).group(1) or 0)
        )
        if (folder/'video.txt').exists()
    ]
    
    Path('index.md').write_text(
        "# 📺 Video Sessions\n\n" + '\n\n---\n\n'.join(entries)
    )

def process_folder(folder: Path) -> str:
    """Process folder contents into markdown string"""
    title = SESSION_PATTERN.sub('', folder.name).replace('-', ' ')
    components = [
        f"## 🎬 {title}",
        f"📺 Watch: [YouTube Link]({(folder/'video.txt').read_text().strip()})"
    ]
    
    if (zip_file := folder/'Files.zip').exists():
        components.append(
            f"📥 Download: [Session Materials]"
            f"(https://raw.githubusercontent.com/{repo_path()}/{zip_file})"
        )
    
    if (urls_file := folder/'urls.txt').exists():
        components.extend([
            "🔗 Additional Resources:",
            *(
                f"- [{t}]({u})" 
                for t, u in (
                    URL_SPLITTER.split(line.strip(), 1) 
                    for line in urls_file.open()
                )
                if u
            )
        ])
    
    return '\n\n'.join(components)
