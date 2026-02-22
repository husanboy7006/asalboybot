const tg = window.Telegram?.WebApp;
let LANG = "ru";

// Helper to get URL query params
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 1. Try URL param
const urlLang = getQueryParam("lang");
if (urlLang === "ru" || urlLang === "uz") {
    LANG = urlLang;
}
// 2. Fallback to Telegram info
else if (tg?.initDataUnsafe?.user?.language_code === "ru") {
    LANG = "ru";
}

if (tg) {
    tg.expand();
    tg.MainButton.textColor = "#000000";
    tg.MainButton.color = "#FFD700";

    // Bind MainButton to the custom submitOrder function
    tg.MainButton.onClick(window.submitOrder);

    // Update static texts based on LANG
    if (LANG === "ru") {
        const tabs = document.querySelectorAll(".tab");
        if (tabs[0]) tabs[0].textContent = "🧺 Все";
        if (tabs[1]) tabs[1].textContent = "🏔 Горный";
        if (tabs[2]) tabs[2].textContent = "🌿 Акация";
        if (tabs[3]) tabs[3].textContent = "🍯 Другое";

        const btnCheckout = document.getElementById("btnCheckout");
        if (btnCheckout) btnCheckout.textContent = "Оформить заказ";

        const nameEl = document.getElementById("name");
        if (nameEl) nameEl.placeholder = "Ваше имя";

        const phoneEl = document.getElementById("phone");
        if (phoneEl) phoneEl.placeholder = "Телефон";

        const addressEl = document.getElementById("address");
        if (addressEl) addressEl.placeholder = "Адрес доставки";

        const locBtn = document.getElementById("locBtn");
        if (locBtn) locBtn.textContent = "📍";

        // Update cart modal texts
        const modalHeader = document.querySelector(".modal-header h2");
        if (modalHeader) modalHeader.innerHTML = 'Корзина <span id="modalCartCount">(0)</span>';

        const summaryLabel = document.querySelector(".cart-summary .row span:first-child");
        if (summaryLabel) summaryLabel.textContent = "Итого:";

        const formTitle = document.querySelector(".order-form h3");
        if (formTitle) formTitle.textContent = "Ваши данные";

        const confirmBtn = document.getElementById("confirmOrder");
        if (confirmBtn) confirmBtn.textContent = "✅ Подтвердить заказ";

        const footerBtn = document.querySelector("#mainFooter button");
        if (footerBtn) {
            const countSpan = document.getElementById("footerCount");
            const count = countSpan ? countSpan.textContent : "0";
            footerBtn.innerHTML = `Открыть корзину (<span id="footerCount">${count}</span>)`;
        }
    }
}

let PRODUCTS = [];
const cart = new Map(); // id -> qty
const grid = document.getElementById("grid");
const tabs = document.querySelectorAll(".tab");
const cartCount = document.getElementById("cartCount");

// Better Honey Placeholders
const PLACEHOLDERS = [
    "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=400&q=80", // Honey jar
    "https://images.unsplash.com/photo-1555421689-491a97ff2040?auto=format&fit=crop&w=400&q=80", // Honeycomb
    "https://images.unsplash.com/photo-1587049548423-4213d2f0ffae?auto=format&fit=crop&w=400&q=80"  // Spoon
];

tabs.forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelector(".tab.active")?.classList.remove("active");
        btn.classList.add("active");
        render(btn.dataset.cat);
    });
});

function inc(id, btnElement) {
    cart.set(id, (cart.get(id) || 0) + 1);
    updateCartCount();

    // Animation
    if (btnElement) {
        const rect = btnElement.getBoundingClientRect();
        const cartRect = document.getElementById("cartBtn").getBoundingClientRect();

        // Create flying particle
        const img = document.createElement("div");
        img.style.width = "20px";
        img.style.height = "20px";
        img.style.background = "#FFD700";
        img.style.borderRadius = "50%";
        img.style.position = "fixed";
        img.style.left = rect.left + "px";
        img.style.top = rect.top + "px";
        img.style.zIndex = 1000;
        img.style.transition = "all 0.6s cubic-bezier(0.19, 1, 0.22, 1)";
        document.body.appendChild(img);

        // Fly to cart
        setTimeout(() => {
            img.style.left = (cartRect.left + 10) + "px";
            img.style.top = (cartRect.top + 10) + "px";
            img.style.transform = "scale(0.1)";
            img.style.opacity = "0";
        }, 10);

        setTimeout(() => img.remove(), 600);
    }
}

// --- CART LOGIC ---
window.toggleCart = function () {
    console.log("toggleCart called");
    const modal = document.getElementById("cartModal");
    if (!modal) {
        console.error("Modal not found!");
        return;
    }
    if (modal.classList.contains("open")) {
        modal.classList.remove("open");
        if (tg) tg.MainButton.hide(); // Hide main button when closing cart
    } else {
        renderCart();
        modal.classList.add("open");
        if (cart.size > 0 && tg) {
            const btnText = LANG === "ru" ? "Оформить заказ" : "Buyurtma berish";
            tg.MainButton.text = btnText;
            tg.MainButton.show(); // Show main button when cart is open and not empty
        }
    }
};

