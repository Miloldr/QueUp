from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
import os
import bcrypt
import functools
import atexit
from app import database, User, TaskTypeSettings, DifficultySettings

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '0ed6181591343759e70ba7ff19f6b9efdf026b5b36552b76bf101c238246d81b')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)
CORS(app, supports_credentials=True)

db = database("tasks.db")

@atexit.register
def cleanup_resources():
    print("Shutting down: Closing database connection")
    db.close()

def auth(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        request.user_data = User(user['id'], db)
        return f(*args, **kwargs)
    return wrapper

@app.teardown_appcontext
def cleanup_after_request(exception=None):
    pass

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if db.get_user_by_email(email):
        return jsonify({'error': 'Email already exists'}), 400
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    if db.get_user(username):
        return jsonify({'error': 'Username already exists'}), 400
    password = data.get('password')
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters long'}), 400
    
    db.add_user(username, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'), email)
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    if not db.get_user(username):
        return jsonify({'error': 'Username does not exist'}), 404
    password = data.get('password')
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    user = db.get_user(username)
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    session['user_id'] = user['id']
    return jsonify({'message': 'Login successful'}), 200

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/me', methods=['GET'])
@auth
def me():
    user_id = session.get('user_id')
    
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'id': user['id'], 'username': user['username'], 'email': user['email']}), 200

