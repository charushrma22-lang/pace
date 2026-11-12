
document.addEventListener("DOMContentLoaded", () => {
    const API = "/api";

    // ==============================
    // COMMON API FUNCTION
    // ==============================

    async function apiRequest(url, method = "GET", data = null) {
        const options = {
            method,
            headers: { "Content-Type": "application/json" }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(
    error.message || error.error || "Something went wrong."
);
        }

        if (response.status === 204) return null;

        return response.json();
    }

    function showError(error) {
        alert(error.message || "Something went wrong.");
    }

    // ==============================
    // HABITS
    // ==============================

    const habitPanel = document.querySelector(".habits-panel");
    const addHabitBtn = document.querySelector("#add-habit-btn");

    let habits = [];

    const habitList = document.createElement("div");
    habitList.className = "habit-list";

    if (habitPanel) {
        habitPanel.appendChild(habitList);
    }

    // Habit modal
    const habitModal = document.createElement("div");

    habitModal.className = "habit-modal";
    habitModal.innerHTML = `
        <div class="habit-modal-content">
            <h2>Add a New Habit</h2>
            <p>Build a small habit every day.</p>

            <form id="habit-form">
                <label for="habit-name">Habit Name</label>
                <input id="habit-name" type="text"
                    placeholder="e.g. Read for 20 minutes"
                    maxlength="100" required>

                <label for="habit-description">Description</label>
                <textarea id="habit-description"
                    placeholder="Optional description"></textarea>

                <div class="habit-modal-actions">
                    <button type="button" id="cancel-habit">Cancel</button>
                    <button type="submit">Save Habit</button>
                </div>
            </form>
        </div>
    `;

    document.body.appendChild(habitModal);

    function openHabitModal() {
        habitModal.classList.add("show");
        document.querySelector("#habit-name").focus();
    }

    function closeHabitModal() {
        habitModal.classList.remove("show");
        document.querySelector("#habit-form").reset();
    }

    addHabitBtn?.addEventListener("click", openHabitModal);

    document.querySelector("#cancel-habit")
        .addEventListener("click", closeHabitModal);

    habitModal.addEventListener("click", event => {
        if (event.target === habitModal) closeHabitModal();
    });

    document.querySelector("#habit-form")
        .addEventListener("submit", async event => {
            event.preventDefault();

            const name = document.querySelector("#habit-name").value.trim();
            const description = document.querySelector("#habit-description").value.trim();

            if (!name) return;

            try {
                await apiRequest(`${API}/habits`, "POST", {
                    name,
                    description
                });

                closeHabitModal();
                await loadHabits();
            } catch (error) {
                showError(error);
            }
        });

    function renderHabits() {
        habitList.innerHTML = "";

        const emptyState = habitPanel?.querySelector(".empty-state");

        if (emptyState) {
            emptyState.style.display = habits.length ? "none" : "";
        }

        habits.forEach(habit => {
            const item = document.createElement("div");
            item.className = "habit-item";

            const heading = document.createElement("h4");
            heading.textContent = habit.name;

            const description = document.createElement("p");
            description.textContent = habit.description || "No description";

            const actions = document.createElement("div");
            actions.className = "habit-actions";

            const completeBtn = document.createElement("button");
            completeBtn.textContent = habit.completed ? "Undo" : "Complete";
            completeBtn.className = "habit-action-btn";

            completeBtn.addEventListener("click", async () => {
                try {
                    await apiRequest(
                        `${API}/habits/${habit.id}`,
                        "PATCH",
                        { completed: !habit.completed }
                    );

                    await loadHabits();
                } catch (error) {
                    showError(error);
                }
            });

            const deleteBtn = document.createElement("button");
            deleteBtn.textContent = "Delete";
            deleteBtn.className = "habit-delete-btn";

            deleteBtn.addEventListener("click", async () => {
                if (!confirm("Delete this habit?")) return;

                try {
                    await apiRequest(
                        `${API}/habits/${habit.id}`,
                        "DELETE"
                    );

                    await loadHabits();
                } catch (error) {
                    showError(error);
                }
            });

            if (habit.completed) {
                item.classList.add("completed");
            }

            actions.append(completeBtn, deleteBtn);
            item.append(heading, description, actions);
            habitList.appendChild(item);
        });

        updateHabitStats();
    }

    async function loadHabits() {
        try {
            habits = await apiRequest(`${API}/habits`);
            renderHabits();
        } catch (error) {
            showError(error);
        }
    }

    function updateHabitStats() {
        const cards = document.querySelectorAll(".stats-grid .stat-card");

        const completed = habits.filter(habit => habit.completed).length;
        const total = habits.length;

        const percentage = total
            ? Math.round((completed / total) * 100)
            : 0;

        if (cards[0]) {
            const heading = cards[0].querySelector("h2");
            const label = cards[0].querySelector("p");

            if (heading) heading.textContent = `${percentage}%`;
            if (label) label.textContent = "Habit Completion";

            const fill = cards[0].querySelector(".progress-fill");
            if (fill) fill.style.width = `${percentage}%`;
        }

        if (cards[1]) {
            const heading = cards[1].querySelector("h2");
            if (heading) heading.textContent = total;
        }
    }

    // ==============================
    // DAILY PLANNER
    // ==============================

    const plannerPanel = document.querySelector(".planner-panel");

    let tasks = [];
    let editingTaskId = null;

    const taskList = document.createElement("div");
    taskList.className = "task-list";

    if (plannerPanel) {
        plannerPanel.appendChild(taskList);
    }

    // Add Task button
    const plannerHeader = plannerPanel?.querySelector("h2, h3");

    const addTaskBtn = document.createElement("button");
    addTaskBtn.textContent = "+ Add Task";
    addTaskBtn.className = "add-task-btn";

    if (plannerHeader) {
        plannerHeader.parentElement.appendChild(addTaskBtn);
    }

    // Task modal
    const taskModal = document.createElement("div");
    taskModal.className = "task-modal";

    taskModal.innerHTML = `
        <div class="task-modal-content">
            <h2 id="task-modal-title">Add a Task</h2>
            <p>Plan your day one task at a time.</p>

            <form id="task-form">
                <label for="task-title">Task Title</label>
                <input id="task-title" type="text"
                    placeholder="e.g. Complete Python assignment"
                    maxlength="150" required>

                <label for="task-description">Description</label>
                <textarea id="task-description"
                    maxlength="300"
                    placeholder="Optional details"></textarea>

                <label for="task-date">Due Date</label>
                <input id="task-date" type="date">

                <label for="task-priority">Priority</label>
                <select id="task-priority">
                    <option value="Low">Low</option>
                    <option value="Medium" selected>Medium</option>
                    <option value="High">High</option>
                </select>

                <div class="task-modal-actions">
                    <button type="button" id="cancel-task">Cancel</button>
                    <button type="submit" id="save-task">Save Task</button>
                </div>
            </form>
        </div>
    `;

    document.body.appendChild(taskModal);

    function openTaskModal(task = null) {
        editingTaskId = task ? task.id : null;

        document.querySelector("#task-modal-title").textContent =
            task ? "Edit Task" : "Add a Task";

        document.querySelector("#task-title").value =
            task?.title || "";

        document.querySelector("#task-description").value =
            task?.description || "";

        document.querySelector("#task-date").value =
            task?.due_date || "";

        document.querySelector("#task-priority").value =
            task?.priority || "Medium";

        taskModal.classList.add("show");
        document.querySelector("#task-title").focus();
    }

    function closeTaskModal() {
        taskModal.classList.remove("show");
        document.querySelector("#task-form").reset();
        editingTaskId = null;
    }

    addTaskBtn.addEventListener("click", () => openTaskModal());

    document.querySelector("#cancel-task")
        .addEventListener("click", closeTaskModal);

    taskModal.addEventListener("click", event => {
        if (event.target === taskModal) closeTaskModal();
    });

    document.querySelector("#task-form")
        .addEventListener("submit", async event => {
            event.preventDefault();

            const taskData = {
                title: document.querySelector("#task-title").value.trim(),
                description: document.querySelector("#task-description").value.trim(),
                due_date: document.querySelector("#task-date").value || null,
                priority: document.querySelector("#task-priority").value
            };

            if (!taskData.title) return;

            try {
                if (editingTaskId) {
                    await apiRequest(
                        `${API}/tasks/${editingTaskId}`,
                        "PATCH",
                        taskData
                    );
                } else {
                    await apiRequest(
                        `${API}/tasks`,
                        "POST",
                        taskData
                    );
                }

                closeTaskModal();
                await loadTasks();
            } catch (error) {
                showError(error);
            }
        });

    function formatDate(dateString) {
        if (!dateString) return "No due date";

        const [year, month, day] = dateString.split("-");

        return `${day}/${month}/${year}`;
    }

    function renderTasks() {
        taskList.innerHTML = "";

        const emptyState = plannerPanel?.querySelector(".empty-state.compact");

        if (emptyState) {
            emptyState.style.display = tasks.length ? "none" : "";
        }

        tasks.forEach(task => {
            const item = document.createElement("div");
            item.className = "task-item";

            if (task.completed) {
                item.classList.add("completed");
            }

            const details = document.createElement("div");
            details.className = "task-details";

            const title = document.createElement("h4");
            title.textContent = task.title;

            const description = document.createElement("p");
            description.textContent = task.description || "No description";

            const meta = document.createElement("p");
            meta.className = "task-meta";
            meta.textContent =
                `${formatDate(task.due_date)} • ${task.priority} priority`;

            details.append(title, description, meta);

            const actions = document.createElement("div");
            actions.className = "task-actions";

            const completeBtn = document.createElement("button");
            completeBtn.textContent = task.completed ? "Undo" : "Done";

            completeBtn.addEventListener("click", async () => {
                try {
                    await apiRequest(
                        `${API}/tasks/${task.id}`,
                        "PATCH",
                        { completed: !task.completed }
                    );

                    await loadTasks();
                } catch (error) {
                    showError(error);
                }
            });

            const editBtn = document.createElement("button");
            editBtn.textContent = "Edit";

            editBtn.addEventListener("click", () => openTaskModal(task));

            const deleteBtn = document.createElement("button");
            deleteBtn.textContent = "Delete";

            deleteBtn.addEventListener("click", async () => {
                if (!confirm("Delete this task?")) return;

                try {
                    await apiRequest(
                        `${API}/tasks/${task.id}`,
                        "DELETE"
                    );

                    await loadTasks();
                } catch (error) {
                    showError(error);
                }
            });

            actions.append(completeBtn, editBtn, deleteBtn);
            item.append(details, actions);
            taskList.appendChild(item);
        });
    }

    async function loadTasks() {
        try {
            tasks = await apiRequest(`${API}/tasks`);
            renderTasks();
        } catch (error) {
            showError(error);
        }
    }

    // ==============================
    // START THE APP
    // ==============================

    loadHabits();
    loadTasks();
});
