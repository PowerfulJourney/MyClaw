const STORAGE_KEY = "todo-demo-tasks";

const form = document.getElementById("todo-form");
const input = document.getElementById("todo-input");
const list = document.getElementById("todo-list");

let tasks = loadTasks();
render();

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  tasks.push({ id: crypto.randomUUID(), text, done: false });
  saveTasks();
  render();
  form.reset();
  input.focus();
});

list.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;

  const item = event.target.closest("li");
  const id = item?.dataset.id;
  if (!id) return;

  if (button.dataset.action === "toggle") {
    tasks = tasks.map((task) =>
      task.id === id ? { ...task, done: !task.done } : task
    );
  }

  if (button.dataset.action === "delete") {
    tasks = tasks.filter((task) => task.id !== id);
  }

  saveTasks();
  render();
});

function loadTasks() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveTasks() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

function render() {
  list.innerHTML = "";

  for (const task of tasks) {
    const li = document.createElement("li");
    li.className = `todo-item${task.done ? " done" : ""}`;
    li.dataset.id = task.id;

    li.innerHTML = `
      <span>${escapeHtml(task.text)}</span>
      <button data-action="toggle" type="button">${task.done ? "Undo" : "Done"}</button>
      <button data-action="delete" type="button">Delete</button>
    `;

    list.append(li);
  }
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