window.renderCart = function () {
    const container = document.getElementById("cartItems");
    if (!container) return;
    container.innerHTML = "";

    const emptyText = LANG === "ru" ? "Корзина пуста 🛒" : "Savatcha bo'sh 🛒";
    const sumText = LANG === "ru" ? "сум" : "so'm";

    if (cart.size === 0) {
        container.innerHTML = `<div style='text-align:center; padding:20px; color:#888'>${emptyText}</div>`;
        document.getElementById("cartTotal").textContent = `0 ${sumText}`;
        return;
    }

    let totalSum = 0;
    cart.forEach((qty, id) => {
        const p = PRODUCTS.find(x => x.id === id);
        if (!p) return;

        const price = p.price_1 || 0;
        const itemTotal = price * qty;
        totalSum += itemTotal;

        const pName = (LANG === "ru" && p.name_ru) ? p.name_ru : p.name_uz;

        const div = document.createElement("div");
        div.className = "cart-item";
        div.innerHTML = `
      <div class="cart-item-info">
        <span class="cart-item-title">${pName}</span>
        <span class="cart-item-price">${price.toLocaleString("uz-UZ")} x ${qty}</span>
      </div>
      <div class="cart-controls">
        <button class="cart-btn-mini" onclick="updateItem('${id}', -1)">-</button>
        <span style="color:white; font-weight:600; min-width:20px; text-align:center">${qty}</span>
        <button class="cart-btn-mini" onclick="updateItem('${id}', 1)">+</button>
      </div>
      <div class="cart-item-total" style="margin-left:10px">
        ${itemTotal.toLocaleString("uz-UZ")}
      </div>
    `;
        container.appendChild(div);
    });

    document.getElementById("cartTotal").textContent = totalSum.toLocaleString("uz-UZ") + ` ${sumText}`;
    document.getElementById("modalCartCount").textContent = `(${cart.size})`;
}

function updateItem(id, change) {
    const current = cart.get(id) || 0;
    const newQty = current + change;

    if (newQty <= 0) {
        cart.delete(id);
    } else {
        cart.set(id, newQty);
    }
    updateCartCount(); // Update global counter
    renderCart(); // Re-render modal
}

function updateCartCount() {
    let total = 0;
    cart.forEach(v => total += v);
    cartCount.textContent = total;
    document.getElementById("footerCount").textContent = total;

    const footerBtn = document.getElementById("mainFooter");
    if (total > 0) {
        footerBtn.style.display = "block";
        if (tg) tg.MainButton.hide(); // We use our own button
    } else {
        footerBtn.style.display = "none";
    }
}

// Ensure cart count is 0 on load
updateCartCount();

let userLat = null;
let userLon = null;

