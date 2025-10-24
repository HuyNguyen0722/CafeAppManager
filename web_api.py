import http.server
import socketserver
import json
import os
import io
import datetime
import traceback
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
APP_DIR = os.path.join(BASE_DIR, "App")
sys.path.insert(0, APP_DIR)

try:
    from utils.data_manager import (
        get_menu,
        get_tables,
        save_tables,
        MENU_FILE,
        TABLES_FILE,
    )
except ImportError as e:
    print(f"\nLỖI NGHIÊM TRỌNG: Không thể import từ 'utils.data_manager'.")
    print(f"Chi tiết: {e}")
    print("Vui lòng đảm bảo file 'App/utils/data_manager.py' là phiên bản MỚI NHẤT.")
    input("Nhấn Enter để thoát...")
    sys.exit(1)

PORT = 8000


class CustomHandler(http.server.SimpleHTTPRequestHandler):

    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_error_json(self, status_code, message):
        print(f"Sending error {status_code}: {message}")
        self.send_response(status_code)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(
            json.dumps({"status": "error", "message": message}).encode("utf-8")
        )

    def translate_path(self, path):
        path = http.server.SimpleHTTPRequestHandler.translate_path(self, path)
        rel_path = os.path.relpath(path, os.getcwd())
        full_path = os.path.join(BASE_DIR, rel_path)
        return full_path

    def do_GET(self):
        if self.path == "/api/menu":
            try:
                print(f"Đang đọc file menu từ: {MENU_FILE}")
                menu_data = get_menu()
                self._send_json_response(200, menu_data)
            except Exception as e:
                print(f"Lỗi 500 khi đọc file menu: {e}")
                self._send_error_json(500, f"Lỗi server khi đọc file: {e}")
            return

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/api/order_takeaway":
            try:
                print("\n--- Nhận được yêu cầu POST /api/order_takeaway ---")

                content_length = int(self.headers["Content-Length"])
                post_body = self.rfile.read(content_length)
                order_data = json.loads(post_body.decode("utf-8"))
                print(f"Dữ liệu nhận được: {order_data}")

                customer_info = order_data.get("customer", {})
                web_cart = order_data.get("cart", {})

                customer_name = customer_info.get("name", "Khách Online")
                customer_phone = customer_info.get("phone", "N/A")
                customer_address = customer_info.get("address", "N/A")

                print(f"Đang đọc file tables từ: {TABLES_FILE}")
                tables_data = get_tables()

                found_slot = False
                new_takeaway_id = ""

                for i, table in enumerate(tables_data):
                    table_id = table.get("id", "")
                    if (
                        str(table_id).startswith("takeaway")
                        and table.get("status") == "Sẵn sàng"
                    ):
                        print(f"Tìm thấy khe 'Mang về' trống: {table_id}")
                        new_order_dict = {}
                        for item_name, details in web_cart.items():
                            new_order_dict[item_name] = {
                                "price": details.get("price", 0),
                                "quantity": details.get("quantity", 1),
                            }
                        tables_data[i]["order"] = new_order_dict
                        tables_data[i][
                            "employee"
                        ] = f"{customer_name} | {customer_phone} | {customer_address}"
                        tables_data[i]["status"] = "Chờ xử lý"
                        found_slot = True
                        new_takeaway_id = table_id
                        break

                if not found_slot:
                    print("Không tìm thấy khe trống, tạo 'Mang về' mới...")
                    takeaway_count = sum(
                        1
                        for t in tables_data
                        if str(t.get("id", "")).startswith("takeaway")
                    )
                    new_takeaway_id = f"takeaway{takeaway_count + 1}"
                    new_order_dict = {}
                    for item_name, details in web_cart.items():
                        new_order_dict[item_name] = {
                            "price": details.get("price", 0),
                            "quantity": details.get("quantity", 1),
                        }
                    new_takeaway_entry = {
                        "id": new_takeaway_id,
                        "name": "Mang về",
                        "status": "Chờ xử lý",
                        "order": new_order_dict,
                        "employee": f"{customer_name} | {customer_phone} | {customer_address}",
                    }
                    tables_data.append(new_takeaway_entry)
                    print(f"Đã tạo mục mới: {new_takeaway_id}")

                save_tables(tables_data)

                print(f"Đã cập nhật đơn hàng thành công vào {TABLES_FILE}")

                self._send_json_response(
                    200,
                    {
                        "status": "success",
                        "message": "Đã nhận đơn hàng.",
                        "takeaway_id": new_takeaway_id,
                    },
                )

            except json.JSONDecodeError:
                self._send_error_json(400, "Lỗi: Dữ liệu gửi lên không phải JSON.")
            except Exception as e:
                print("\n--- LỖI 500 KHI XỬ LÝ POST ---")
                traceback.print_exc()
                print("---------------------------------")
                self._send_error_json(500, f"Lỗi server khi xử lý đơn hàng: {e}")
        else:
            self._send_error_json(404, "Đường dẫn POST không hợp lệ.")

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers", "X-Requested-With, Content-Type"
        )
        self.end_headers()


Handler = CustomHandler
try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"--- Server Python Đơn giản đang chạy tại cổng {PORT} ---")
        print(f"Mở trình duyệt và truy cập: http://localhost:{PORT}/Web/index.html")
        print(f"API Menu: http://localhost:{PORT}/api/menu")
        print("Nhấn Ctrl+C để tắt server.")
        httpd.serve_forever()
except OSError as e:
    print(f"\nLỖI: Không thể khởi động server trên cổng {PORT}.")
    print(f"Chi tiết: {e}")
    print("Có thể cổng này đang được sử dụng bởi một chương trình khác?")