@app.route('/tasks', methods=['GET'])
@auth
def get_tasks():    
    try:
        tasks = request.user_data.get_prioritized_tasks()
        urgent_tasks_list = request.user_data.get_urgent_tasks()
        overdue_tasks_list = request.user_data.get_overdue_tasks()

        overdue_tasks = [task for task in tasks if task in overdue_tasks_list]
        urgent_tasks = [task for task in tasks if task in urgent_tasks_list and task not in overdue_tasks_list]
        prioritized_tasks = [task for task in tasks if task not in urgent_tasks_list and task not in overdue_tasks_list]
        
        tasks_data = {
            "overdue": [{'id': task.id, 'title': task.title, 'category': task.category, 'type': task.type, 'difficulty': task.difficulty, 'note': task.note, 'due': task.due.isoformat() if task.due else None, 'deadline': task.deadline.isoformat() if task.deadline else None, 'complete': task.complete} for task in overdue_tasks],
            "urgent": [{'id': task.id, 'title': task.title, 'category': task.category, 'type': task.type, 'difficulty': task.difficulty, 'note': task.note, 'due': task.due.isoformat() if task.due else None, 'deadline': task.deadline.isoformat() if task.deadline else None, 'complete': task.complete} for task in urgent_tasks],
            "prioritized": [{'id': task.id, 'title': task.title, 'category': task.category, 'type': task.type, 'difficulty': task.difficulty, 'note': task.note, 'due': task.due.isoformat() if task.due else None, 'deadline': task.deadline.isoformat() if task.deadline else None, 'complete': task.complete} for task in prioritized_tasks]
        }
        
        return jsonify(tasks_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks/completed', methods=['GET'])
@auth
def get_completed_tasks():
    try:
        completed_tasks = request.user_data.get_completed_tasks()
        tasks_data = [{'id': task.id, 'title': task.title, 'category': task.category, 'type': task.type, 'difficulty': task.difficulty, 'note': task.note, 'due': task.due.isoformat() if task.due else None, 'deadline': task.deadline.isoformat() if task.deadline else None, 'complete': task.complete} for task in completed_tasks]
        return jsonify(tasks_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tasks', methods=['POST'])
@auth
def add_task():    
    data = request.get_json()
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    category = data.get('category')
    if not category:
        return jsonify({'error': 'Category is required'}), 400
    typee = data.get('type')
    if not typee:
        return jsonify({'error': 'Type is required'}), 400
    task_type = request.user_data.get_task_type_setting(typee)
    if not task_type:
        return jsonify({'error': 'Invalid task type'}), 404
    difficulty = data.get('difficulty')
    if not difficulty:
        return jsonify({'error': 'Difficulty is required'}), 400
    difficulty_setting = request.user_data.get_difficulty_setting(difficulty)
    if not difficulty_setting:
        return jsonify({'error': 'Invalid task difficulty'}), 404
    note = data.get('note', '')
    deadline = data.get('deadline')
    if not deadline:
        return jsonify({'error': 'Deadline is required'}), 400
    
    try:
        result = request.user_data.add_task(title, category, typee, deadline, difficulty, note)
        if result['success']:
            return jsonify({'message': 'Task added successfully'}), 201
        else:
            return jsonify({'error': result['response']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/tasks/<task_id>', methods=['DELETE'])
@auth
def delete_task(task_id):
    try:
        task = request.user_data.get_task_by_id(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        result = request.user_data.delete_task(task_id)
        if result['success']:
            return jsonify({'message': 'Task deleted successfully'}), 200
        else:
            return jsonify({'error': result['response']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/tasks/complete/<task_id>', methods=['PUT'])
@auth
def mark_task_complete(task_id):
    try:
        task = request.user_data.get_task_by_id(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        result = request.user_data.mark_complete(task_id, complete=not task.complete)
        if result['success']:
            if task.complete:
                return jsonify({'message': 'Task marked as complete'}), 200
            else:
                return jsonify({'message': 'Task marked as incomplete'}), 200
        else:
            return jsonify({'error': result['response']}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/settings', methods=['GET'])
@auth
def get_settings():
    try:
        settings = {
            "task_types": [{"name": setting.name, "deadline_format": setting.deadline_format, "priority_rank": setting.priority_rank, "default_due_days_before_deadline": setting.default_due_days_before_deadline, "prioritize_when_days_left": setting.prioritize_when_days_left} for setting in request.user_data.get_task_type_settings()], 
            "difficulties": [{"name": setting.name, "priority_rank": setting.priority_rank} for setting in request.user_data.get_difficulty_settings()]
        }
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/settings', methods=['PUT'])
@auth
def update_settings():
    data = request.get_json()
    task_types = data.get('task_types')
    difficulties = data.get('difficulties')
    
    if not task_types or not isinstance(task_types, list):
        return jsonify({'error': 'Task types must be a list'}), 400
    if not difficulties or not isinstance(difficulties, list):
        return jsonify({'error': 'Difficulties must be a list'}), 400
    
    try:        
        if task_types:
            for setting in task_types:
                if not isinstance(setting, dict):
                    return jsonify({'error': 'Each task type setting must be an object'}), 400
                if 'name' not in setting:
                    return jsonify({'error': 'Task type setting name is required'}), 400
                    
            task_type_settings = [TaskTypeSettings(**setting) for setting in task_types]
            result = request.user_data.update_task_type_settings(task_type_settings)
            if not result['success']:
                return jsonify({'error': result['response']}), 400
                
        if difficulties:
            for setting in difficulties:
                if not isinstance(setting, dict):
                    return jsonify({'error': 'Each difficulty setting must be an object'}), 400
                if 'name' not in setting:
                    return jsonify({'error': 'Difficulty setting name is required'}), 400
                    
            difficulty_settings = [DifficultySettings(**setting) for setting in difficulties]
            result = request.user_data.update_difficulty_settings(difficulty_settings)
            if not result['success']:
                return jsonify({'error': result['response']}), 400
                
        return jsonify({'message': 'Settings updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/settings/priority-order', methods=['PUT'])
@auth
def update_priority_order():
    """Update the priority order of task types and difficulties"""
    data = request.get_json()
    task_types_order = data.get('task_types_order')
    difficulties_order = data.get('difficulties_order')
    
    try:
        # Update task type priority rankings based on order
        if task_types_order and isinstance(task_types_order, list):
            current_type_settings = request.user_data.get_task_type_settings()
            settings_dict = {setting.name: setting for setting in current_type_settings}
            
            updated_type_settings = []
            for index, type_name in enumerate(task_types_order):
                if type_name in settings_dict:
                    setting = settings_dict[type_name]
                    setting.priority_rank = index  # Lower index = higher priority (lower rank)
                    updated_type_settings.append(setting)
            
            if updated_type_settings:
                result = request.user_data.update_task_type_settings(updated_type_settings)
                if not result['success']:
                    return jsonify({'error': f'Failed to update task types: {result["response"]}'}), 400
        
        # Update difficulty priority rankings based on order
        if difficulties_order and isinstance(difficulties_order, list):
            current_difficulty_settings = request.user_data.get_difficulty_settings()
            settings_dict = {setting.name: setting for setting in current_difficulty_settings}
            
            updated_difficulty_settings = []
            for index, difficulty_name in enumerate(difficulties_order):
                if difficulty_name in settings_dict:
                    setting = settings_dict[difficulty_name]
                    setting.priority_rank = index  # Lower index = higher priority (lower rank)
                    updated_difficulty_settings.append(setting)
            
            if updated_difficulty_settings:
                result = request.user_data.update_difficulty_settings(updated_difficulty_settings)
                if not result['success']:
                    return jsonify({'error': f'Failed to update difficulties: {result["response"]}'}), 400
        
        return jsonify({'message': 'Priority order updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("Closing..")
    finally:
        if 'db' in locals() or 'db' in globals():
            db.close()
            print("Closed database connection")