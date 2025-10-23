from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QListWidget, QListWidgetItem,
    QMessageBox, QSpinBox, QWidget, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
import os
import datetime
import uuid
import platform
import subprocess

from utils.data_manager import (
    get_menu, PROJECT_ROOT, save_receipt, 
    RECEIPTS_PRINT_DIR
)

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_INSTALLED = True
except ImportError:
    REPORTLAB_INSTALLED = False
    print("CẢNH BÁO: Thư viện 'reportlab' chưa được cài. In PDF sẽ không hoạt động.")
# -------------------------------------------


class GridMenuItemWidget(QPushButton):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.setFixedSize(140, 140)
        self.setObjectName("gridMenuItem")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        image_label = QLabel()
        image_label.setFixedSize(80, 80)
        image_label.setObjectName("gridItemImage")
        image_path = item_data.get("image", "")
        
        # --- SỬA LẠI: Đường dẫn ảnh (image_path là 'data/images/...') ---
        full_image_path = os.path.join(PROJECT_ROOT, image_path)
        
        if image_path and os.path.exists(full_image_path):
             pixmap = QPixmap(full_image_path)
             image_label.setPixmap(pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            image_label.setText("🍽️")
        
        name_label = QLabel(item_data.get("name", "N/A"))
        name_label.setObjectName("gridItemName")
        name_label.setWordWrap(True)
        
        price_label = QLabel(f"{item_data.get('price', 0):,.0f} VND")
        price_label.setObjectName("gridItemPrice")

        layout.addWidget(image_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(price_label, 0, Qt.AlignmentFlag.AlignCenter)


class OrderDialog(QDialog):
    # (Hàm __init__ và init_ui giữ nguyên)
    def __init__(self, table_data, current_user, parent=None):
        super().__init__(parent)
        self.table_data = table_data
        self.current_user = current_user
        self.menu = get_menu()
        
        self.setWindowTitle(f"Bàn {self.table_data['id']} - Hóa đơn")
        self.setMinimumSize(1400, 750) 
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.init_ui()
        self.update_order_summary()
        self.apply_stylesheet()
        
    def init_ui(self):
        # (Giữ nguyên toàn bộ hàm init_ui)
        category_panel = QFrame()
        category_panel.setObjectName("categoryPanel")
        category_panel.setFixedWidth(200)
        category_layout = QVBoxLayout(category_panel)
        category_title = QLabel("Danh mục")
        category_title.setObjectName("panelTitle")
        self.category_list = QListWidget()
        self.category_list.setObjectName("categoryList")
        categories = sorted(list(set(item['category'] for item in self.menu if 'category' in item)))
        self.category_list.addItems(categories)
        self.category_list.itemClicked.connect(self.filter_menu_by_category)
        category_layout.addWidget(category_title)
        category_layout.addWidget(self.category_list)
        menu_panel = QFrame()
        menu_layout = QVBoxLayout(menu_panel)
        menu_title = QLabel("Chọn món")
        menu_title.setObjectName("panelTitle")
        self.menu_items_grid_widget = QWidget()
        self.menu_items_grid = QGridLayout(self.menu_items_grid_widget)
        self.menu_items_grid.setAlignment(Qt.AlignmentFlag.AlignTop) 
        self.menu_items_grid.setSpacing(15) 
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.menu_items_grid_widget)
        scroll_area.setObjectName("menuScrollArea")
        menu_layout.addWidget(menu_title)
        menu_layout.addWidget(scroll_area)
        order_panel = QFrame()
        order_panel.setObjectName("orderPanel")
        order_panel.setFixedWidth(320)
        order_layout = QVBoxLayout(order_panel)
        order_title = QLabel("Món đã gọi")
        order_title.setObjectName("panelTitle")
        self.order_list = QListWidget()
        self.order_list.setObjectName("orderList")
        self.total_label = QLabel("Tổng cộng: 0 VND")
        self.total_label.setObjectName("totalLabel")
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Xác nhận")
        self.confirm_button.setObjectName("confirmButton")
        self.checkout_button = QPushButton("Thanh toán")
        self.checkout_button.setObjectName("checkoutButton")
        self.cancel_button = QPushButton("Hủy")
        self.cancel_button.setObjectName("cancelButton")
        self.confirm_button.clicked.connect(self.handle_confirm)
        self.checkout_button.clicked.connect(self.handle_checkout)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.checkout_button)
        button_layout.addWidget(self.confirm_button)
        order_layout.addWidget(order_title)
        order_layout.addWidget(self.order_list, 1)
        order_layout.addWidget(self.total_label)
        order_layout.addLayout(button_layout)
        self.main_layout.addWidget(category_panel)
        self.main_layout.addWidget(menu_panel, 1)
        self.main_layout.addWidget(order_panel)
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)
            self.filter_menu_by_category(self.category_list.item(0))

    # (Các hàm filter_menu_by_category, add_item_to_order, 
    # update_order_summary, create_order_item_widget, 
    # change_item_quantity, remove_item_from_order, handle_confirm
    # giữ nguyên như cũ)
    def filter_menu_by_category(self, category_item):
        while self.menu_items_grid.count():
            child = self.menu_items_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        selected_category = category_item.text()
        filtered_menu = [item for item in self.menu if item.get('category') == selected_category]
        row, col = 0, 0
        for item in filtered_menu:
            if isinstance(item, dict):
                item_widget = GridMenuItemWidget(item)
                item_widget.clicked.connect(lambda ch, d=item: self.add_item_to_order(d))
                self.menu_items_grid.addWidget(item_widget, row, col)
                col += 1
                if col >= 3: 
                    col = 0
                    row += 1

    def add_item_to_order(self, item_data):
        item_name = item_data['name']
        if not isinstance(self.table_data.get('order'), dict):
            self.table_data['order'] = {}
        order = self.table_data.get('order', {})
        if item_name in order:
            order[item_name]['quantity'] += 1
        else:
            order[item_name] = {'price': item_data['price'], 'quantity': 1}
        self.update_order_summary()

    def update_order_summary(self):
        self.order_list.clear()
        total_price = 0
        current_order = self.table_data.get('order', {})
        if not isinstance(current_order, dict):
            current_order = {} 
        for item_name, details in current_order.items():
            item_widget = self.create_order_item_widget(item_name, details)
            list_item = QListWidgetItem(self.order_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.order_list.addItem(list_item)
            self.order_list.setItemWidget(list_item, item_widget)
            total_price += details['price'] * details['quantity']
        self.total_label.setText(f"Tổng cộng: {total_price:,.0f} VND")
        self.checkout_button.setEnabled(bool(current_order))

    def create_order_item_widget(self, name, details):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5) 
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(0)
        name_label = QLabel(name)
        name_label.setObjectName("orderItemName")
        unit_price_label = QLabel(f"@ {details['price']:,.0f} VND")
        unit_price_label.setObjectName("orderItemUnitPrice")
        info_layout.addWidget(name_label)
        info_layout.addWidget(unit_price_label)
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0,0,0,0)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        quantity_spinbox = QSpinBox()
        quantity_spinbox.setObjectName("quantitySpinBox")
        quantity_spinbox.setRange(1, 99)
        quantity_spinbox.setValue(details['quantity'])
        quantity_spinbox.setFixedWidth(50)
        quantity_spinbox.valueChanged.connect(lambda value, n=name: self.change_item_quantity(n, value))
        price_label = QLabel(f"{details['price'] * details['quantity']:,.0f}")
        price_label.setObjectName("orderItemPriceTotal")
        price_label.setMinimumWidth(80)
        price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        remove_button = QPushButton("🗑️")
        remove_button.setObjectName("removeButton")
        remove_button.setFixedSize(30, 30)
        remove_button.clicked.connect(lambda: self.remove_item_from_order(name))
        controls_layout.addWidget(quantity_spinbox)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(price_label)
        controls_layout.addSpacing(5)
        controls_layout.addWidget(remove_button)
        layout.addWidget(info_widget, 1)
        layout.addWidget(controls_widget)
        return widget

    def change_item_quantity(self, item_name, quantity):
        order = self.table_data.get('order', {})
        if item_name in order:
            order[item_name]['quantity'] = quantity
        self.update_order_summary()

    def remove_item_from_order(self, item_name):
        order = self.table_data.get('order', {})
        if item_name in order:
            del order[item_name]
        self.update_order_summary()

    def handle_confirm(self):
        if not self.table_data.get('order') or not isinstance(self.table_data.get('order'), dict):
             QMessageBox.information(self, "Thông báo", "Chưa có món nào được gọi.")
             return
        self.table_data['status'] = "Có khách"
        self.table_data['employee'] = self.current_user
        self.accept()

    def handle_checkout(self):
        current_order = self.table_data.get('order', {})
        if not current_order or not isinstance(current_order, dict): 
            QMessageBox.warning(self, "Lỗi", "Không có đơn hàng để thanh toán.")
            return
        total_price = sum(details['price'] * details['quantity'] for details in current_order.values())
        reply = QMessageBox.question(self, "Xác nhận Thanh toán",
                                     f"Tổng hóa đơn là: {total_price:,.0f} VND.\n\nXác nhận thanh toán và in hóa đơn?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                receipt = {
                    "id": str(uuid.uuid4()),
                    "table_id": self.table_data['id'],
                    "employee": self.current_user,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "items": current_order, 
                    "total": total_price
                }
                save_receipt(receipt)
                self.print_receipt_pdf(receipt)
            except Exception as e:
                print(f"Lỗi khi lưu/in hóa đơn: {e}")
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu hoặc in hóa đơn: {e}")
                return
            self.table_data['order'] = {}
            self.table_data['status'] = "Trống"
            self.table_data['employee'] = None
            QMessageBox.information(self, "Thành công", f"Đã thanh toán cho Bàn {self.table_data['id']}.\nHóa đơn PDF đã được tạo.")
            self.accept()

    # --- CẬP NHẬT: Hàm in PDF ---
    def print_receipt_pdf(self, receipt_data):
        if not REPORTLAB_INSTALLED:
            QMessageBox.critical(self, "Lỗi", "Thư viện 'reportlab' chưa được cài đặt.\nKhông thể in PDF. Vui lòng cài đặt: pip install reportlab")
            return

        # --- 1. Đăng ký Font (Quan trọng) ---
        font_name = "VNF_Arial"
        # --- SỬA LẠI: 'fonts' (đúng như trong ảnh) và dùng PROJECT_ROOT ---
        font_path = os.path.join(PROJECT_ROOT, 'fonts', 'times.ttf')
        # -----------------------------------------------------------
        
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        except Exception as e:
            print(f"Lỗi đăng ký font: {e}")
            print(f"HƯỚNG DẪN: Đảm bảo file 'times.ttf' có trong thư mục '{os.path.join(PROJECT_ROOT, 'fonts')}'")
            QMessageBox.warning(self, "Lỗi Font", "Không tìm thấy file font 'times.ttf' trong thư mục 'fonts'.\nFile PDF sẽ dùng font mặc định và có thể lỗi tiếng Việt.")
            font_name = "Helvetica"

        # --- 2. Tạo file và Canvas ---
        now = datetime.datetime.fromisoformat(receipt_data['timestamp'])
        filename = f"HD_{now.strftime('%Y%m%d_%H%M%S')}_{receipt_data['id'][:4]}.pdf"
        filepath = os.path.join(RECEIPTS_PRINT_DIR, filename)

        receipt_width = 80 * mm
        receipt_height = 200 * mm
        
        c = canvas.Canvas(filepath, pagesize=(receipt_width, receipt_height))

        # (Phần còn lại của hàm print_receipt_pdf giữ nguyên)
        y = receipt_height - (10 * mm)
        margin_left = 7 * mm
        margin_right = receipt_width - margin_left
        line_height_normal = 5 * mm
        line_height_small = 4 * mm
        c.setFont(font_name, 14)
        c.drawCentredString(receipt_width / 2, y, "TÊN QUÁN CAFE")
        y -= line_height_normal * 1.5
        c.setFont(font_name, 9)
        c.drawCentredString(receipt_width / 2, y, "Địa chỉ quán của bạn...")
        y -= line_height_normal
        c.drawCentredString(receipt_width / 2, y, "============================")
        y -= line_height_normal
        c.setFont(font_name, 10)
        c.drawCentredString(receipt_width / 2, y, f"HOÁ ĐƠN (Bàn {receipt_data['table_id']})")
        y -= line_height_normal
        c.setFont(font_name, 9)
        c.drawString(margin_left, y, f"Mã HĐ: {receipt_data['id'][:8]}...")
        y -= line_height_small
        c.drawString(margin_left, y, f"Ngày: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        y -= line_height_small
        c.drawString(margin_left, y, f"Thu ngân: {receipt_data['employee']}")
        y -= line_height_normal
        c.drawCentredString(receipt_width / 2, y, "--------------------------------------------------")
        y -= line_height_normal
        c.setFont(font_name, 9)
        c.drawString(margin_left, y, "Tên món")
        c.drawRightString(margin_right, y, "Th.Tiền")
        c.drawRightString(margin_right - (15 * mm), y, "Đ.Giá")
        c.drawRightString(margin_right - (30 * mm), y, "SL")
        y -= line_height_small
        items = receipt_data.get('items', {})
        for item_name, details in items.items():
            y -= line_height_normal
            qty = details.get('quantity', 0)
            price = details.get('price', 0)
            subtotal = qty * price
            name = (item_name[:12] + '..') if len(item_name) > 14 else item_name
            c.setFont(font_name, 9)
            c.drawString(margin_left, y, name)
            c.drawRightString(margin_right, y, f"{subtotal:,.0f}")
            c.drawRightString(margin_right - (15 * mm), y, f"{price:,.0f}")
            c.drawRightString(margin_right - (30 * mm), y, str(qty))
        y -= line_height_normal
        c.drawCentredString(receipt_width / 2, y, "--------------------------------------------------")
        y -= line_height_normal
        c.setFont(font_name, 12)
        c.drawRightString(margin_right, y, f"TỔNG CỘNG: {receipt_data['total']:,.0f} VND")
        y -= line_height_normal * 2
        c.setFont(font_name, 10)
        c.drawCentredString(receipt_width / 2, y, "Cảm ơn quý khách!")
        y -= line_height_small
        c.drawCentredString(receipt_width / 2, y, "Hẹn gặp lại!")
        c.showPage()
        c.save()

        try:
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', filepath])
            else:
                subprocess.run(['xdg-open', filepath])
        except Exception as e:
            print(f"Không thể mở file PDF: {e}")
            QMessageBox.warning(self, "Lỗi in", f"Không thể tự động mở file PDF.\nFile đã được lưu tại: {filepath}")

    # (Hàm apply_stylesheet giữ nguyên)
    def apply_stylesheet(self):
        self.setStyleSheet("""
            QDialog { background-color: #f0f2f5; font-family: Inter; }
            QFrame#categoryPanel, QFrame#orderPanel { 
                background-color: #ffffff; 
                border-radius: 8px; 
            }
            #panelTitle { 
                font-size: 18px; font-weight: bold; padding: 10px; 
                color: #343a40; border-bottom: 1px solid #e9ecef; 
            }
            QListWidget, #menuScrollArea { border: none; }
            
            #categoryList::item { 
                padding: 12px 15px; border-bottom: 1px solid #f0f2f5; font-size: 15px;
            }
            #categoryList::item:selected { 
                background-color: #e7f3ff; color: #007bff; font-weight: bold;
                border-left: 3px solid #007bff;
            }
            
            QPushButton#gridMenuItem { 
                background-color: #ffffff; border: 1px solid #dee2e6;
                border-radius: 8px; text-align: center;
            }
            QPushButton#gridMenuItem:hover { background-color: #f8f9fa; }
            #gridItemImage { 
                background-color: #f8f9fa; border-radius: 8px; font-size: 40px; 
                color: #adb5bd; qproperty-alignment: 'AlignCenter';
            }
            #gridItemName { font-size: 14px; font-weight: bold; color: #212529; }
            #gridItemPrice { font-size: 13px; color: #495057; }
            
            /* --- Order Summary Styles --- */
            #orderList::item { border-bottom: 1px solid #f0f2f5; }
            #orderItemName { font-size: 15px; font-weight: 500; color: #212529; }
            #orderItemUnitPrice { font-size: 12px; color: #6c757d; }
            #orderItemPriceTotal { font-size: 14px; color: #212529; font-weight: 500; }
            #totalLabel { font-size: 20px; font-weight: bold; color: #28a745; padding: 10px; }
            #removeButton { background-color: transparent; border: none; font-size: 16px; }
            QSpinBox#quantitySpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 10px;
                margin-left: -5px;
            }
            
            /* --- Button Styles --- */
            QPushButton { padding: 10px 15px; border-radius: 5px; font-weight: bold; border: 1px solid #ced4da; }
            QPushButton#confirmButton { background-color: #007bff; color: white; border: none; }
            QPushButton#checkoutButton { background-color: #28a745; color: white; border: none; }
            QPushButton#cancelButton { background-color: #6c757d; color: white; border: none; }
            QPushButton:hover { background-color: #e9ecef; }
            QPushButton#confirmButton:hover { background-color: #0056b3; }
            QPushButton#checkoutButton:hover { background-color: #218838; }
            QPushButton#cancelButton:hover { background-color: #5a6268; }
        """)