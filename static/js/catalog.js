/* Кастомне сортування на PLP (без нативного select). */
(() => {
  const closeAll = (except) => {
    document.querySelectorAll("[data-custom-select].is-open").forEach((el) => {
      if (except && el === except) return;
      el.classList.remove("is-open");
      const trigger = el.querySelector("[data-custom-select-trigger]");
      const menu = el.querySelector("[data-custom-select-menu]");
      if (trigger) trigger.setAttribute("aria-expanded", "false");
      if (menu) menu.hidden = true;
    });
  };

  document.body.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-custom-select-trigger]");
    if (trigger) {
      e.preventDefault();
      const root = trigger.closest("[data-custom-select]");
      if (!root) return;
      const willOpen = !root.classList.contains("is-open");
      closeAll(root);
      const menu = root.querySelector("[data-custom-select-menu]");
      root.classList.toggle("is-open", willOpen);
      trigger.setAttribute("aria-expanded", willOpen ? "true" : "false");
      if (menu) menu.hidden = !willOpen;
      return;
    }

    const option = e.target.closest("[data-custom-select-option]");
    if (option) {
      const href = option.getAttribute("data-href");
      if (href) window.location.href = href;
      return;
    }

    if (!e.target.closest("[data-custom-select]")) {
      closeAll();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAll();
  });
})();
