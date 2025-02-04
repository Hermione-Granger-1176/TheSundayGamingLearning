import os
import glob

sessions_dir = 'sessions'
output_file = 'index.md'

template = """# My Video Sessions

<!-- AUTO_GENERATED_START -->
%s
<!-- AUTO_GENERATED_END -->
"""

sessions = sorted([d for d in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, d))])
entries = []

for session in sessions:
    session_path = os.path.join(sessions_dir, session)
    
    try:
        with open(os.path.join(session_path, 'title.txt')) as f:
            title = f.read().strip()
        with open(os.path.join(session_path, 'video_url.txt')) as f:
            video_url = f.read().strip()
    except FileNotFoundError:
        continue

    files = []
    files_dir = os.path.join(session_path, 'files')
    if os.path.exists(files_dir):
        for file in os.listdir(files_dir):
            if os.path.isfile(os.path.join(files_dir, file)):
                file_path = os.path.join(sessions_dir, session, 'files', file)
                files.append(f'[{file}]({file_path})')

    file_links = ' | '.join(files)
    entries.append(f"### {title}\n- [Watch Video]({video_url})\n- Downloads: {file_links}\n")

content = template % '\n\n'.join(entries)

with open(output_file, 'w') as f:
    f.write(content)
