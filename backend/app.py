import sqlite3
import json
import uuid
from datetime import datetime, timedelta


class TaskTypeSettings:
    def __init__(self, name, default_due_days_before_deadline=1, prioritize_when_days_left=1, deadline_format="date", priority_rank=0):
        self.name = name
        self.default_due_days_before_deadline = default_due_days_before_deadline
        self.prioritize_when_days_left = prioritize_when_days_left
        self.deadline_format = deadline_format
        self.priority_rank = priority_rank

class DifficultySettings:
    def __init__(self, name, priority_rank=0):
        self.name = name
        self.priority_rank = priority_rank

class Task:
    def __init__(self, title, category, type, due, deadline, difficulty=None, note=None, complete=False, id=None):
        self.id = id if id else str(uuid.uuid4())
        self.title = title
        self.type = type
        self.due = due if isinstance(due, datetime) else datetime.fromisoformat(due) if due else None
        self.deadline = deadline if isinstance(deadline, datetime) else datetime.fromisoformat(deadline) if deadline else None
        self.category = category
        self.difficulty = difficulty
        self.note = note
        self.complete = complete
    
    def set_deadline_with_time_setting(self, deadline_input, format_type: str = "date"):
        if isinstance(deadline_input, str):
            deadline_input = datetime.fromisoformat(deadline_input)
        
        if format_type == "datetime":
            self.deadline = deadline_input
        else:
            self.deadline = deadline_input.replace(hour=23, minute=59, second=59, microsecond=0)

