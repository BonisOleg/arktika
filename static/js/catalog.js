/* Навігація по вибору сортування на PLP (без inline onchange). */
(() => {
  document.body.addEventListener("change", (e) => {
    const select = e.target.closest("[data-sort-navigate]");
    if (!select) return;
    window.location.href = select.value;
  });
})();
