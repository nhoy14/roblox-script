import os
import uuid
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '../frontend')
UPLOAD_FOLDER = os.path.join(FRONTEND_DIR, 'uploads')
DATA_FILE = os.path.join(BASE_DIR, 'database.json')

app = Flask(__name__, 
            template_folder=FRONTEND_DIR, 
            static_folder=FRONTEND_DIR)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- JSON DATABASE HELPERS ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"scripts": [], "executors": [], "users": []}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "users" not in data:
                data["users"] = []
            return data
    except Exception:
        return {"scripts": [], "executors": [], "users": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# Ensure file exists
if not os.path.exists(DATA_FILE):
    save_data({"scripts": [], "executors": [], "users": []})
print("✅ Successfully initialized local JSON database!")

# --- BACKGROUND TASK: 1s = 1 View ---
def background_view_updater():
    """
    Runs forever.
    Waits 1 second.
    Adds +1 view to ALL scripts.
    """
    print("Background View Updater Started (1s / +1 view)...")
    while True:
        time.sleep(1) 
        try:
            data = load_data()
            if data["scripts"]:
                for script in data["scripts"]:
                    script['views'] = script.get('views', 0) + 1
                save_data(data)
        except Exception as e:
            print(f"[Auto-View] Error: {e}")

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login.html')
def login():
    return render_template('login.html')

@app.route('/signup.html')
def signup():
    return render_template('signup.html')

@app.route('/profile.html')
def profile():
    return render_template('profile.html')

@app.route('/admin.html')
def admin():
    return render_template('admin.html')

@app.route('/download.html')
def download():
    return render_template('download.html')

# --- API: USERS ---
@app.route('/api/users/signup', methods=['POST'])
def api_signup():
    data = load_data()
    req = request.json
    if any(u['username'] == req['username'] for u in data['users']):
        return jsonify({'error': 'Username already exists'}), 400
    
    new_user = {
        'id': uuid.uuid4().hex,
        'username': req['username'],
        'password': req['password'],
        'avatar': req.get('avatar', 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + req['username']),
        'created_at': datetime.now().isoformat(),
        'role': 'user'
    }
    data['users'].append(new_user)
    save_data(data)
    # Don't send password back to frontend
    user_safe = {k: v for k, v in new_user.items() if k != 'password'}
    return jsonify({'success': True, 'user': user_safe})

@app.route('/api/users/login', methods=['POST'])
def api_login():
    data = load_data()
    req = request.json
    if req['username'] == 'admin' and req['password'] == 'admin':
        return jsonify({'success': True, 'user': {'id': 'admin', 'username': 'admin', 'role': 'admin', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin'}})
    
    user = next((u for u in data['users'] if u['username'] == req['username'] and u['password'] == req['password']), None)
    if user:
        user_safe = {k: v for k, v in user.items() if k != 'password'}
        return jsonify({'success': True, 'user': user_safe})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/users/all', methods=['GET'])
def get_all_users():
    # Only for admin (we trust the UI for now, but ideally this would check tokens)
    data = load_data()
    return jsonify(data['users'])

@app.route('/api/users/<id>', methods=['PUT', 'DELETE'])
def manage_user(id):
    data = load_data()
    user_idx = next((i for i, u in enumerate(data['users']) if u.get('id') == id), None)
    
    if user_idx is None:
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'DELETE':
        data['users'].pop(user_idx)
    elif request.method == 'PUT':
        update_data = request.json
        if 'password' in update_data and update_data['password']:
            data['users'][user_idx]['password'] = update_data['password']
        if 'avatar' in update_data and update_data['avatar']:
            data['users'][user_idx]['avatar'] = update_data['avatar']

    save_data(data)
    return jsonify({'success': True})

# --- IMAGE UPLOAD ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'error': 'File type not allowed'}), 400
            
        filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        return jsonify({'url': f'/uploads/{filename}'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- API: SCRIPTS ---
@app.route('/api/scripts', methods=['GET', 'POST'])
def handle_scripts():
    data = load_data()
    
    if request.method == 'GET':
        return jsonify(data["scripts"][::-1])
    
    new_script = request.json
    new_script['id'] = uuid.uuid4().hex
    new_script['views'] = 0 
    if 'timestamp' not in new_script:
        new_script['timestamp'] = datetime.now().isoformat()
    
    data["scripts"].append(new_script)
    save_data(data)
    
    return jsonify({'success': True, 'id': new_script['id']})

@app.route('/api/scripts/<id>', methods=['PUT', 'DELETE'])
def manage_script(id):
    data = load_data()
    script_idx = next((i for i, s in enumerate(data["scripts"]) if s.get('id') == id), None)
    
    if script_idx is None:
        return jsonify({'error': 'Script not found'}), 404

    if request.method == 'DELETE':
        data["scripts"].pop(script_idx)
    elif request.method == 'PUT':
        update_data = request.json
        data["scripts"][script_idx].update(update_data)
        
    save_data(data)
    return jsonify({'success': True})

# --- API: EXECUTORS ---
@app.route('/api/executors', methods=['GET', 'POST'])
def handle_executors():
    data = load_data()
    
    if request.method == 'GET':
        return jsonify(data["executors"][::-1])
    
    new_exec = request.json
    new_exec['id'] = uuid.uuid4().hex
    data["executors"].append(new_exec)
    save_data(data)
    
    return jsonify({'success': True, 'id': new_exec['id']})

@app.route('/api/executors/<id>', methods=['PUT', 'DELETE'])
def manage_executors(id):
    data = load_data()
    exec_idx = next((i for i, e in enumerate(data["executors"]) if e.get('id') == id), None)
    
    if exec_idx is None:
        return jsonify({'error': 'Executor not found'}), 404

    if request.method == 'DELETE':
        data["executors"].pop(exec_idx)
    elif request.method == 'PUT':
        update_data = request.json
        data["executors"][exec_idx].update(update_data)
        
    save_data(data)
    return jsonify({'success': True})

if __name__ == '__main__':
    threading.Thread(target=background_view_updater, daemon=True).start()
    app.run(debug=True, port=5000)