(() => {
  const header = document.querySelector("[data-header]");
  const burger = document.querySelector("[data-burger]");
  const mobileNav = document.querySelector("[data-mobile-nav]");
  const cartOpeners = document.querySelectorAll("[data-cart-open]");
  const cartDrawer = document.querySelector("[data-cart]");
  const cartClosers = document.querySelectorAll("[data-cart-close]");
  const qtyOut = document.querySelector("[data-qty]");
  const qtyMinus = document.querySelector("[data-qty-minus]");
  const qtyPlus = document.querySelector("[data-qty-plus]");
  const priceEl = document.querySelector("[data-price]");
  const skuEl = document.querySelector("[data-sku]");
  const variantInputs = document.querySelectorAll("[data-variant]");

  const onScroll = () => {
    if (!header) return;
    header.classList.toggle("is-stuck", window.scrollY > 8);
  };

  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  burger?.addEventListener("click", () => {
    const open = mobileNav?.classList.toggle("is-open");
    burger.setAttribute("aria-expanded", open ? "true" : "false");
  });

  const setCart = (open) => {
    if (!cartDrawer) return;
    cartDrawer.classList.toggle("is-open", open);
    cartDrawer.setAttribute("aria-hidden", open ? "false" : "true");
    document.body.style.overflow = open ? "hidden" : "";
  };

  cartOpeners.forEach((el) => el.addEventListener("click", () => setCart(true)));
  cartClosers.forEach((el) => el.addEventListener("click", () => setCart(false)));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setCart(false);
  });

  let qty = 1;
  const renderQty = () => {
    if (qtyOut) qtyOut.textContent = String(qty);
  };

  qtyMinus?.addEventListener("click", () => {
    qty = Math.max(1, qty - 1);
    renderQty();
  });

  qtyPlus?.addEventListener("click", () => {
    qty += 1;
    renderQty();
  });

  const applyVariant = (input) => {
    if (!input) return;
    if (priceEl && input.dataset.price) {
      priceEl.textContent = input.dataset.price;
    }
    if (skuEl && input.dataset.sku) {
      skuEl.textContent = input.dataset.sku;
    }
  };

  variantInputs.forEach((input) => {
    input.addEventListener("change", () => applyVariant(input));
    if (input.checked) applyVariant(input);
  });

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