window.getLocation = function () {
    const btn = document.getElementById("locBtn");

    // Store original SVG
    const originalSVG = btn.innerHTML;

    // Loading state
    btn.classList.remove('success', 'error');
    btn.classList.add('loading');
    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 6v6l4 2"/>
    </svg>`;

    const notSupported = LANG === "ru" ? "Ваш браузер не поддерживает геолокацию." : "Brauzeringiz lokatsiyani qo'llab-quvvatlamaydi.";
    const locError = LANG === "ru" ? "Не удалось определить локацию. Введите адрес вручную." : "Lokatsiyani aniqlab bo'lmadi. Iltimos, manzilni yozma kiriting.";
    const locPrefix = LANG === "ru" ? "Локация" : "Lokatsiya";

    if (!navigator.geolocation) {
        alert(notSupported);
        btn.classList.remove('loading');
        btn.innerHTML = originalSVG;
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            userLat = pos.coords.latitude;
            userLon = pos.coords.longitude;

            // Success state
            btn.classList.remove('loading');
            btn.classList.add('success');
            btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M20 6L9 17l-5-5"/>
            </svg>`;

            // Auto-fill address if empty
            const addr = document.getElementById("address");
            if (!addr.value) addr.value = `${locPrefix}: ${userLat.toFixed(5)}, ${userLon.toFixed(5)}`;
        },
        (err) => {
            console.error(err);
            alert(locError);

            // Error state
            btn.classList.remove('loading');
            btn.classList.add('error');
            btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M18 6L6 18M6 6l12 12"/>
            </svg>`;

            // Reset after 3 seconds
            setTimeout(() => {
                btn.classList.remove('error');
                btn.innerHTML = originalSVG;
            }, 3000);
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
};

// --- CHECKOUT ---
window.submitOrder = async () => {
    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const address = document.getElementById("address").value.trim();

    const emptyText = LANG === "ru" ? "Корзина пуста!" : "Savatcha bo'sh!";
    const fillText = LANG === "ru" ? "Пожалуйста, заполните все поля (Имя, Телефон, Адрес)." : "Iltimos, barcha ma'lumotlarni (Ism, Telefon, Manzil) to'ldiring.";
    const errText = LANG === "ru" ? "Ошибка при отправке заказа." : "Buyurtma yuborishda xatolik yuz berdi.";

    const items = [];
    cart.forEach((qty, id) => items.push({ id, qty }));

    if (items.length === 0) {
        tg?.showAlert(emptyText);
        return;
    }
    if (!name || !phone) {
        tg?.showAlert(fillText);
        return;
    }

    if (tg?.HapticFeedback) {
        tg.HapticFeedback.impactOccurred('medium');
    }

    const payload = {
        initData: tg?.initData || "",
        items, name, phone, address,
        lat: userLat,
        lon: userLon
    };

    // Make the confirm button loading state
    const confirmBtn = document.getElementById("confirmOrder");
    const originalText = confirmBtn.textContent;
    confirmBtn.textContent = "⏳...";
    confirmBtn.disabled = true;

    try {
        const response = await fetch('/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.success) {
            if (tg?.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('success');
            }
            if (tg) {
                tg.close(); // Close the WebApp on success
            } else {
                alert("Order Sent! ID: " + result.order_id);
            }
        } else {
            if (tg?.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('error');
            }
            tg?.showAlert(errText + " (" + (result.error || "Unknown") + ")");
            confirmBtn.textContent = originalText;
            confirmBtn.disabled = false;
        }
    } catch (error) {
        console.error("Order submit error:", error);
        if (tg?.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred('error');
        }
        tg?.showAlert(errText);
        confirmBtn.textContent = originalText;
        confirmBtn.disabled = false;
    }
};

function cardHTML(p, idx) {
    // LOGIC: 
    // 1. Try local image: /webapp/img/{id}.jpg (Absolute path to match static route)
    // 2. If valid photo_url exists -> use it
    // 3. Fallback to generic Honey placeholder

    // Note: handling "try local, failback to other" in HTML is done via onerror
    const localImg = `/webapp/img/${p.id}.jpg?t=${new Date().getTime()}`; // Add timestamp to avoid caching uploaded images
    const placeholder = PLACEHOLDERS[idx % PLACEHOLDERS.length];

    // Translation Logic
    const pName = (LANG === "ru" && p.name_ru) ? p.name_ru : p.name_uz;
    // Use info_short_ru for Russian, fallback to info_short (Uzbek)
    const pDesc = (LANG === "ru" && p.info_short_ru) ? p.info_short_ru : (p.info_short || p.desc_uz || "");
    const sumText = LANG === "ru" ? "сум" : "so'm";

    return `
  <div class="card" onclick="showInfo('${p.id}')">
    <img src="${localImg}" 
         class="card-img" 
         alt="${pName}" 
         loading="lazy"
         onerror="this.onerror=null; this.src='${placeholder}';">
    <div class="card-body">
      <div class="title">${pName || "Nomsiz"}</div>
      <div class="desc">${pDesc}</div>
      <div class="price-row">
        <div class="price">${(p.price_1 || 0).toLocaleString("uz-UZ")} ${sumText}</div>
        <button class="plus" onclick="event.stopPropagation(); inc('${p.id}', this)">+</button>
      </div>
    </div>
  </div>`;
}

function showInfo(id) {
    const p = PRODUCTS.find(x => x.id === id);
    if (!p) return;

    const pName = (LANG === "ru" && p.name_ru) ? p.name_ru : p.name_uz;
    const pInfo = (LANG === "ru" && p.info_full) ? p.info_full : (p.info_full || p.info_short || "Ma'lumot yo'q");

    tg?.showPopup({
        title: pName,
        message: pInfo,
        buttons: [{ type: "ok" }]
    });
}

function render(cat = "all") {
    grid.innerHTML = "";
    let data = PRODUCTS;

    if (cat !== "all") {
        const q = cat.toLowerCase();
        data = PRODUCTS.filter(p => {
            const name = (p.name_uz || "").toLowerCase();
            // Simple robust filtering. 
            // Better: add 'category' field to json. But for now regex matches:
            if (cat === "tog") return name.includes("tog") || name.includes("tog'") || name.includes("tog‘");
            if (cat === "akatsiya") return name.includes("akatsiya");
            return !name.includes("tog") && !name.includes("akatsiya");
        });
    }

    grid.innerHTML = data.map((p, i) => cardHTML(p, i)).join("");
}

async function bootstrap() {
    try {
        const r = await fetch("/api/products");
        const j = await r.json();
        PRODUCTS = j.items || [];

        // Initial render logic based on LANG
        const activeTab = document.querySelector(".tab.active");
        const cat = activeTab ? activeTab.dataset.cat : "all";
        render(cat);

    } catch (e) {
        grid.innerHTML = `<div style="color:red; text-align:center">Xatolik: ${e.message}</div>`;
    }
}

bootstrap();