class database:
    def __init__(self, db_name: str):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self._create_tables()
        
    def get_cursor(self):
        return self.connection.cursor()

    def _create_tables(self):
        cursor = self.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                tasks TEXT,
                task_types TEXT,
                task_difficulties TEXT,
                task_type_settings TEXT,
                difficulty_settings TEXT
            )
        ''')
        self.connection.commit()
    
    def add_user(self, username: str, password: str, email: str):
        try:
            default_types = json.dumps(["Short term", "Long term"])
            default_difficulties = json.dumps(["Easy", "Medium", "Hard"])
            
            default_type_settings = json.dumps([{"name": "Short term", "default_due_days_before_deadline": 1, "prioritize_when_days_left": 1, "deadline_format": "date", "priority_rank": 0}, {"name": "Long term", "default_due_days_before_deadline": 7, "prioritize_when_days_left": 14, "deadline_format": "date", "priority_rank": 1}])
            default_difficulty_settings = json.dumps([{"name": "Easy", "priority_rank": 2}, {"name": "Medium", "priority_rank": 1}, {"name": "Hard", "priority_rank": 0}])
            
            cursor = self.get_cursor()
            cursor.execute('''
                INSERT INTO users (username, password, email, task_types, task_difficulties, task_type_settings, difficulty_settings)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, email, default_types, default_difficulties, default_type_settings, default_difficulty_settings))
            self.connection.commit()
            return {"success": True, "response": "User added successfully."}
        except sqlite3.IntegrityError:
            return {"success": False, "response": "User already exists."}
        except sqlite3.Error as e:
            return {"success": False, "response": f"An error occurred: {e}"}
    
    def _get_user(self, username: str):
        cursor = self.get_cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        return user
    
    def get_user(self, username: str):
        user = self._get_user(username)
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "password": user[2],
                "email": user[3],
                "tasks": user[4],
                "task_types": user[5] if len(user) > 5 else json.dumps(["Short term", "Long term"]),
                "task_difficulties": user[6] if len(user) > 6 else json.dumps(["Easy", "Medium", "Hard"]),
                "task_type_settings": user[7] if len(user) > 7 else None,
                "difficulty_settings": user[8] if len(user) > 8 else None
            }
        return None
    
    def get_user_by_id(self, user_id: int):
        cursor = self.get_cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "password": user[2],
                "email": user[3],
                "tasks": user[4],
                "task_types": user[5] if len(user) > 5 else json.dumps(["Short term", "Long term"]),
                "task_difficulties": user[6] if len(user) > 6 else json.dumps(["Easy", "Medium", "Hard"]),
                "task_type_settings": user[7] if len(user) > 7 else None,
                "difficulty_settings": user[8] if len(user) > 8 else None
            }
        return None
    
    def get_user_by_email(self, email: str):
        cursor = self.get_cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "password": user[2],
                "email": user[3],
                "tasks": user[4],
                "task_types": user[5] if len(user) > 5 else json.dumps(["Short term", "Long term"]),
                "task_difficulties": user[6] if len(user) > 6 else json.dumps(["Easy", "Medium", "Hard"]),
                "task_type_settings": user[7] if len(user) > 7 else None,
                "difficulty_settings": user[8] if len(user) > 8 else None
            }
        return None
    
    def _update_user_tasks(self, username: str, tasks: list[Task]):
        tasks_json = json.dumps([{
            'id': task.id,
            'title': task.title,
            'category': task.category,
            'type': task.type,
            'difficulty': task.difficulty,
            'note': task.note,
            'due': task.due.isoformat() if task.due else None,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'complete': task.complete
        } for task in tasks])
        cursor = self.get_cursor()
        cursor.execute('UPDATE users SET tasks = ? WHERE username = ?', (tasks_json, username))
        self.connection.commit()
    
    def add_task_to_user(self, username: str, task: Task):
        user = self._get_user(username)
        if user:
            tasks = []
            if user[4]:
                tasks_data = json.loads(user[4])
                tasks = [Task(**task_data) for task_data in tasks_data]
            tasks.append(task)
            self._update_user_tasks(username, tasks)
            return {"success": True, "response": "Task added successfully."}
        else:
            return {"success": False, "response": "User not found."}
    
    def get_user_tasks(self, username: str):
        user = self._get_user(username)
        if user:
            tasks_json = user[4]
            if tasks_json:
                tasks_data = json.loads(tasks_json)
                return [Task(**task_data) for task_data in tasks_data]
            return []
        return None
    
    def remove_task_from_user(self, username: str, task_id: str):
        user = self._get_user(username)
        if user:
            if user[4]:
                tasks_data = json.loads(user[4])
                tasks = [Task(**task_data) for task_data in tasks_data]
                original_count = len(tasks)
                tasks = [task for task in tasks if task.id != task_id]
                if len(tasks) < original_count:
                    self._update_user_tasks(username, tasks)
                    return {"success": True, "response": "Task removed successfully."}
                else:
                    return {"success": False, "response": "Task not found."}
            else:
                return {"success": False, "response": "No tasks found."}
        else:
            return {"success": False, "response": "User not found."}

    def mark_task_complete(self, username: str, task_id: str, complete: bool = True):
        user = self._get_user(username)
        if user:
            if user[4]:
                tasks_data = json.loads(user[4])
                tasks = [Task(**task_data) for task_data in tasks_data]
                for task in tasks:
                    if task.id == task_id:
                        task.complete = complete
                        self._update_user_tasks(username, tasks)
                        return {"success": True, "response": "Task status updated successfully."}
                return {"success": False, "response": "Task not found."}
            else:
                return {"success": False, "response": "No tasks found."}
        else:
            return {"success": False, "response": "User not found."}

    def update_user(self, username: str, password: str = None, email: str = None):
        cursor = self.get_cursor()
        if password:
            cursor.execute('UPDATE users SET password = ? WHERE username = ?', (password, username))
        if email:
            cursor.execute('UPDATE users SET email = ? WHERE username = ?', (email, username))
        self.connection.commit()

    def delete_user(self, username: str):
        cursor = self.get_cursor()
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        self.connection.commit()

    def update_user_task_types(self, username: str, task_types: list[str]):
        cursor = self.get_cursor()
        task_types_json = json.dumps(task_types)
        cursor.execute('UPDATE users SET task_types = ? WHERE username = ?', (task_types_json, username))
        self.connection.commit()
        return {"success": True, "response": "Task types updated successfully."}
    
    def update_user_task_difficulties(self, username: str, task_difficulties: list[str]):
        cursor = self.get_cursor()
        task_difficulties_json = json.dumps(task_difficulties)
        cursor.execute('UPDATE users SET task_difficulties = ? WHERE username = ?', (task_difficulties_json, username))
        self.connection.commit()
        return {"success": True, "response": "Task difficulties updated successfully."}
    
    def get_user_task_types(self, username: str):
        user = self._get_user(username)
        if user and len(user) > 5 and user[5]:
            return json.loads(user[5])
        return ["Short term", "Long term"]
    
    def get_user_task_difficulties(self, username: str):
        user = self._get_user(username)
        if user and len(user) > 6 and user[6]:
            return json.loads(user[6])
        return ["Easy", "Medium", "Hard"]
    
    def update_user_task_type_settings(self, username: str, task_type_settings: list[TaskTypeSettings]):
        cursor = self.get_cursor()
        settings_json = json.dumps([{
            "name": setting.name,
            "default_due_days_before_deadline": setting.default_due_days_before_deadline,
            "prioritize_when_days_left": setting.prioritize_when_days_left,
            "deadline_format": setting.deadline_format,
            "priority_rank": setting.priority_rank
        } for setting in task_type_settings])
        cursor.execute('UPDATE users SET task_type_settings = ? WHERE username = ?', (settings_json, username))
        self.connection.commit()
        return {"success": True, "response": "Task type settings updated successfully."}
    
    def update_user_difficulty_settings(self, username: str, difficulty_settings: list[DifficultySettings]):
        cursor = self.get_cursor()
        settings_json = json.dumps([{
            "name": setting.name,
            "priority_rank": setting.priority_rank
        } for setting in difficulty_settings])
        cursor.execute('UPDATE users SET difficulty_settings = ? WHERE username = ?', (settings_json, username))
        self.connection.commit()
        return {"success": True, "response": "Difficulty settings updated successfully."}
    
    def close(self):
        try:
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
                print("Database connection closed successfully")
        except Exception as e:
            print(f"Error closing database connection: {e}")
            
    def __del__(self):
        """Destructor to ensure connection is closed when object is garbage collected"""
        self.close()

