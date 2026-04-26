(function () {
  const API = "/api";

  const el = (id) => document.getElementById(id);
  const showErr = (msg) => {
    const box = el("err");
    box.textContent = msg || "";
    box.classList.toggle("visible", !!msg);
  };

  const setStep = (n) => {
    document.querySelectorAll(".step").forEach((s, i) => {
      s.classList.toggle("active", i <= n);
    });
  };

  let phone = "";
  let phoneCodeHash = "";
  let tempSession = "";

  const formPhone = el("form-phone");
  const formCode = el("form-code");
  const form2fa = el("form-2fa");

  el("title").textContent = "Вход в аккаунт";
  el("subtitle").textContent = "Укажите номер телефона, привязанный к Telegram";

  formPhone.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr("");
    const btn = el("btn-phone");
    btn.disabled = true;
    phone = el("phone").value.trim();
    try {
      const r = await fetch(`${API}/auth/send-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.detail || "Не удалось отправить код");
      }
      const data = await r.json();
      phoneCodeHash = data.phone_code_hash;
      tempSession = data.temp_session;
      formPhone.classList.add("hidden");
      formCode.classList.remove("hidden");
      el("code").focus();
      setStep(1);
      el("subtitle").textContent = "Введите код из приложения Telegram";
    } catch (err) {
      showErr(err.message || String(err));
    } finally {
      btn.disabled = false;
    }
  });

  el("back-phone").addEventListener("click", () => {
    showErr("");
    formCode.classList.add("hidden");
    form2fa.classList.add("hidden");
    formPhone.classList.remove("hidden");
    setStep(0);
    el("subtitle").textContent = "Укажите номер телефона, привязанный к Telegram";
  });

  async function loginWithCode() {
    showErr("");
    const btn = el("btn-code");
    btn.disabled = true;
    const code = el("code").value.trim();
    try {
      const r = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          phone,
          code,
          phone_code_hash: phoneCodeHash,
          temp_session: tempSession,
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (r.status === 401) {
        throw new Error(data.detail || "Неверный код или ошибка входа");
      }
      if (!r.ok) {
        throw new Error(data.detail || "Ошибка сервера");
      }
      if (data.status === "need_password") {
        tempSession = data.temp_session;
        formCode.classList.add("hidden");
        form2fa.classList.remove("hidden");
        setStep(2);
        el("subtitle").textContent = "Включена двухфакторная аутентификация";
        el("password").focus();
        return;
      }
      if (data.status === "success") {
        window.location.href = "/chats";
        return;
      }
      throw new Error("Неожиданный ответ сервера");
    } catch (err) {
      showErr(err.message || String(err));
    } finally {
      btn.disabled = false;
    }
  }

  formCode.addEventListener("submit", async (e) => {
    e.preventDefault();
    await loginWithCode();
  });

  form2fa.addEventListener("submit", async (e) => {
    e.preventDefault();
    showErr("");
    const btn = el("btn-2fa");
    btn.disabled = true;
    const password = el("password").value;
    try {
      const r = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          phone,
          code: el("code").value.trim(),
          phone_code_hash: phoneCodeHash,
          temp_session: tempSession,
          password,
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (r.status === 401) {
        throw new Error(data.detail || "Неверный облачный пароль");
      }
      if (!r.ok) {
        throw new Error(data.detail || "Ошибка сервера");
      }
      if (data.status === "success") {
        window.location.href = "/chats";
        return;
      }
      throw new Error(data.detail || "Ошибка входа");
    } catch (err) {
      showErr(err.message || String(err));
    } finally {
      btn.disabled = false;
    }
  });

  fetch(`${API}/auth/me`, { credentials: "include" })
    .then((r) => r.json())
    .then((d) => {
      if (d.authenticated) {
        window.location.href = "/chats";
      }
    })
    .catch(() => {});
})();
