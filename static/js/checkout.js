/* Checkout: автокомпліт НП + клієнтська валідація полів. */
(() => {
  const form = document.querySelector("[data-checkout-form]");
  if (!form) return;

  const showFieldError = (fieldEl, message) => {
    if (!fieldEl) return;
    fieldEl.classList.add("has-error");
    let err = fieldEl.querySelector("[data-client-error]");
    if (!err) {
      err = document.createElement("span");
      err.className = "field-errors";
      err.dataset.clientError = "1";
      fieldEl.appendChild(err);
    }
    err.textContent = message;
  };

  const clearClientErrors = () => {
    form.querySelectorAll("[data-client-error]").forEach((el) => el.remove());
    form.querySelectorAll(".field.has-error").forEach((el) => {
      if (!el.querySelector(".field-errors:not([data-client-error])")) {
        el.classList.remove("has-error");
      }
    });
  };

  const fieldWrap = (input) => input?.closest(".field");

  const validate = () => {
    clearClientErrors();
    let firstInvalid = null;

    const requireText = (selector, message) => {
      const input = form.querySelector(selector);
      if (!input) return true;
      if (String(input.value || "").trim()) return true;
      showFieldError(fieldWrap(input), message);
      firstInvalid = firstInvalid || input;
      return false;
    };

    let ok = true;
    ok = requireText("#id_customer_name", "Вкажіть ім'я та прізвище.") && ok;
    ok = requireText("#id_customer_phone", "Вкажіть телефон.") && ok;

    const phone = form.querySelector("#id_customer_phone");
    if (phone && String(phone.value || "").trim()) {
      const digits = String(phone.value).replace(/[^\d+]/g, "");
      if (!/^\+?3?8?(0\d{9})$/.test(digits)) {
        showFieldError(fieldWrap(phone), "Введіть коректний український номер телефону.");
        firstInvalid = firstInvalid || phone;
        ok = false;
      }
    }

    const cityId = form.querySelector("[data-np-id='city']");
    const cityName = form.querySelector("[data-np-text='city']");
    const warehouseId = form.querySelector("[data-np-id='warehouse']");
    const warehouseName = form.querySelector("[data-np-text='warehouse']");
    const requireRefs = form.dataset.npRequireRefs === "1";

    if (requireRefs) {
      if (!cityId?.value) {
        showFieldError(fieldWrap(cityName), "Оберіть місто зі списку підказок.");
        firstInvalid = firstInvalid || cityName;
        ok = false;
      }
      if (!warehouseId?.value) {
        showFieldError(fieldWrap(warehouseName), "Оберіть відділення зі списку підказок.");
        firstInvalid = firstInvalid || warehouseName;
        ok = false;
      }
    } else {
      ok = requireText("[data-np-text='city']", "Вкажіть місто.") && ok;
      ok = requireText("[data-np-text='warehouse']", "Вкажіть відділення або поштомат.") && ok;
    }

    const consent = form.querySelector("#id_consent_gdpr");
    if (consent && !consent.checked) {
      const wrap = consent.closest(".checkout-card") || consent.parentElement;
      let err = wrap?.querySelector("[data-client-error='consent']");
      if (!err && wrap) {
        err = document.createElement("span");
        err.className = "field-errors";
        err.dataset.clientError = "consent";
        wrap.appendChild(err);
      }
      if (err) err.textContent = "Потрібно погодитись з умовами.";
      firstInvalid = firstInvalid || consent;
      ok = false;
    }

    if (firstInvalid) {
      firstInvalid.focus({ preventScroll: false });
      firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    return ok;
  };

  form.addEventListener("submit", (e) => {
    if (form.dataset.minBlocked === "1") {
      e.preventDefault();
      const banner = document.querySelector("[data-min-order-banner]");
      banner?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    if (!validate()) {
      e.preventDefault();
    }
  });

  document.body.addEventListener("click", (e) => {
    const option = e.target.closest("[data-np-select]");
    if (!option) return;
    e.preventDefault();

    const kind = option.dataset.npSelect; // "city" | "warehouse"
    const container = option.closest("[data-np-autocomplete]");
    if (!container) return;

    const textInput = container.querySelector("[data-np-text]");
    const idInput = container.querySelector("[data-np-id]");
    const optionsPanel = container.querySelector(".autocomplete-options");

    if (textInput) textInput.value = option.dataset.npLabel || "";
    if (idInput) idInput.value = option.dataset.npId || "";
    optionsPanel?.classList.remove("is-open");
    container.classList.remove("has-error");
    container.querySelector("[data-client-error]")?.remove();

    if (kind === "city") {
      const warehouseInput = document.querySelector("[data-np-text='warehouse']");
      const warehouseId = document.querySelector("[data-np-id='warehouse']");
      if (warehouseInput) warehouseInput.value = "";
      if (warehouseId) warehouseId.value = "";
    }
  });

  document.body.addEventListener("focusout", (e) => {
    const container = e.target.closest("[data-np-autocomplete]");
    if (!container) return;
    setTimeout(() => {
      if (!container.contains(document.activeElement)) {
        container.querySelector(".autocomplete-options")?.classList.remove("is-open");
      }
    }, 120);
  });

  document.body.addEventListener("htmx:afterSwap", (e) => {
    if (e.target.matches("[data-np-options]")) {
      e.target.classList.add("is-open");
    }
  });
})();