class TaskManager:
    def __init__(self, tasks: list[Task] = [], task_type_settings: list[TaskTypeSettings] = [], difficulty_settings: list[DifficultySettings] = []):
        self.tasks: list[Task] = tasks
        self.task_type_settings = {setting.name: setting for setting in task_type_settings}
        self.difficulty_settings = {setting.name: setting for setting in difficulty_settings}

    def add_task(self, task: Task):
        self.tasks.append(task)

    def _calculate_priority_score(self, task: Task) -> int:
        score = 0
        now = datetime.now()
        
        if task.type in self.task_type_settings:
            type_setting = self.task_type_settings[task.type]
            score += type_setting.priority_rank * 1000
            
            if task.deadline:
                if type_setting.deadline_format == "datetime":
                    time_left = (task.deadline - now).total_seconds() / 3600
                    prioritize_threshold = type_setting.prioritize_when_days_left * 24
                    if time_left <= prioritize_threshold:
                        score -= 2000
                        urgency_bonus = max(0, (prioritize_threshold - time_left) * 10)
                        score -= int(urgency_bonus)
                else:
                    days_left = (task.deadline.date() - now.date()).days
                    if days_left <= type_setting.prioritize_when_days_left:
                        score -= 2000
        
        if task.difficulty in self.difficulty_settings:
            difficulty_setting = self.difficulty_settings[task.difficulty]
            score += difficulty_setting.priority_rank * 100
        
        if task.due:
            if task.type in self.task_type_settings and self.task_type_settings[task.type].deadline_format == "datetime":
                time_until_due = (task.due - now).total_seconds() / 3600
                score += max(0, int(time_until_due))
            else:
                days_until_due = (task.due.date() - now.date()).days
                score += max(0, days_until_due) * 24
        
        if task.deadline and now > task.deadline:
            if task.type in self.task_type_settings and self.task_type_settings[task.type].deadline_format == "datetime":
                hours_overdue = (now - task.deadline).total_seconds() / 3600
                score -= int(hours_overdue * 100)
            else:
                days_overdue = (now.date() - task.deadline.date()).days
                score -= days_overdue * 2400
        
        return score

    def get_prioritized_tasks(self) -> list[Task]:
        incomplete_tasks = [task for task in self.tasks if not task.complete]
        return sorted(incomplete_tasks, key=self._calculate_priority_score)

    def get_overdue_tasks(self) -> list[Task]:
        now = datetime.now()
        return [task for task in self.tasks if not task.complete and task.deadline and now > task.deadline]
    
    def get_urgent_tasks(self) -> list[Task]:
        urgent_tasks = []
        now = datetime.now()
        
        for task in self.tasks:
            if task.complete or not task.deadline:
                continue
                
            if task.type in self.task_type_settings:
                setting = self.task_type_settings[task.type]
                
                if setting.deadline_format == "datetime":
                    hours_left = (task.deadline - now).total_seconds() / 3600
                    threshold_hours = setting.prioritize_when_days_left * 24
                    if hours_left <= threshold_hours:
                        urgent_tasks.append(task)
                else:
                    days_left = (task.deadline.date() - now.date()).days
                    if days_left <= setting.prioritize_when_days_left:
                        urgent_tasks.append(task)
        
        return urgent_tasks

    def get_completed_tasks(self) -> list[Task]:
        """Return tasks that are marked as complete"""
        return [task for task in self.tasks if task.complete]

