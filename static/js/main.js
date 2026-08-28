(() => {
  const header = document.querySelector("[data-header]");
  const burger = document.querySelector("[data-burger]");
  const mobileNav = document.querySelector("[data-mobile-nav]");
  const cartOpeners = document.querySelectorAll("[data-cart-open]");
  const cartDrawer = document.querySelector("[data-cart]");
  const cartClosers = document.querySelectorAll("[data-cart-close]");
  const dropdown = document.querySelector("[data-dropdown]");
  const dropdownToggle = document.querySelector("[data-dropdown-toggle]");

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

  const cartSummaryUrl = document.body.dataset.cartSummaryUrl;

  cartOpeners.forEach((el) =>
    el.addEventListener("click", () => {
      setCart(true);
      if (cartSummaryUrl) {
        htmx.ajax("GET", cartSummaryUrl, { target: "#cart-drawer-content" });
      }
    })
  );
  cartClosers.forEach((el) => el.addEventListener("click", () => setCart(false)));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      setCart(false);
      dropdown?.classList.remove("is-open");
    }
  });

  dropdownToggle?.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown?.classList.toggle("is-open");
  });

  document.addEventListener("click", (e) => {
    if (dropdown && !dropdown.contains(e.target)) {
      dropdown.classList.remove("is-open");
    }
  });

  /* Відкривати drawer після оновлення контенту (add-to-cart).
     GET на load прибрано з cart_drawer.html — інакше панель відкривалась на кожному F5/переході. */
  document.body.addEventListener("htmx:afterSwap", (e) => {
    if (e.target.id === "cart-drawer-content") {
      const verb = (e.detail?.requestConfig?.verb || "").toLowerCase();
      if (verb !== "get") {
        setCart(true);
      }
    }
  });

  /* CSRF для hx-post поза формами (видалення в drawer тощо). */
  const csrfCookie = (name) => {
    const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
    return match ? decodeURIComponent(match[1]) : "";
  };
  document.body.addEventListener("htmx:configRequest", (e) => {
    if (e.detail.headers["X-CSRFToken"]) return;
    const token = csrfCookie("csrftoken");
    if (token) e.detail.headers["X-CSRFToken"] = token;
  });
})();
