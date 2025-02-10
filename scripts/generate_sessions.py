from pathlib import Path
import re
import os

def generate_site():
    sessions_dir = Path('sessions')
    output_header = "# 📺 Video Sessions\n\n"
    
    processed_entries = [
        process_folder(folder)
        for folder in sorted(
            (p for p in sessions_dir.iterdir() if p.is_dir()),
            key=lambda x: int(re.search(r'^(\d+)', x.name).group(1) or 0)
        )
        if (folder/'video.txt').exists()
    ]
    
    Path('index.md').write_text(output_header + '\n\n---\n\n'.join(processed_entries))

def process_folder(folder: Path) -> str:
    title = re.sub(r'^\d+-', '', folder.name).replace('-', ' ')
    components = [
        f"## 🎬 {title}",
        f"📺 Watch: [YouTube Link]({(folder/'video.txt').read_text().strip()})"
    ]
    
    if (zip_file := folder/'Files.zip').exists():
        components.append(
            f"📥 Download: [Session Materials]"
            f"(https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/main/{zip_file})"
        )
    
    if (urls_file := folder/'urls.txt').exists():
        components.extend([
            "🔗 Additional Resources:",
            *(f"- [{t}]({u})" for t,u in 
              (line.strip().split(':',1) 
               for line in urls_file.read_text().splitlines()
               if ':' in line))
        ])
    
    return '\n\n'.join(components)
