// app.js: Минималистичный клиент для админки (REST + GraphQL)

const TOKEN_KEY = "vault_token";

// 1. Универсальная функция запроса к REST-эндпоинту
async function api(path, body) {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(path, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || "Ошибка запроса к API");
  }
  return data;
}

// 2. Универсальная функция запроса к GraphQL-эндпоинту
async function gql(query, variables = {}) {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch("/graphql/", {
    method: "POST",
    headers,
    body: JSON.stringify({ query, variables }),
  });

  const result = await res.json();
  if (result.errors && result.errors.length > 0) {
    throw new Error(result.errors[0].message);
  }
  return result.data;
}

// Элементы интерфейса
const alertBox = document.getElementById("alertBox");
const loginBlock = document.getElementById("loginBlock");
const profileBlock = document.getElementById("profileBlock");
const profileEmail = document.getElementById("profileEmail");
const userHeader = document.getElementById("userHeader");
const userEmail = document.getElementById("userEmail");
const loginForm = document.getElementById("loginForm");
const logoutBtn = document.getElementById("logoutBtn");
const createClientBtn = document.getElementById("createClientBtn");
const clientsBlock = document.getElementById("clientsBlock");
const clientsTableBody = document.getElementById("clientsTableBody");
const guestNotice = document.getElementById("guestNotice");

// Вспомогательный вывод уведомлений
let alertTimeout = null;
function showAlert(message, type = "error") {
  if (alertTimeout) clearTimeout(alertTimeout);
  alertBox.className = `alert alert-${type}`;
  alertBox.textContent = message;
  alertBox.style.display = "block";
  alertTimeout = setTimeout(() => {
    alertBox.style.display = "none";
  }, 4500);
}

// 3. Переключение видимости блоков по статусу авторизации
function toggleAuth(isAuth, email = "") {
  if (isAuth) {
    loginBlock.classList.add("hidden");
    profileBlock.classList.remove("hidden");
    profileEmail.textContent = email;

    userHeader.classList.remove("hidden");
    userEmail.textContent = email;

    clientsBlock.classList.remove("hidden");
    createClientBtn.classList.remove("hidden");
    guestNotice.classList.add("hidden");

    loadClients();
  } else {
    loginBlock.classList.remove("hidden");
    profileBlock.classList.add("hidden");
    profileEmail.textContent = "";

    userHeader.classList.add("hidden");
    userEmail.textContent = "";

    clientsBlock.classList.add("hidden");
    createClientBtn.classList.add("hidden");
    guestNotice.classList.remove("hidden");

    clientsTableBody.innerHTML = "";
  }
}

// 4. Загрузка списка клиентов через GraphQL Query
async function loadClients() {
  try {
    clientsTableBody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
          Загрузка клиентов...
        </td>
      </tr>
    `;

    const data = await gql(`
      query {
        clients {
          id
          clientId
          name
          isConfidential
          redirectUris
        }
      }
    `);

    const clients = data.clients || [];
    if (clients.length === 0) {
      clientsTableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
            Клиенты пока не зарегистрированы
          </td>
        </tr>
      `;
      return;
    }

    clientsTableBody.innerHTML = clients
      .map(
        (c) => `
        <tr>
          <td>${c.id}</td>
          <td><code>${c.clientId}</code></td>
          <td><strong>${c.name}</strong></td>
          <td>
            <span class="badge ${c.isConfidential ? "badge-confidential" : "badge-public"}">
              ${c.isConfidential ? "Confidential" : "Public"}
            </span>
          </td>
          <td>${(c.redirectUris || []).join(", ") || "—"}</td>
        </tr>
      `
      )
      .join("");
  } catch (err) {
    showAlert(err.message, "error");
    clientsTableBody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; color: var(--danger); padding: 1.5rem;">
          Не удалось загрузить данные
        </td>
      </tr>
    `;
  }
}

// Обработка отправки формы логина
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  try {
    const res = await api("/auth/login", { email, password });
    localStorage.setItem(TOKEN_KEY, res.access_token);
    toggleAuth(true, email);
    showAlert("Вход выполнен успешно", "success");
  } catch (err) {
    showAlert(err.message, "error");
  }
});

// Кнопка "Выйти" — очистка localStorage и сброс состояния
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem(TOKEN_KEY);
  toggleAuth(false);
  showAlert("Вы вышли из системы", "success");
});

// Кнопка "Создать клиента" — отправка GraphQL Mutation createClient
createClientBtn.addEventListener("click", async () => {
  const name = prompt("Введите имя нового OAuth-клиента:");
  if (!name || !name.trim()) return;

  const urisRaw = prompt(
    "Введите разрешенные Redirect URIs (через запятую):",
    "http://localhost:3000/callback"
  );
  const redirectUris = urisRaw
    ? urisRaw.split(",").map((s) => s.trim()).filter(Boolean)
    : [];

  const isConfidential = confirm(
    "Сделать клиента конфиденциальным (Confidential)?\n[ОК = Да / Отмена = Public]"
  );

  const mutation = `
    mutation CreateClient($name: String!, $isConfidential: Boolean!, $redirectUris: [String!]) {
      createClient(name: $name, isConfidential: $isConfidential, redirectUris: $redirectUris) {
        id
        clientId
        name
        isConfidential
        redirectUris
      }
    }
  `;

  try {
    await gql(mutation, {
      name: name.trim(),
      isConfidential,
      redirectUris,
    });
    showAlert(`Клиент "${name.trim()}" успешно создан`, "success");
    loadClients();
  } catch (err) {
    showAlert(err.message, "error");
  }
});

// Восстановление сессии при обновлении страницы
async function checkAuthSession() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) {
    toggleAuth(false);
    return;
  }

  try {
    const data = await gql(`
      query {
        me {
          id
          email
        }
      }
    `);
    if (data && data.me) {
      toggleAuth(true, data.me.email);
    } else {
      localStorage.removeItem(TOKEN_KEY);
      toggleAuth(false);
    }
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    toggleAuth(false);
  }
}

document.addEventListener("DOMContentLoaded", checkAuthSession);
