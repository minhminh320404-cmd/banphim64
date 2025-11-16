import weaviate
import os

# -----------------------------------------------------------------
# 1. CẤU HÌNH (THAY THÔNG TIN CỦA BẠN VÀO ĐÂY)
# -----------------------------------------------------------------
# Lấy từ trang quản lý Weaviate Cloud Sandbox (Cluster Details -> Show API keys)
WEAVIATE_URL = "https://pkrv8ayzqtwuazs6zypjgg.c0.asia-southeast1.gcp.weaviate.cloud" 
WEAVIATE_API_KEY = "NlVFWE9RallVd0plK1k1Ml9SL1poK3F1Rm9sKzlFQURPNFVFcnUyeXpNS0V0cThrVkJhQzNhZUQ3WTFJPV92MjAw" # Key "read-write"

# -----------------------------------------------------------------
# 2. KHỞI TẠO CLIENT
# -----------------------------------------------------------------
try:
    auth_config = weaviate.auth.AuthApiKey(api_key=WEAVIATE_API_KEY)
    client = weaviate.Client(
        url=WEAVIATE_URL,
        auth_client_secret=auth_config,
        # Nếu dùng Cohere API Key (tùy chọn, tùy sandbox của bạn)
        # headers={
        #     "X-Cohere-Api-Key": "YOUR_COHERE_API_KEY" 
        # }
    )
    print("Kết nối đến Weaviate Cloud thành công!")
except Exception as e:
    print(f"Lỗi kết nối Weaviate: {e}")
    exit()

# -----------------------------------------------------------------
# 3. ĐỊNH NGHĨA "CLASS" (NHƯ BẢNG) TRONG WEAVIATE
# -----------------------------------------------------------------
# Class này sẽ lưu trữ các mô tả schema của bạn
class_name = "MySQLSchema" 
class_obj = {
    "class": class_name,
    "description": "Lưu trữ mô tả về cấu trúc (schema) của các bảng MySQL.",
    "properties": [
        {
            "name": "table_name", # Tên bảng
            "dataType": ["text"],
            "description": "Tên của bảng trong MySQL (ví dụ: sanpham, danhmuc)."
        },
        {
            "name": "schema_description", # Mô tả chi tiết
            "dataType": ["text"],
            "description": "Mô tả chi tiết về bảng đó, các cột, và mối quan hệ."
        }
    ],
    # Weaviate Cloud Sandbox miễn phí thường có sẵn vectorizer (như text2vec-transformers)
    # hoặc bạn đã cấu hình Cohere/OpenAI khi tạo sandbox.
    # Chúng ta không cần định nghĩa rõ ở đây, nó sẽ dùng vectorizer mặc định.
}

# Xóa Class cũ nếu có (để làm sạch) và tạo mới
try:
    if client.schema.exists(class_name):
        print(f"Đã thấy '{class_name}'. Xóa đi để tạo mới...")
        client.schema.delete_class(class_name)
    
    client.schema.create_class(class_obj)
    print(f"Tạo class '{class_name}' thành công.")
except Exception as e:
    print(f"Lỗi khi tạo class: {e}")
    exit()