class User:
    def __init__(self, user_id: int, db: database, tasks: list[Task] = []):
        self.user_id = user_id
        self.username = None
        self.db = db
        self.tasks = tasks
        self.task_types = []
        self.task_difficulties = []
        self.task_type_settings = []
        self.difficulty_settings = []
        if not self._load_data()["success"]:
            raise ValueError("User not found or no tasks available.")
        self.taskManager = TaskManager(self.tasks, self.task_type_settings, self.difficulty_settings)

    def _load_data(self):
        user_data = self.db.get_user_by_id(self.user_id)
        if user_data:
            self.username = user_data['username']
            if user_data['tasks']:
                tasks_data = json.loads(user_data['tasks'])
                self.tasks = [Task(**task_data) for task_data in tasks_data]
            else:
                self.tasks = []
            
            self.task_types = json.loads(user_data['task_types']) if user_data['task_types'] else ["Short term", "Long term"]
            self.task_difficulties = json.loads(user_data['task_difficulties']) if user_data['task_difficulties'] else ["Easy", "Medium", "Hard"]
            
            if user_data['task_type_settings']:
                settings_data = json.loads(user_data['task_type_settings'])
                self.task_type_settings = [TaskTypeSettings(**setting) for setting in settings_data]
            else:
                self.task_type_settings = [
                    TaskTypeSettings("Short term", 1, 1, "date", 0),
                    TaskTypeSettings("Long term", 7, 14, "date", 1)
                ]
            
            if user_data['difficulty_settings']:
                settings_data = json.loads(user_data['difficulty_settings'])
                self.difficulty_settings = [DifficultySettings(**setting) for setting in settings_data]
            else:
                self.difficulty_settings = [
                    DifficultySettings("Easy", 2),
                    DifficultySettings("Medium", 1),
                    DifficultySettings("Hard", 0)
                ]
        else:
            return {"success": False, "response": "User not found."}
        return {"success": True, "response": "User data loaded successfully."}
    
    def _add_task(self, task: Task):
        self.tasks.append(task)
        self.taskManager.tasks = self.tasks
        result = self.db.add_task_to_user(self.username, task)
        return result
    
    def add_task(self, title: str, category: str, task_type: str, deadline_input, difficulty: str = None, note: str = None):
        type_setting = self.get_task_type_setting(task_type)
        format_type = type_setting.deadline_format if type_setting else "date"
        
        task = Task(title=title, category=category, type=task_type, due=None, deadline=None, difficulty=difficulty, note=note)
        
        task.set_deadline_with_time_setting(deadline_input, format_type)
        
        if type_setting:
            days_before = type_setting.default_due_days_before_deadline
            
            if format_type == "datetime":
                task.due = task.deadline - timedelta(days=days_before)
            else:
                if task_type == "Short term":
                    task.due = task.deadline
                else:
                    due_date = task.deadline.date() - timedelta(days=days_before)
                    task.due = datetime.combine(due_date, datetime.time(23, 59, 59))
        else:
            if task_type == "Short term":
                task.due = task.deadline
            else:
                task.due = task.deadline - timedelta(days=1)
        
        return self._add_task(task)
    
    def get_tasks(self) -> list[Task]:
        return self.tasks
    
    def get_prioritized_tasks(self) -> list[Task]:
        return self.taskManager.get_prioritized_tasks()
    
    def get_task_types(self) -> list[str]:
        return self.task_types
    
    def get_task_difficulties(self) -> list[str]:
        return self.task_difficulties
    
    def update_task_types(self, task_types: list[str]):
        self.task_types = task_types
        return self.db.update_user_task_types(self.username, task_types)
    
    def update_task_difficulties(self, task_difficulties: list[str]):
        self.task_difficulties = task_difficulties
        return self.db.update_user_task_difficulties(self.username, task_difficulties)
    
    def get_task_type_settings(self) -> list[TaskTypeSettings]:
        return self.task_type_settings
    
    def get_task_type_setting(self, task_type: str) -> TaskTypeSettings:
        for setting in self.task_type_settings:
            if setting.name == task_type:
                return setting
        return None
    
    def get_difficulty_settings(self) -> list[DifficultySettings]:
        return self.difficulty_settings
    
    def get_difficulty_setting(self, difficulty: str) -> DifficultySettings:
        for setting in self.difficulty_settings:
            if setting.name == difficulty:
                return setting
        return None
    
    def update_task_type_settings(self, task_type_settings: list[TaskTypeSettings]):
        self.task_type_settings = task_type_settings
        self.taskManager.task_type_settings = {setting.name: setting for setting in task_type_settings}
        return self.db.update_user_task_type_settings(self.username, task_type_settings)
    
    def update_difficulty_settings(self, difficulty_settings: list[DifficultySettings]):
        self.difficulty_settings = difficulty_settings
        self.taskManager.difficulty_settings = {setting.name: setting for setting in difficulty_settings}
        return self.db.update_user_difficulty_settings(self.username, difficulty_settings)
    
    def calculate_default_due_date(self, task_type: str, deadline: datetime) -> datetime:
        for setting in self.task_type_settings:
            if setting.name == task_type:
                return deadline - timedelta(days=setting.default_due_days_before_deadline)
        return deadline - timedelta(days=1)

    def add_task_with_deadline(self, title: str, category: str, task_type: str, deadline_input, difficulty: str = None, note: str = None):
        type_setting = None
        for setting in self.task_type_settings:
            if setting.name == task_type:
                type_setting = setting
                break
        
        task = Task(title=title, category=category, type=task_type, due=None, deadline=None, difficulty=difficulty, note=note)
        
        format_type = type_setting.deadline_format if type_setting else "date"
        task.set_deadline_with_time_setting(deadline_input, format_type)
        
        if type_setting:
            if format_type == "datetime":
                hours_before = type_setting.default_due_days_before_deadline * 24
                task.due = task.deadline - timedelta(hours=hours_before)
            else:
                days_before = type_setting.default_due_days_before_deadline
                due_date = task.deadline.date() - timedelta(days=days_before)
                task.due = datetime.combine(due_date, datetime.min.time().replace(hour=23, minute=59))
        else:
            task.due = task.deadline - timedelta(days=1)
        
        return self.add_task(task)
    
    def get_overdue_tasks(self) -> list[Task]:
        return self.taskManager.get_overdue_tasks()
    
    def get_urgent_tasks(self) -> list[Task]:
        return self.taskManager.get_urgent_tasks()
    
    def get_completed_tasks(self) -> list[Task]:
        return self.taskManager.get_completed_tasks()
    
    def get_deadline_format_for_type(self, task_type: str) -> str:
        for setting in self.task_type_settings:
            if setting.name == task_type:
                return setting.deadline_format
        return "date"
    
    def delete_task(self, task_id: str):
        original_count = len(self.tasks)
        self.tasks = [task for task in self.tasks if task.id != task_id]
        
        if len(self.tasks) < original_count:
            self.taskManager.tasks = self.tasks
            result = self.db.remove_task_from_user(self.username, task_id)
            return result
        else:
            return {"success": False, "response": "Task not found."}
    
    def get_task_by_id(self, task_id: str) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def mark_complete(self, task_id: str, complete: bool = True):
        for task in self.tasks:
            if task.id == task_id:
                task.complete = complete
                self.taskManager.tasks = self.tasks
                result = self.db.mark_task_complete(self.username, task_id, complete)
                return result
        return {"success": False, "response": "Task not found."}

