import os
import re

BACKEND_URL = "https://roblox-script-4dl2.onrender.com"
dir_path = 'd:/project/backend-frontend/script-roblox/frontend'

for filename in os.listdir(dir_path):
    if filename.endswith('.html'):
        filepath = os.path.join(dir_path, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Update all API fetch requests
        content = content.replace("fetch('/api/", f"fetch('{BACKEND_URL}/api/")
        content = content.replace('fetch("/api/', f'fetch("{BACKEND_URL}/api/')
        content = content.replace("fetch(`/api/", f"fetch(`{BACKEND_URL}/api/")

        # 2. Update Image rendering paths to support legacy relative URLs
        content = content.replace('src="${s.image}"', f'src="${{s.image && s.image.startsWith(\'/\') ? \'{BACKEND_URL}\' + s.image : s.image}}"')
        content = content.replace('src="${e.image}"', f'src="${{e.image && e.image.startsWith(\'/\') ? \'{BACKEND_URL}\' + e.image : e.image}}"')
        content = content.replace('src="${u.avatar', f'src="${{u.avatar && u.avatar.startsWith(\'/\') ? \'{BACKEND_URL}\' + u.avatar : u.avatar')
        content = content.replace('src="${user.avatar', f'src="${{user.avatar && user.avatar.startsWith(\'/\') ? \'{BACKEND_URL}\' + user.avatar : user.avatar')
        
        # 3. Update Admin upload logic to save absolute URLs
        if filename == 'admin.html':
            content = content.replace(
                "document.getElementById(prefix + 'Image').value = data.url;",
                f"const fullUrl = data.url.startsWith('/') ? '{BACKEND_URL}' + data.url : data.url;\n                    document.getElementById(prefix + 'Image').value = fullUrl;"
            )
            content = content.replace(
                "document.getElementById('sPreview').src = data.url;",
                "document.getElementById('sPreview').src = fullUrl;"
            )
            
        # 4. Update Profile upload logic to save absolute URLs
        if filename == 'profile.html':
            content = content.replace(
                "if (data.url) {",
                f"if (data.url) {{\n                    const fullUrl = data.url.startsWith('/') ? '{BACKEND_URL}' + data.url : data.url;\n                    data.url = fullUrl;"
            )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filename}")
