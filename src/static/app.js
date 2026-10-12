// app.js: Клиент для панели администратора (REST + GraphQL)

const TOKEN_KEY = "vault_token";

// Универсальная функция запроса к REST-эндпоинту
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
    let errorMsg = data.detail || "Ошибка запроса к API";
    if (Array.isArray(errorMsg)) {
      errorMsg = errorMsg.map((e) => e.msg || JSON.stringify(e)).join(", ");
    } else if (typeof errorMsg === "object") {
      errorMsg = JSON.stringify(errorMsg);
    }
    throw new Error(errorMsg);
  }
  return data;
}

// Универсальная функция запроса к GraphQL-эндпоинту
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

  const result = await res.json().catch(() => ({}));
  if (result.errors && result.errors.length > 0) {
    throw new Error(result.errors[0].message);
  }
  return result.data;
}

// Инициализация при полной загрузке DOM
document.addEventListener("DOMContentLoaded", () => {
  const alertBox = document.getElementById("alertBox");
  const mainGrid = document.getElementById("mainGrid");
  const loginCard = document.getElementById("loginCard");
  const userHeader = document.getElementById("userHeader");
  const userEmail = document.getElementById("userEmail");
  const loginForm = document.getElementById("loginForm");
  const logoutBtn = document.getElementById("logoutBtn");
  const createClientBtn = document.getElementById("createClientBtn");
  const clientsBlock = document.getElementById("clientsBlock");
  const clientsTableBody = document.getElementById("clientsTableBody");
  const guestNotice = document.getElementById("guestNotice");

  let alertTimeout = null;
  let currentUser = null;

  function showAlert(message, type = "error") {
    if (alertTimeout) clearTimeout(alertTimeout);
    alertBox.className = `alert alert-${type} show`;
    alertBox.textContent = message;
    alertTimeout = setTimeout(() => {
      alertBox.classList.remove("show");
    }, 5000);
  }

  function toggleAuth(isAuth, user = null) {
    currentUser = isAuth ? user : null;
    if (isAuth && user) {
      if (loginCard) loginCard.classList.add("hidden");
      if (mainGrid) mainGrid.classList.add("auth-mode");

      const roleText = user.isAdmin ? "Администратор" : "Пользователь";
      userHeader.classList.remove("hidden");
      userEmail.textContent = `${user.email} (${roleText})`;

      clientsBlock.classList.remove("hidden");
      createClientBtn.classList.remove("hidden");
      guestNotice.classList.add("hidden");

      loadClients();
    } else {
      currentUser = null;
      if (loginCard) loginCard.classList.remove("hidden");
      if (mainGrid) mainGrid.classList.remove("auth-mode");

      userHeader.classList.add("hidden");
      userEmail.textContent = "";

      clientsBlock.classList.add("hidden");
      createClientBtn.classList.add("hidden");
      guestNotice.classList.remove("hidden");

      clientsTableBody.innerHTML = "";
    }
  }

  async function loadClients() {
    try {
      if (!currentUser || !currentUser.isAdmin) {
        clientsTableBody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
              Просмотр и создание OAuth-клиентов доступны только администраторам.
            </td>
          </tr>
        `;
        return;
      }

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
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      console.log("[Vault Admin] Отправка формы входа...");
      const emailInput = document.getElementById("loginEmail");
      const passwordInput = document.getElementById("loginPassword");
      const email = emailInput ? emailInput.value.trim() : "";
      const password = passwordInput ? passwordInput.value : "";

      if (!email || !password) {
        showAlert("Заполните email и пароль", "error");
        return;
      }

      try {
        console.log(`[Vault Admin] Запрос /auth/login для ${email}...`);
        const res = await api("/auth/login", { email, password });
        if (!res.access_token) {
          throw new Error("Токен авторизации не получен от сервера");
        }
        localStorage.setItem(TOKEN_KEY, res.access_token);

        // Получаем информацию о пользователе и его роли
        const meData = await gql(`
          query {
            me {
              id
              email
              isAdmin
            }
          }
        `);
        const user = (meData && meData.me) ? meData.me : { email, isAdmin: false };
        toggleAuth(true, user);
        showAlert("Вход выполнен успешно", "success");
        console.log("[Vault Admin] Вход успешен!", user);
      } catch (err) {
        console.error("[Vault Admin] Ошибка входа:", err);
        showAlert(err.message, "error");
      }
    });
  }

  // Обработка кнопки выхода
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem(TOKEN_KEY);
      toggleAuth(false);
      showAlert("Вы вышли из системы", "success");
    });
  }

  // Элементы модального окна создания клиента
  const createClientModal = document.getElementById("createClientModal");
  const createClientModalForm = document.getElementById("createClientModalForm");
  const closeClientModalXBtn = document.getElementById("closeClientModalXBtn");
  const cancelClientModalBtn = document.getElementById("cancelClientModalBtn");
  const modalClientName = document.getElementById("modalClientName");
  const modalIsConfidential = document.getElementById("modalIsConfidential");
  const urisEmptyMsg = document.getElementById("urisEmptyMsg");
  const urisList = document.getElementById("urisList");
  const openAddUriPromptBtn = document.getElementById("openAddUriPromptBtn");

  // Элементы всплывающего окна ввода ссылки
  const uriPromptModal = document.getElementById("uriPromptModal");
  const uriPromptForm = document.getElementById("uriPromptForm");
  const closeUriPromptXBtn = document.getElementById("closeUriPromptXBtn");
  const cancelUriPromptBtn = document.getElementById("cancelUriPromptBtn");
  const promptUriInput = document.getElementById("promptUriInput");
  const promptUriError = document.getElementById("promptUriError");

  let currentRedirectUris = [];

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function renderUrisList() {
    if (currentRedirectUris.length === 0) {
      if (urisEmptyMsg) urisEmptyMsg.classList.remove("hidden");
      if (urisList) urisList.innerHTML = "";
      return;
    }

    if (urisEmptyMsg) urisEmptyMsg.classList.add("hidden");
    if (!urisList) return;

    urisList.innerHTML = currentRedirectUris
      .map(
        (uri, index) => `
        <div class="uri-item">
          <span class="uri-text">${escapeHtml(uri)}</span>
          <button type="button" class="btn-circle btn-circle-remove" data-index="${index}" title="Удалить ссылку">−</button>
        </div>
      `
      )
      .join("");

    urisList.querySelectorAll(".btn-circle-remove").forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.dataset.index, 10);
        if (!isNaN(idx) && idx >= 0 && idx < currentRedirectUris.length) {
          currentRedirectUris.splice(idx, 1);
          renderUrisList();
        }
      });
    });
  }

  function openCreateClientModal() {
    currentRedirectUris = [];
    if (modalClientName) modalClientName.value = "";
    if (modalIsConfidential) modalIsConfidential.checked = false;
    renderUrisList();
    if (createClientModal) {
      createClientModal.classList.remove("hidden");
      if (modalClientName) modalClientName.focus();
    }
  }

  function closeCreateClientModal() {
    if (createClientModal) createClientModal.classList.add("hidden");
  }

  function openUriPromptModal() {
    if (promptUriInput) promptUriInput.value = "";
    if (promptUriError) {
      promptUriError.textContent = "";
      promptUriError.classList.add("hidden");
    }
    if (uriPromptModal) {
      uriPromptModal.classList.remove("hidden");
      if (promptUriInput) promptUriInput.focus();
    }
  }

  function closeUriPromptModal() {
    if (uriPromptModal) uriPromptModal.classList.add("hidden");
  }

  if (createClientBtn) {
    createClientBtn.addEventListener("click", () => {
      if (!currentUser || !currentUser.isAdmin) {
        showAlert("Ошибка: только администраторы могут создавать клиентов", "error");
        return;
      }
      openCreateClientModal();
    });
  }

  if (closeClientModalXBtn) {
    closeClientModalXBtn.addEventListener("click", closeCreateClientModal);
  }

  if (cancelClientModalBtn) {
    cancelClientModalBtn.addEventListener("click", closeCreateClientModal);
  }

  if (createClientModal) {
    createClientModal.addEventListener("click", (e) => {
      if (e.target === createClientModal) closeCreateClientModal();
    });
  }

  if (openAddUriPromptBtn) {
    openAddUriPromptBtn.addEventListener("click", () => {
      openUriPromptModal();
    });
  }

  if (closeUriPromptXBtn) {
    closeUriPromptXBtn.addEventListener("click", closeUriPromptModal);
  }

  if (cancelUriPromptBtn) {
    cancelUriPromptBtn.addEventListener("click", closeUriPromptModal);
  }

  if (uriPromptModal) {
    uriPromptModal.addEventListener("click", (e) => {
      if (e.target === uriPromptModal) closeUriPromptModal();
    });
  }

  if (uriPromptForm) {
    uriPromptForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const val = promptUriInput ? promptUriInput.value.trim() : "";
      if (!val) {
        if (promptUriError) {
          promptUriError.textContent = "Введите URL перенаправления";
          promptUriError.classList.remove("hidden");
        }
        return;
      }

      if (currentRedirectUris.includes(val)) {
        if (promptUriError) {
          promptUriError.textContent = "Такая ссылка уже добавлена";
          promptUriError.classList.remove("hidden");
        }
        return;
      }

      currentRedirectUris.push(val);
      renderUrisList();
      closeUriPromptModal();
    });
  }

  if (createClientModalForm) {
    createClientModalForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!currentUser || !currentUser.isAdmin) {
        showAlert("Ошибка: только администраторы могут создавать клиентов", "error");
        return;
      }

      const name = modalClientName ? modalClientName.value.trim() : "";
      const isConfidential = modalIsConfidential ? modalIsConfidential.checked : false;

      if (!name) {
        showAlert("Укажите имя клиента", "error");
        return;
      }

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
        console.log(`[Vault Admin] Создание клиента "${name}"...`);
        await gql(mutation, {
          name,
          isConfidential,
          redirectUris: currentRedirectUris,
        });
        closeCreateClientModal();
        showAlert(`Клиент "${name}" успешно создан`, "success");
        loadClients();
      } catch (err) {
        console.error("[Vault Admin] Ошибка создания клиента:", err);
        showAlert(err.message, "error");
      }
    });
  }

  // Закрытие активного модального окна по нажатию Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (uriPromptModal && !uriPromptModal.classList.contains("hidden")) {
        closeUriPromptModal();
      } else if (createClientModal && !createClientModal.classList.contains("hidden")) {
        closeCreateClientModal();
      }
    }
  });

  // Проверка сессии при старте
  async function checkAuthSession() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      console.log("[Vault Admin] Токен отсутствует, режим гостя");
      toggleAuth(false);
      return;
    }

    try {
      console.log("[Vault Admin] Проверка валидности сохраненного токена через GraphQL query { me }...");
      const data = await gql(`
        query {
          me {
            id
            email
            isAdmin
          }
        }
      `);
      if (data && data.me) {
        console.log("[Vault Admin] Сессия успешно подтверждена:", data.me);
        toggleAuth(true, data.me);
      } else {
        console.warn("[Vault Admin] Токен недействителен, сброс");
        localStorage.removeItem(TOKEN_KEY);
        toggleAuth(false);
      }
    } catch (err) {
      console.warn("[Vault Admin] Ошибка проверки сессии:", err.message);
      localStorage.removeItem(TOKEN_KEY);
      toggleAuth(false);
    }
  }

  checkAuthSession();
});
