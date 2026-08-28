/* Степер кількості в drawer/cart-сторінці — inline +/- на server-rendered формах,
 * зміна значення тригерить hx-post автоматично (hx-trigger="change" на input). */
(() => {
  document.body.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-qty-step]");
    if (!btn) return;
    const wrapper = btn.closest("[data-qty-wrapper]");
    const input = wrapper?.querySelector("input[name='quantity']");
    if (!input) return;

    const step = Number(btn.dataset.qtyStep);
    const min = Number(btn.dataset.qtyMin || "0");
    const decimals = Math.abs(step) < 1 ? 1 : 0;
    const raw = Number(input.value || 1) + step;
    // Крок < 0 (мінус) нижче мін. кількості → прибрати позицію (0), інакше клампимо до мін.
    const next = step < 0 && raw < min ? 0 : Math.max(min, raw);
    input.value = next.toFixed(decimals);
    input.dispatchEvent(new Event("change", { bubbles: true }));
  });
})();
