const API_BASE = 'https://someonecool.pythonanywhere.com/';
let currentUser = null;

function updateStatus(message) {
    document.getElementById('status').textContent = message;
}

async function register() {
    const email = document.getElementById('reg-email').value;
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, username, password })
        });
        
        const data = await response.json();
        updateStatus(response.ok ? data.message : data.error);
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        if (response.ok) {
            updateStatus('Logged in successfully');
            getCurrentUser();
        } else {
            updateStatus(data.error);
        }
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

async function logout() {
    try {
        const response = await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        updateStatus('Logged out');
        currentUser = null;
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

async function getCurrentUser() {
    try {
        const response = await fetch(`${API_BASE}/me`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = await response.json();
            updateStatus(`Logged in as ${currentUser.username}`);
            loadTasks();
        } else {
            updateStatus('Not logged in');
        }
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

async function addTask() {
    const title = document.getElementById('task-title').value;
    const category = document.getElementById('task-category').value;
    const type = document.getElementById('task-type').value;
    const difficulty = document.getElementById('task-difficulty').value;
    const deadline = document.getElementById('task-deadline').value;
    const note = document.getElementById('task-note').value;
    
    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ title, category, type, difficulty, deadline, note })
        });
        
        const data = await response.json();
        updateStatus(response.ok ? data.message : data.error);
        if (response.ok) {
            document.getElementById('task-title').value = '';
            document.getElementById('task-category').value = '';
            document.getElementById('task-note').value = '';
            loadTasks();
        }
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const tasks = await response.json();
            displayTasks(tasks);
        } else {
            updateStatus('Failed to load tasks');
        }
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

function displayTasks(tasks) {
    displayTaskList('overdue-tasks', tasks.overdue, 'overdue');
    displayTaskList('urgent-tasks', tasks.urgent, 'urgent');
    displayTaskList('regular-tasks', tasks.prioritized, '');
}

function displayTaskList(containerId, tasks, className) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    tasks.forEach(task => {
        const taskDiv = document.createElement('div');
        taskDiv.className = `task-item ${className}`;
        taskDiv.innerHTML = `
            <div class="task-info">
                <div class="task-title">${task.title}</div>
                <div class="task-meta">${task.category} • ${task.type} • ${task.difficulty}</div>
                <div class="task-meta">Due: ${new Date(task.deadline).toLocaleDateString()}</div>
            </div>
            <div class="task-actions">
                <button class="btn-small btn-success" onclick="toggleComplete('${task.id}')">
                    ${task.complete ? 'Undo' : 'Complete'}
                </button>
                <button class="btn-small btn-danger" onclick="deleteTask('${task.id}')">Delete</button>
            </div>
        `;
        container.appendChild(taskDiv);
    });
}

async function toggleComplete(taskId) {
    try {
        const response = await fetch(`${API_BASE}/tasks/complete/${taskId}`, {
            method: 'PUT',
            credentials: 'include'
        });
        
        const data = await response.json();
        updateStatus(response.ok ? data.message : data.error);
        if (response.ok) loadTasks();
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

async function deleteTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        updateStatus(response.ok ? data.message : data.error);
        if (response.ok) loadTasks();
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

async function loadCompletedTasks() {
    try {
        const response = await fetch(`${API_BASE}/tasks/completed`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const tasks = await response.json();
            displayTaskList('completed-tasks', tasks, 'completed');
        } else {
            updateStatus('Failed to load completed tasks');
        }
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/settings`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const settings = await response.json();
            displaySettings(settings);
        } else {
            updateStatus('Failed to load settings');
        }
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

function displaySettings(settings) {
    const typesContainer = document.getElementById('task-types-settings');
    const diffsContainer = document.getElementById('difficulties-settings');
    
    typesContainer.innerHTML = '';
    diffsContainer.innerHTML = '';
    
    settings.task_types.forEach(type => {
        const div = document.createElement('div');
        div.className = 'priority-item';
        div.innerHTML = `
            <span>${type.name}</span>
            <span>Priority: ${type.priority_rank}</span>
        `;
        typesContainer.appendChild(div);
    });
    
    settings.difficulties.forEach(diff => {
        const div = document.createElement('div');
        div.className = 'priority-item';
        div.innerHTML = `
            <span>${diff.name}</span>
            <span>Priority: ${diff.priority_rank}</span>
        `;
        diffsContainer.appendChild(div);
    });
}

async function updatePriorityOrder() {
    const orderData = {
        task_types_order: ['Short term', 'Long term'],
        difficulties_order: ['Hard', 'Medium', 'Easy']
    };
    
    try {
        const response = await fetch(`${API_BASE}/settings/priority-order`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(orderData)
        });
        
        const data = await response.json();
        updateStatus(response.ok ? data.message : data.error);
        if (response.ok) loadSettings();
    } catch (error) {
        updateStatus('Error: ' + error.message);
    }
}

getCurrentUser();
