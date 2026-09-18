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

  const setBurgerOpen = (open) => {
    if (!burger) return;
    burger.setAttribute("aria-expanded", open ? "true" : "false");
    const label = burger.getAttribute(open ? "data-label-close" : "data-label-open");
    if (label) burger.setAttribute("aria-label", label);
  };

  let scrollLockY = 0;

  const syncScrollLock = () => {
    const locked = Boolean(
      mobileNav?.classList.contains("is-open") || cartDrawer?.classList.contains("is-open")
    );
    if (locked && !document.body.classList.contains("is-scroll-lock")) {
      scrollLockY = window.scrollY;
      document.body.classList.add("is-scroll-lock");
      document.body.style.top = `-${scrollLockY}px`;
    }
    if (!locked && document.body.classList.contains("is-scroll-lock")) {
      document.body.classList.remove("is-scroll-lock");
      document.body.style.top = "";
      window.scrollTo(0, scrollLockY);
    }
  };

  const hideMobileNav = () => {
    mobileNav?.classList.remove("is-open");
    setBurgerOpen(false);
  };

  const closeMobileNav = () => {
    hideMobileNav();
    syncScrollLock();
  };

  burger?.addEventListener("click", () => {
    const open = mobileNav?.classList.toggle("is-open");
    setBurgerOpen(Boolean(open));
    if (open) {
      document.querySelectorAll(".search-suggest.is-open").forEach((el) => {
        el.classList.remove("is-open");
        el.hidden = true;
      });
    }
    syncScrollLock();
  });

  const setCart = (open) => {
    if (!cartDrawer) return;
    cartDrawer.classList.toggle("is-open", open);
    cartDrawer.setAttribute("aria-hidden", open ? "false" : "true");
    syncScrollLock();
  };

  const cartSummaryUrl = document.body.dataset.cartSummaryUrl;

  cartOpeners.forEach((el) =>
    el.addEventListener("click", () => {
      hideMobileNav();
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
      closeMobileNav();
      dropdown?.classList.remove("is-open");
      document.querySelectorAll(".search-suggest.is-open").forEach((el) => {
        el.classList.remove("is-open");
        el.hidden = true;
      });
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
    document.querySelectorAll("[data-search-suggest]").forEach((form) => {
      if (!form.contains(e.target)) {
        const panel = form.querySelector(".search-suggest");
        if (panel) {
          panel.classList.remove("is-open");
          panel.hidden = true;
        }
      }
    });
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
    if (e.target.classList?.contains("search-suggest")) {
      const hasContent = e.target.childElementCount > 0;
      e.target.classList.toggle("is-open", hasContent);
      e.target.hidden = !hasContent;
    }
  });
  /* CSRF для hx-post поза формами (видалення в drawer тощо). */
  const csrfCookie = (name) => {
    const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
    return match ? decodeURIComponent(match[1]) : "";
  };
  window.addEventListener("resize", () => {
    if (window.matchMedia("(min-width: 1024px)").matches && mobileNav?.classList.contains("is-open")) {
      closeMobileNav();
    }
  });

  document.body.addEventListener("htmx:configRequest", (e) => {
    if (e.detail.headers["X-CSRFToken"]) return;
    const token = csrfCookie("csrftoken");
    if (token) e.detail.headers["X-CSRFToken"] = token;
  });
})();