def test():
    db = database("tasks.db")
    if not db.get_user("john_doe"):
        print(db.add_user("john_doe", "password123", "john.doe@gmail.com"))
    
    user_data = db.get_user("john_doe")
    if user_data:
        user_id = user_data["id"]
        user = User(user_id, db)
    else:
        print("User not found")
        return
    
    updated_settings = [
        TaskTypeSettings("Short term", 1, 1, "date", 0),
        TaskTypeSettings("Long term", 7, 14, "datetime", 1)
    ]
    user.update_task_type_settings(updated_settings)
    
    if not user.get_tasks():
        print("Creating homework task..")
        result1 = user.add_task("Math homework", "Homework", "Short term", "2025-06-13", "Hard")
        print(result1)
        
        print("Creating project task..")
        result2 = user.add_task("Research project", "Project", "Long term", "2025-06-30T15:30:00", "Medium")
        print(result2)
    
    print()
    print("Tasks:")
    for task in user.get_tasks():
        due_str = task.due.strftime("%Y-%m-%d %H:%M")
        deadline_str = task.deadline.strftime("%Y-%m-%d %H:%M")
        print(f"  {task.title}: Due {due_str}, Deadline {deadline_str}")
    
    print()
    print("Priority order:", [task.title for task in user.get_prioritized_tasks()])
    print("Urgent tasks:", [task.title for task in user.get_urgent_tasks()])
    print("Overdue tasks:", [task.title for task in user.get_overdue_tasks()])
    print("Completed tasks:", [task.title for task in user.get_completed_tasks()])
    
    print()
    print("Deadline formats:")
    print(f"Short term format: {user.get_deadline_format_for_type('Short term')}")
    print(f"Long term format: {user.get_deadline_format_for_type('Long term')}")

if __name__ == "__main__":
    test()