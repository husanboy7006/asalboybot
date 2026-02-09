const tg = window.Telegram?.WebApp;
if (tg) {
    tg.expand();
    tg.MainButton.textColor = "#000000";
    tg.MainButton.color = "#FFD700";
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
    } else {
        renderCart();
        modal.classList.add("open");
    }
};

window.renderCart = function () {
    const container = document.getElementById("cartItems");
    if (!container) return;
    container.innerHTML = "";

    if (cart.size === 0) {
        container.innerHTML = "<div style='text-align:center; padding:20px; color:#888'>Savatcha bo'sh 🛒</div>";
        document.getElementById("cartTotal").textContent = "0 so'm";
        return;
    }

    let totalSum = 0;
    cart.forEach((qty, id) => {
        const p = PRODUCTS.find(x => x.id === id);
        if (!p) return;

        const price = p.price_1 || 0;
        const itemTotal = price * qty;
        totalSum += itemTotal;

        const div = document.createElement("div");
        div.className = "cart-item";
        div.innerHTML = `
      <div class="cart-item-info">
        <span class="cart-item-title">${p.name_uz}</span>
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

    document.getElementById("cartTotal").textContent = totalSum.toLocaleString("uz-UZ") + " so'm";
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
    btn.textContent = "⏳";

    if (!navigator.geolocation) {
        alert("Brauzeringiz lokatsiyani qo'llab-quvvatlamaydi.");
        btn.textContent = "📍";
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            userLat = pos.coords.latitude;
            userLon = pos.coords.longitude;
            btn.textContent = "✅";
            btn.style.background = "#4CAF50"; // Green

            // Auto-fill address if empty
            const addr = document.getElementById("address");
            if (!addr.value) addr.value = `Lokatsiya: ${userLat.toFixed(5)}, ${userLon.toFixed(5)}`;
        },
        (err) => {
            console.error(err);
            alert("Lokatsiyani aniqlab bo'lmadi. Iltimos, manzilni yozma kiriting.");
            btn.textContent = "❌";
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
};

// --- CHECKOUT ---
window.submitOrder = () => {
    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const address = document.getElementById("address").value.trim();

    const items = [];
    cart.forEach((qty, id) => items.push({ id, qty }));

    if (items.length === 0) {
        tg?.showAlert("Savatcha bo'sh!");
        return;
    }
    if (!name || !phone) { // Address is optional if loc provided? Let's keep it required but auto-filled.
        tg?.showAlert("Iltimos, barcha ma'lumotlarni to'ldiring (Ism, Telefon, Manzil).");
        return;
    }

    const payload = {
        items, name, phone, address,
        lat: userLat,
        lon: userLon
    };

    if (tg) tg.sendData(JSON.stringify(payload));
    else {
        console.log("Order payload:", payload);
        alert("Order sent! (Desktop mode)");
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

    return `
  <div class="card" onclick="showInfo('${p.id}')">
    <img src="${localImg}" 
         class="card-img" 
         alt="${p.name_uz}" 
         loading="lazy"
         onerror="this.onerror=null; this.src='${placeholder}';">
    <div class="card-body">
      <div class="title">${p.name_uz || "Nomsiz"}</div>
      <div class="desc">${p.info_short || p.name_ru || ""}</div>
      <div class="price-row">
        <div class="price">${(p.price_1 || 0).toLocaleString("uz-UZ")} so'm</div>
        <button class="plus" onclick="event.stopPropagation(); inc('${p.id}', this)">+</button>
      </div>
    </div>
  </div>`;
}

function showInfo(id) {
    const p = PRODUCTS.find(x => x.id === id);
    if (!p) return;
    tg?.showPopup({
        title: p.name_uz,
        message: p.info_full || p.info_short || "Ma'lumot yo'q",
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
        render();
    } catch (e) {
        grid.innerHTML = `<div style="color:red; text-align:center">Xatolik: ${e.message}</div>`;
    }
}

bootstrap();
