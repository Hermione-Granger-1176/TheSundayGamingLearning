import os
import re

def get_session_number(folder_name):
    """Extract number from folder name like '01-Session Name'"""
    match = re.match(r'^(\d+)-', folder_name)
    return int(match.group(1)) if match else 0

def parse_urls(urls_file):
    """Parse URLs with titles from urls.txt"""
    urls = []
    if os.path.exists(urls_file):
        with open(urls_file) as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    title, url = line.split(':', 1)
                    urls.append((title.strip(), url.strip()))
    return urls

def generate_site():
    sessions_dir = 'sessions'
    output = ["# 📺 Video Sessions\n\n"]
    
    # Get all session folders
    folders = [d for d in os.listdir(sessions_dir) 
               if os.path.isdir(os.path.join(sessions_dir, d))]
    
    # Sort by extracted number
    folders.sort(key=get_session_number)
    
    for folder in folders:
        path = os.path.join(sessions_dir, folder)
        
        # Get session title (remove number prefix)
        title = re.sub(r'^\d+-', '', folder).replace('-', ' ')
        
        # Get video URL
        video_file = os.path.join(path, 'video.txt')
        if os.path.exists(video_file):
            video_url = open(video_file).read().strip()
        else:
            continue  # Skip if no video URL
        
        # Start building entry
        entry = [
            f"## 🎬 {title}",
            f"📺 Watch: [YouTube Link]({video_url})"
        ]
        
        # Add ZIP file if exists
        zip_path = os.path.join(path, 'Files.zip')
        if os.path.exists(zip_path):
            raw_url = f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/main/{zip_path}"
            entry.append(f"📥 Download: [Session Materials]({raw_url})")
        
        # Add additional URLs if exists
        urls_file = os.path.join(path, 'urls.txt')
        titled_urls = parse_urls(urls_file)
        if titled_urls:
            entry.append("🔗 Additional Resources:")
            entry.extend([f"- [{title}]({url})" for title, url in titled_urls])
        
        output.append("\n\n".join(entry) + "\n\n---")
    
    # Write final content
    with open('index.md', 'w') as f:
        f.write("\n\n".join(output))

if __name__ == "__main__":
    generate_site()
