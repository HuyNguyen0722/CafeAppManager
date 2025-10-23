document.addEventListener('DOMContentLoaded', () => {
    const menuContainer = document.getElementById('menu-container');
    const categoryTabsContainer = document.getElementById('category-tabs'); // Lấy div chứa tab
    const apiUrl = '../App/data/menu.json';
    const placeholderImage = 'placeholder.png';
    let groupedMenu = {}; // Biến toàn cục để lưu menu đã nhóm

    async function fetchMenu() {
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`Không thể tải ${apiUrl}. Status: ${response.status}.`);
            }
            const menuItems = await response.json();

            // 1. Nhóm menu theo category
            groupedMenu = groupItemsByCategory(menuItems);

            // 2. Tạo các nút tab
            createCategoryTabs(Object.keys(groupedMenu)); // Lấy danh sách category từ object đã nhóm

            // 3. Hiển thị category đầu tiên mặc định
            if (Object.keys(groupedMenu).length > 0) {
                const firstCategory = Object.keys(groupedMenu)[0];
                displayCategoryItems(firstCategory); // Hiển thị món của category đầu tiên
                setActiveTab(firstCategory); // Đặt tab đầu tiên là active
            } else {
                menuContainer.innerHTML = '<p>Thực đơn hiện đang trống.</p>';
            }

        } catch (error) {
            console.error('Lỗi khi tải hoặc xử lý menu:', error);
            menuContainer.innerHTML = `<p class="error-message">Không thể tải thực đơn. Chi tiết: ${error.message}</p>`;
        }
    }

    // --- HÀM MỚI: Nhóm item theo category ---
    function groupItemsByCategory(items) {
        if (!Array.isArray(items)) return {}; // Trả về object rỗng nếu data lỗi
        return items.reduce((acc, item) => {
            if (typeof item !== 'object' || item === null) return acc;
            const category = item.category || 'Khác';
            if (!acc[category]) {
                acc[category] = [];
            }
            acc[category].push(item);
            return acc;
        }, {});
    }

    // --- HÀM MỚI: Tạo các nút tab ---
    function createCategoryTabs(categories) {
        categoryTabsContainer.innerHTML = ''; // Xóa nội dung cũ (nếu có)
        categories.forEach(category => {
            const tabButton = document.createElement('button');
            tabButton.classList.add('tab-button');
            tabButton.textContent = category;
            tabButton.dataset.category = category; // Lưu category vào data attribute

            // Thêm sự kiện click cho nút tab
            tabButton.addEventListener('click', () => {
                displayCategoryItems(category); // Hiển thị món của category này
                setActiveTab(category);       // Đặt tab này là active
            });

            categoryTabsContainer.appendChild(tabButton);
        });
    }

    // --- HÀM MỚI: Đặt trạng thái active cho tab ---
    function setActiveTab(activeCategory) {
        const tabButtons = categoryTabsContainer.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            if (button.dataset.category === activeCategory) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }


    // --- SỬA LẠI HÀM NÀY: Chỉ hiển thị món của 1 category ---
    function displayCategoryItems(category) {
        menuContainer.innerHTML = ''; // Xóa các món cũ

        const items = groupedMenu[category]; // Lấy danh sách món từ menu đã nhóm

        if (!items || items.length === 0) {
            menuContainer.innerHTML = '<p>Không có món nào trong danh mục này.</p>';
            return;
        }

        // Tạo grid container (nếu cần style riêng cho grid này)
        const gridContainer = document.createElement('div');
        gridContainer.classList.add('menu-grid'); // Dùng lại class cũ hoặc tạo class mới
        menuContainer.appendChild(gridContainer);


        items.forEach(item => {
            if (typeof item !== 'object' || item === null) return;

            const menuItemDiv = document.createElement('div');
            menuItemDiv.classList.add('menu-item');

            let imagePath = placeholderImage;
            if (item.image && typeof item.image === 'string') {
                imagePath = `../App/${item.image.replace(/\\/g, '/')}`;
            }

            const name = item.name || 'Chưa đặt tên';
            const price = item.price || 0;

            menuItemDiv.innerHTML = `
                <img
                    src="${imagePath}"
                    alt="${name}"
                    class="menu-item-image"
                    onerror="this.onerror=null; this.src='${placeholderImage}';"
                >
                <h3>${name}</h3>
                <p class="price">${formatPrice(price)} VND</p>
            `;
            // Thêm vào gridContainer thay vì menuContainer trực tiếp
            gridContainer.appendChild(menuItemDiv);
        });
    }
    // --- HẾT PHẦN SỬA ---

    // (Hàm formatPrice giữ nguyên)
    function formatPrice(price) {
        if (typeof price !== 'number') { return 'N/A'; }
        return price.toLocaleString('vi-VN');
    }

    // Gọi hàm fetch ban đầu
    fetchMenu();
});