# -----------------------------------------------------------------
# 4. DATA: MÔ TẢ SCHEMA (ĐÃ NÂNG CẤP)
# -----------------------------------------------------------------
# Chúng ta thêm ví dụ về CÁCH DÙNG vào mô tả, 
# giúp Weaviate hiểu các khái niệm như "rẻ nhất", "tồn kho"...
schema_data = [
    {
        "table_name": "sanpham",
        "description": """
        Bảng 'sanpham' (Sản phẩm) chứa thông tin chung về sản phẩm.
        - MaSP (int): Khóa chính, ID duy nhất của sản phẩm.
        - MaTH (int): Khóa ngoại, liên kết đến bảng 'thuonghieu'.
        - TenSP (varchar): Tên đầy đủ của sản phẩm.
        - Gia (decimal): Giá bán hiện tại (giá đã giảm) của sản phẩm.
        - GiaGoc (decimal): Giá gốc (giá chưa giảm) của sản phẩm.
        
        **CÁCH DÙNG**: Dùng bảng này để trả lời các câu hỏi về:
        1. Giá sản phẩm (ví dụ: 'giá bao nhiêu?', 'so sánh giá').
        2. Tìm sản phẩm **đắt nhất** (ORDER BY Gia DESC).
        3. Tìm sản phẩm **rẻ nhất** (ORDER BY Gia ASC).
        """
    },
    {
        "table_name": "thuonghieu",
        "description": """
        Bảng 'thuonghieu' (Thương hiệu) chứa thông tin về nhà sản xuất.
        - MaTH (int): Khóa chính, ID duy nhất của thương hiệu.
        - TenTH (varchar): Tên của thương hiệu (ví dụ: Logitech, Keychron, Akko).
        
        **CÁCH DÙNG**: Dùng bảng này khi người dùng lọc theo thương hiệu (ví dụ: 'sản phẩm của Akko', 'có hàng Logitech không?').
        """
    },
    {
        "table_name": "danhmuc",
        "description": """
        Bảng 'danhmuc' (Danh mục) dùng để phân loại sản phẩm.
        - MaDM (int): Khóa chính, ID duy nhất của danh mục.
        - TenDM (varchar): Tên của danh mục (ví dụ: Bàn phím cơ, Chuột không dây).
        
        **CÁCH DÙNG**: Dùng bảng này khi người dùng lọc theo loại sản phẩm (ví dụ: 'tìm bàn phím', 'có chuột gaming không?').
        """
    },
    {
        "table_name": "bienthesp",
        "description": """
        Bảng 'bienthesp' (Biến thể sản phẩm) chứa các phiên bản khác nhau của một sản phẩm.
        - MaBienThe (int): Khóa chính, ID duy nhất của biến thể.
        - MaSP (int): Khóa ngoại, liên kết đến sản phẩm gốc trong bảng 'sanpham'.
        - MauSac (varchar): Màu sắc của biến thể (ví dụ: Đen, Trắng).
        - LoaiSwitch (varchar): Loại switch (ví dụ: Red Switch, Blue Switch).
        - SoLuongTon (int): Số lượng tồn kho *cụ thể* của biến thể này.
        
        **CÁCH DÙNG**: Dùng bảng này khi người dùng hỏi về:
        1. Thuộc tính chi tiết (ví dụ: 'có màu trắng không?', 'gồm switch gì?').
        2. Kiểm tra **tồn kho** hoặc **còn hàng không** (ví dụ: 'sản phẩm X còn hàng không?' -> SUM(SoLuongTon) > 0).
        """
    },
    {
        "table_name": "sanpham_danhmuc",
        "description": """
        Bảng 'sanpham_danhmuc' là bảng trung gian (pivot table) để xử lý mối quan hệ Nhiều-Nhiều (N-N) giữa 'sanpham' và 'danhmuc'.
        - MaSP (int): Khóa ngoại, liên kết đến bảng 'sanpham'.
        - MaDM (int): Khóa ngoại, liên kết đến bảng 'danhmuc'.
        
        **CÁCH DÙNG**: Luôn dùng bảng này để JOIN giữa `sanpham` và `danhmuc`.
        """
    }
]
# -----------------------------------------------------------------
# 5. ĐẨY DATA VÀO WEAVIATE (BATCH MODE)
# -----------------------------------------------------------------
print("Bắt đầu đẩy dữ liệu schema lên Weaviate...")
try:
    with client.batch as batch:
        batch.batch_size = 5 # Đẩy 5 item một lúc
        
        for item in schema_data:
            properties = {
                "table_name": item["table_name"],
                "schema_description": item["description"].strip().replace("    ", "") # Xóa khoảng trắng thừa
            }
            
            batch.add_data_object(
                data_object=properties,
                class_name=class_name
            )

    print(f"Đã đẩy và vector hóa {len(schema_data)} mô tả schema lên Weaviate thành công!")
    print("Bạn có thể kiểm tra dữ liệu trong Weaviate Cloud Console.")

except Exception as e:
    print(f"Lỗi khi đẩy dữ liệu: {e}")