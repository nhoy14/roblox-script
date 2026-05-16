import os

dir_path = 'd:/project/backend-frontend/script-roblox/frontend'
for filename in os.listdir(dir_path):
    if filename.endswith('.html'):
        filepath = os.path.join(dir_path, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '<link rel="icon"' not in content:
            content = content.replace('<head>', '<head>\n    <link rel="icon" type="image/png" href="/favicon.png">')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        print(f'Processed {filename}')
