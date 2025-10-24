document.addEventListener('DOMContentLoaded', () => {
    const menuContainer = document.getElementById('menu-container');
    const categoryTabsContainer = document.getElementById('category-tabs');
    const cartItemsContainer = document.getElementById('cart-items');
    const cartTotalSpan = document.getElementById('cart-total');
    const cartCountSpan = document.getElementById('cart-count');
    const checkoutButton = document.getElementById('checkout-button');
    const modal = document.getElementById('checkout-modal');
    const closeModalButton = document.getElementById('close-modal-button');
    const checkoutForm = document.getElementById('checkout-form');
    const modalTotalSpan = document.getElementById('modal-total');
    const placeOrderButton = document.getElementById('place-order-button');
    const customerNameInput = document.getElementById('customer-name');
    const customerPhoneInput = document.getElementById('customer-phone');
    const customerAddressInput = document.getElementById('customer-address');

    const menuApiUrl = '/api/menu';
    const orderApiUrl = '/api/order_takeaway';
    const placeholderImage = 'placeholder.png';

    let allMenuItems = [];
    let groupedMenu = {};
    let cart = JSON.parse(localStorage.getItem('cafeCart')) || {};

    async function initApp() {
        try {
            const response = await fetch(menuApiUrl);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Không thể tải ${menuApiUrl}. Status: ${response.status}. Bạn đã chạy 'python web_api.py' chưa?`);
            }
            allMenuItems = await response.json();

            groupedMenu = groupItemsByCategory(allMenuItems);
            createCategoryTabs(Object.keys(groupedMenu));

            if (Object.keys(groupedMenu).length > 0) {
                const firstCategory = Object.keys(groupedMenu)[0];
                displayCategoryItems(firstCategory);
                setActiveTab(firstCategory);
            } else {
                menuContainer.innerHTML = '<p>Thực đơn hiện đang trống.</p>';
            }
        } catch (error) {
            console.error('Lỗi khi tải hoặc xử lý menu:', error);
            if (menuContainer) menuContainer.innerHTML = `<p class="error-message">Không thể tải thực đơn. Chi tiết: ${error.message}</p>`;
        }
        updateCartDisplay();

        checkoutButton.addEventListener('click', openCheckoutModal);
        closeModalButton.addEventListener('click', closeCheckoutModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeCheckoutModal();
        });
        checkoutForm.addEventListener('submit', placeOrder);
    }

    function groupItemsByCategory(items) {
        if (!Array.isArray(items)) return {};
        return items.reduce((acc, item) => {
            if (typeof item !== 'object' || item === null) return acc;
            const category = item.category || 'Khác';
            if (!acc[category]) acc[category] = [];
            acc[category].push(item);
            return acc;
        }, {});
    }

    function createCategoryTabs(categories) {
        categoryTabsContainer.innerHTML = '';
        categories.forEach(category => {
            const tabButton = document.createElement('button');
            tabButton.classList.add('tab-button');
            tabButton.textContent = category;
            tabButton.dataset.category = category;
            tabButton.addEventListener('click', () => { displayCategoryItems(category); setActiveTab(category); });
            categoryTabsContainer.appendChild(tabButton);
        });
    }

    function setActiveTab(activeCategory) {
        const tabButtons = categoryTabsContainer.querySelectorAll('.tab-button');
        tabButtons.forEach(button => { button.classList.toggle('active', button.dataset.category === activeCategory); });
    }

    function displayCategoryItems(category) {
        menuContainer.innerHTML = '';
        const items = groupedMenu[category];
        if (!items || items.length === 0) {
            menuContainer.innerHTML = '<p>Không có món nào trong danh mục này.</p>'; return;
        }
        const gridContainer = document.createElement('div');
        gridContainer.classList.add('menu-grid');
        menuContainer.appendChild(gridContainer);

        items.forEach(item => {
            if (typeof item !== 'object' || item === null || !item.id) return;
            const menuItemDiv = createMenuItemCard(item);
            const addButton = menuItemDiv.querySelector('.btn-add-cart');
            if (addButton) {
                addButton.addEventListener('click', (e) => {
                    e.stopPropagation();
                    addToCart(item);
                    addButton.textContent = 'Đã thêm!';
                    addButton.disabled = true;
                    setTimeout(() => {
                        addButton.textContent = 'Thêm';
                        addButton.disabled = false;
                    }, 1000);
                });
            }
            gridContainer.appendChild(menuItemDiv);
        });
    }

    function createMenuItemCard(item) {
        const menuItemDiv = document.createElement('div');
        menuItemDiv.classList.add('menu-item');
        let imagePath = placeholderImage;
        if (item.image && typeof item.image === 'string') {
            imagePath = `/App/${item.image.replace(/\\/g, '/')}`;
        }
        const name = item.name || 'Chưa đặt tên';
        const price = item.price || 0;
        const itemId = item.id || '';

        menuItemDiv.innerHTML = `
            <div class="menu-item-image-wrapper">
                <img src="${imagePath}" alt="${name}" class="menu-item-image" onerror="this.onerror=null; this.src='${placeholderImage}';">
            </div>
            <div class="menu-item-details">
                <h3>${name}</h3>
                <p class="price">${formatPrice(price)} VND</p>
                <button class="btn btn-add-cart" data-id="${itemId}" ${!itemId ? 'disabled' : ''}>Thêm</button>
            </div>
        `;
        return menuItemDiv;
    }

    function saveCart() {
        localStorage.setItem('cafeCart', JSON.stringify(cart));
    }

    function addToCart(item) {
        const itemName = item.name;
        if (!itemName || !item.id) return;
        if (cart[itemName]) {
            cart[itemName].quantity += 1;
        } else {
            cart[itemName] = {
                id: item.id,
                price: item.price || 0,
                quantity: 1
            };
        }
        saveCart();
        updateCartDisplay();
    }

    function updateCartDisplay() {
        cartItemsContainer.innerHTML = '';
        let total = 0;
        let itemCount = 0;
        const cartItemNames = Object.keys(cart);

        if (cartItemNames.length === 0) {
            cartItemsContainer.innerHTML = '<p class="empty-cart-message">Giỏ hàng đang trống.</p>';
            checkoutButton.disabled = true;
            cartCountSpan.textContent = '0';
            cartCountSpan.style.display = 'none';
        } else {
            cartItemNames.forEach(itemName => {
                const item = cart[itemName];
                const itemTotal = item.price * item.quantity;
                total += itemTotal;
                itemCount += item.quantity;

                const cartItemDiv = document.createElement('div');
                cartItemDiv.classList.add('cart-item');
                cartItemDiv.innerHTML = `
                    <span class="cart-item-name">${itemName}</span>
                    <div class="cart-item-controls">
                         <button class="btn-qty-change" data-name="${itemName}" data-change="-1">-</button>
                         <span class="cart-item-qty">${item.quantity}</span>
                         <button class="btn-qty-change" data-name="${itemName}" data-change="1">+</button>
                    </div>
                    <span class="cart-item-price">${formatPrice(itemTotal)} VND</span>
                    <button class="btn-remove-item" data-name="${itemName}">&times;</button>
                `;
                cartItemDiv.querySelector('.btn-remove-item').addEventListener('click', () => removeFromCart(itemName));
                cartItemDiv.querySelectorAll('.btn-qty-change').forEach(btn => {
                    btn.addEventListener('click', (e) => changeQuantity(e.target.dataset.name, parseInt(e.target.dataset.change, 10)));
                });
                cartItemsContainer.appendChild(cartItemDiv);
            });
            checkoutButton.disabled = false;
            cartCountSpan.textContent = itemCount;
            cartCountSpan.style.display = 'block';
        }

        const totalFormatted = `${formatPrice(total)} VND`;
        cartTotalSpan.textContent = totalFormatted;
        modalTotalSpan.textContent = totalFormatted;
    }

    function removeFromCart(itemName) {
        if (cart[itemName]) { delete cart[itemName]; saveCart(); updateCartDisplay(); }
    }

    function changeQuantity(itemName, change) {
        if (cart[itemName]) {
            cart[itemName].quantity += change;
            if (cart[itemName].quantity <= 0) { delete cart[itemName]; }
            saveCart();
            updateCartDisplay();
        }
    }

    function openCheckoutModal() {
        if (Object.keys(cart).length === 0) return;
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('visible'), 10);
        customerNameInput.value = localStorage.getItem('cafeCustomerName') || '';
        customerPhoneInput.value = localStorage.getItem('cafeCustomerPhone') || '';
        customerAddressInput.value = localStorage.getItem('cafeCustomerAddress') || '';
    }

    function closeCheckoutModal() {
        modal.classList.remove('visible');
        setTimeout(() => modal.style.display = 'none', 300);
    }

    async function placeOrder(event) {
        event.preventDefault();

        const customerName = customerNameInput.value.trim();
        const customerPhone = customerPhoneInput.value.trim();
        const customerAddress = customerAddressInput.value.trim();

        if (!customerName || !customerPhone) {
            alert("Vui lòng nhập Họ tên và Số điện thoại.");
            return;
        }

        localStorage.setItem('cafeCustomerName', customerName);
        localStorage.setItem('cafeCustomerPhone', customerPhone);
        localStorage.setItem('cafeCustomerAddress', customerAddress);

        const orderData = {
            customer: { name: customerName, phone: customerPhone, address: customerAddress },
            cart: cart
        };

        try {
            placeOrderButton.disabled = true;
            placeOrderButton.textContent = 'Đang gửi đơn...';

            const response = await fetch(orderApiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(orderData)
            });

            const responseData = await response.json();

            if (!response.ok) {
                throw new Error(responseData.message || `Lỗi khi đặt hàng: ${response.statusText}`);
            }

            alert(`Đặt hàng thành công! Đơn của bạn đã được ghi vào mục ${responseData.takeaway_id}.`);
            cart = {};
            saveCart();
            updateCartDisplay();
            closeCheckoutModal();

        } catch (error) {
            console.error("Lỗi đặt hàng:", error);
            alert(`Đã xảy ra lỗi khi gửi đơn hàng: ${error.message}`);
        } finally {
            placeOrderButton.disabled = false;
            placeOrderButton.textContent = 'Xác Nhận Đặt Hàng';
        }
    }

    function formatPrice(price) {
        if (typeof price !== 'number') { return 'N/A'; }
        return price.toLocaleString('vi-VN');
    }

    initApp();
});