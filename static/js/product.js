(() => {
  const qtyOut = document.querySelector("[data-qty]");
  const qtyMinus = document.querySelector("[data-qty-minus]");
  const qtyPlus = document.querySelector("[data-qty-plus]");
  const qtyInput = document.querySelector("[data-qty-input]");
  const qtyInputBuyNow = document.querySelector("[data-qty-input-buynow]");
  const qtyHint = document.querySelector("[data-qty-hint]");
  const lineTotalEl = document.querySelector("[data-line-total]");
  const priceEl = document.querySelector("[data-price]");
  const unitSuffixEl = document.querySelector("[data-unit-suffix]");
  const unitSpecEl = document.querySelector("[data-unit-spec]");
  const qtyLabelEl = document.querySelector("[data-qty-label]");
  const skuEl = document.querySelector("[data-sku]");
  const approxWeightEl = document.querySelector("[data-unit-weight-hint]");
  const variantInputs = document.querySelectorAll("[data-variant]");
  const addForm = document.querySelector("[data-cart-add-form]");
  const buyNowForm = document.querySelector("[data-buy-now-form]");
  const buyNowBtn = document.querySelector("[data-buy-now]");
  const buyNowHint = document.querySelector("[data-buy-now-hint]");
  const actionsEl = document.querySelector(".pdp-actions");
  const qtyRow = document.querySelector(".qty-row");

  const minOrder = Number(actionsEl?.dataset.minOrder || "0");
  const cartSubtotal = Number(actionsEl?.dataset.cartSubtotal || "0");

  /* Формат ваги за правилом клієнта: до 1 кг — грами, від 1 кг — кг. */
  const formatWeight = (kg) => {
    const value = Math.round(kg * 1000) / 1000;
    if (value < 1) return `${Math.round(value * 1000)} г`;
    const text = value.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
    return `${text} кг`;
  };

  const formatPieces = (qty, unitLabel) => `${qty} ${unitLabel}`;

  // Дефолтні значення завжди беремо з data-атрибутів (|unlocalize на сервері) —
  // текст у DOM може бути локалізований коми ("0,50"), що ламає Number().
  let variant = {
    unit: qtyRow?.dataset.defaultUnit || "pcs",
    unitLabel: qtyRow?.dataset.defaultUnitLabel || "",
    step: Number(qtyRow?.dataset.defaultStep || "1"),
    min: Number(qtyRow?.dataset.defaultMin || "1"),
    price: Number(qtyRow?.dataset.defaultPrice || "0"),
    approxWeight: qtyRow?.dataset.defaultApproxWeight || "",
  };

  const readVariantFromInput = (input) => ({
    unit: input.dataset.unit || "pcs",
    unitLabel: input.dataset.unitLabel || "",
    step: Number(input.dataset.step || "1"),
    min: Number(input.dataset.minQuantity || "1"),
    price: Number(input.dataset.price || "0"),
    approxWeight: input.dataset.approxWeight || "",
  });

  let qty = variant.min || variant.step;

  const round = (value, step) => {
    const decimals = step < 1 ? 1 : 0;
    return Number(value.toFixed(decimals));
  };

  if (buyNowBtn && buyNowBtn.disabled) {
    buyNowBtn.dataset.unavailable = "1";
  }

  const syncBuyNowState = () => {
    if (!buyNowBtn) return;
    const unavailable = buyNowBtn.dataset.unavailable === "1";
    const projected = cartSubtotal + qty * variant.price;
    const blocked = minOrder > 0 && projected < minOrder;
    buyNowBtn.disabled = unavailable || blocked;
    buyNowBtn.setAttribute("aria-disabled", unavailable || blocked ? "true" : "false");
    if (buyNowHint) buyNowHint.hidden = unavailable || !blocked;
  };

  const renderQty = () => {
    const displayValue = variant.unit === "kg" ? formatWeight(qty) : formatPieces(qty, variant.unitLabel);
    if (qtyOut) qtyOut.textContent = displayValue;
    if (qtyInput) qtyInput.value = String(qty);
    if (qtyInputBuyNow) qtyInputBuyNow.value = String(qty);
    if (lineTotalEl) lineTotalEl.textContent = `${(qty * variant.price).toFixed(2)} ₴`;
    if (qtyHint) {
      const minText = variant.unit === "kg" ? formatWeight(variant.min) : formatPieces(variant.min, variant.unitLabel);
      const stepText = variant.unit === "kg" ? formatWeight(variant.step) : formatPieces(variant.step, variant.unitLabel);
      const minLabel = qtyHint.dataset.minOrderText || "Мін. замовлення";
      const stepLabel = qtyHint.dataset.stepText || "крок";
      qtyHint.textContent = `${minLabel}: ${minText} · ${stepLabel} ${stepText}`;
    }
    syncBuyNowState();
  };

  qtyMinus?.addEventListener("click", () => {
    qty = Math.max(variant.min, round(qty - variant.step, variant.step));
    renderQty();
  });

  qtyPlus?.addEventListener("click", () => {
    qty = round(qty + variant.step, variant.step);
    renderQty();
  });

  const applyVariant = (input) => {
    if (!input) return;
    variant = readVariantFromInput(input);
    qty = variant.min || variant.step;

    if (priceEl) priceEl.textContent = variant.price.toFixed(2);
    if (unitSuffixEl) unitSuffixEl.textContent = `/${variant.unitLabel}`;
    if (unitSpecEl) unitSpecEl.textContent = variant.unitLabel;
    if (qtyLabelEl) {
      qtyLabelEl.textContent = variant.unit === "kg"
        ? (qtyLabelEl.dataset.labelWeight || qtyLabelEl.textContent)
        : (qtyLabelEl.dataset.labelPiece || qtyLabelEl.textContent);
    }
    if (skuEl && input.dataset.sku) skuEl.textContent = input.dataset.sku;
    if (approxWeightEl) {
      approxWeightEl.textContent = variant.approxWeight;
      approxWeightEl.hidden = !variant.approxWeight;
    }
    if (addForm && input.dataset.addUrl) {
      addForm.setAttribute("hx-post", input.dataset.addUrl);
      if (window.htmx) window.htmx.process(addForm);
    }
    if (buyNowForm && input.dataset.addUrl) {
      buyNowForm.setAttribute("hx-post", input.dataset.addUrl);
      if (window.htmx) window.htmx.process(buyNowForm);
    }
    renderQty();
  };

  variantInputs.forEach((input) => {
    input.addEventListener("change", () => applyVariant(input));
    if (input.checked) applyVariant(input);
  });

  if (!variantInputs.length) renderQty();

  const mainPhoto = document.querySelector("[data-main-photo]");
  const thumbs = document.querySelectorAll("[data-thumb]");
  thumbs.forEach((btn) => {
    btn.addEventListener("click", () => {
      const src = btn.getAttribute("data-thumb");
      if (mainPhoto && src) {
        mainPhoto.src = src;
      }
      thumbs.forEach((t) => t.classList.toggle("is-active", t === btn));
    });
  });
})();
