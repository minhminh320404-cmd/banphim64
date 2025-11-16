import os
import groq
# import weaviate <-- KHÔNG CẦN NỮA
import mysql.connector
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict 

# -----------------------------------------------------------------
# 1. TẢI BIẾN MÔI TRƯỜNG VÀ KHỞI TẠO APP
# -----------------------------------------------------------------
load_dotenv() 
app = FastAPI(
    title="Chatbot API (Text-to-SQL)",
    description="Một API nhận ngôn ngữ tự nhiên và truy vấn MySQL."
)
# -----------------------------------------------------------------
# 2B. CẤU HÌNH CORS
# -----------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)
# -----------------------------------------------------------------
# 2. KHỞI TẠO CÁC CLIENT (ĐÃ XÓA WEAVIATE)
# -----------------------------------------------------------------
# (WEAVIATE ĐÃ BỊ XÓA)

try:
    groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    print("Kết nối Groq API thành công.")
except Exception as e:
    print(f"LỖI NGHIÊM TRỌNG: KẾT NỐI GROQ THẤT BẠI: {e}")
    print("Kiểm tra lại .env (GROQ_API_KEY).")
    exit() 

# -----------------------------------------------------------------
# 3. ĐỊNH NGHĨA MODEL INPUT
# -----------------------------------------------------------------
class ChatQuery(BaseModel):
    query: str
    history: List[Dict[str, str]] = [] 

# -----------------------------------------------------------------
# 4. HÀM HARDCODE SCHEMA (Thay thế Weaviate)
# -----------------------------------------------------------------

# Chúng ta nhồi (hardcode) toàn bộ kiến thức vào đây
# Thay vì gọi Weaviate, chúng ta dùng biến này.
FULL_SCHEMA_CONTEXT = """
--- CONTEXT SCHEMA (TOÀN BỘ CSDL) ---
Bảng: 'sanpham'
Mô tả:
- MaSP (int): Khóa chính.
- MaTH (int): Khóa ngoại, liên kết đến 'thuonghieu'.
- TenSP (varchar): Tên đầy đủ của sản phẩm.
- Gia (decimal): Giá bán hiện tại.
- GiaGoc (decimal): Giá gốc.
**CÁCH DÙNG**: Dùng để tìm giá ('rẻ nhất', 'đắt nhất' dựa trên 'Gia'), tên, giá gốc.
---
Bảng: 'thuonghieu'
Mô tả:
- MaTH (int): Khóa chính.
- TenTH (varchar): Tên của thương hiệu (ví dụ: Logitech, Keychron, Akko).
**CÁCH DÙNG**: Dùng khi lọc theo thương hiệu.
---
Bảng: 'danhmuc'
Mô tả:
- MaDM (int): Khóa chính.
- TenDM (varchar): Tên của danh mục (ví dụ: Bàn phím cơ, Chuột không dây).
**CÁCH DÙNG**: Dùng khi lọc theo loại sản phẩm (ví dụ: 'tìm bàn phím', 'chuột gaming').
---
Bảng: 'bienthesp'
Mô tả:
- MaBienThe (int): Khóa chính.
- MaSP (int): Khóa ngoại, liên kết đến 'sanpham'.
- MauSac (varchar): Màu sắc của biến thể (ví dụ: Đen, Trắng).
- LoaiSwitch (varchar): Loại switch (ví dụ: Red Switch, Blue Switch).
- SoLuongTon (int): Số lượng tồn kho.
**CÁCH DÙNG**: Dùng khi hỏi về thuộc tính chi tiết ('màu trắng', 'switch gì') hoặc tồn kho ('còn hàng không').
---
Bảng: 'sanpham_danhmuc'
Mô tả:
- MaSP (int): Khóa ngoại.
- MaDM (int): Khóa ngoại.
**CÁCH DÙNG**: Bảng trung gian để JOIN 'sanpham' và 'danhmuc'.
---
"""

# -----------------------------------------------------------------
# 4. CÁC HÀM HỖ TRỢ KHÁC
# -----------------------------------------------------------------

def get_db_connection():
    # (Hàm này giữ nguyên)
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )
        if conn.is_connected():
            return conn
    except Exception as e:
        print(f"Lỗi kết nối CSDL: {e}")
        return None

def call_groq(prompt: str, model: str = "openai/gpt-oss-20b") -> str:
    # (Hàm này giữ nguyên)
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý AI."},
                {"role": "user", "content": prompt},
            ],
            model=model,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Lỗi khi gọi Groq: {e}")
        return f"Lỗi Groq: {e}"

def _classify_intent(user_query: str) -> str:
    # (Hàm này giữ nguyên)
    classification_prompt = f"""
    Dựa vào câu hỏi MỚI của người dùng: "{user_query}"
    Bất kể lịch sử chat, câu hỏi này là 'chitchat' (chào hỏi, cảm ơn, tạm biệt, hỏi thăm sức khỏe) 
    hay 'task' (hỏi về sản phẩm, giá, thông tin, đổi mật khẩu, hoặc bất kỳ công việc nào khác)?
    Chỉ trả lời bằng MỘT từ: CHITCHAT hoặc TASK.
    """
    print("GROQ (CLASSIFY): Phân loại intent...")
    intent = call_groq(classification_prompt)
    if "CHITCHAT" in intent.upper():
        print("GROQ (CLASSIFY): Kết quả = CHITCHAT")
        return "CHITCHAT"
    else:
        print("GROQ (CLASSIFY): Kết quả = TASK")
        return "TASK"

def _rewrite_query_with_history(user_query: str, history: List[Dict[str, str]]) -> str:
    # (Hàm này giữ nguyên)
    if not history:
        print("LỊCH SỬ CHAT: Trống. Dùng query gốc.")
        return user_query 
    formatted_history = ""
    for turn in history:
        role = "User" if turn["role"] == "user" else "Bot"
        formatted_history += f"{role}: {turn['content']}\n"
    rewrite_prompt = f"""
    Dưới đây là lịch sử chat:
    ---
    {formatted_history}
    ---
    Câu hỏi mới của người dùng (có thể là câu hỏi tiếp nối): "{user_query}"
    Hãy viết lại câu hỏi mới này thành một câu hỏi độc lập, đầy đủ ngữ cảnh mà không cần lịch sử chat.
    Chỉ trả về câu hỏi đã viết lại, không giải thích.
    """
    print("GROQ (REWRITE): Đang viết lại câu hỏi...")
    rewritten_query = call_groq(rewrite_prompt)
    print(f"GROQ (REWRITE): Đã viết lại: '{rewritten_query}'")
    if '"' in rewritten_query:
        rewritten_query = rewritten_query.replace('"', '')
    return rewritten_query

# (Hàm get_schema_from_weaviate ĐÃ BỊ XÓA)

def is_safe_select(sql_query: str) -> bool:
    # (Hàm này giữ nguyên)
    query_lower = sql_query.strip().lower()
    if query_lower.startswith("select"):
        if ";" in query_lower:
            parts = query_lower.split(";")
            if len(parts) > 2 or parts[1].strip():
                return False
        return True
    return False
# -----------------------------------------------------------------


# -----------------------------------------------------------------
# 5. ENDPOINT CHAT CHÍNH (ĐÃ BỎ WEAVIATE VÀ GUARDRAIL CŨ)
# -----------------------------------------------------------------
@app.post("/api/chat")
async def handle_chat(request: ChatQuery):
    
    user_query = request.query
    history = request.history
    print(f"Đã nhận query: '{user_query}' (với {len(history)} lượt chat)")

    try:
        # ---- BƯỚC 1.1: PHÂN LOẠI INTENT ----
        intent_type = _classify_intent(user_query)
        
        # ---- LUỒNG 1: XỬ LÝ CHITCHAT ----
        if intent_type == "CHITCHAT":
            print("LOGIC: Đang xử lý CHITCHAT.")
            chitchat_prompt = f"""
            Người dùng vừa nói một câu chào hỏi/chitchat: "{user_query}"
            Hãy trả lời lại một cách thân thiện, ngắn gọn.
            """
            final_answer = call_groq(chitchat_prompt)
            return JSONResponse(content={"answer": final_answer})

        # ---- LUỒNG 2: XỬ LÝ TASK ----
        print("LOGIC: Đang xử lý TASK.")
        
        # ---- BƯỚC 1.5: VIẾT LẠI CÂU HỎI ----
        standalone_query = _rewrite_query_with_history(user_query, history)
        
        # (ĐÃ XÓA BƯỚC 2 & 3: Lấy Schema Context từ Weaviate)
        # (ĐÃ XÓA BƯỚC 3.5: GUARDRAIL CŨ)

        # -----------------------------------------------------------------
        # ---- BƯỚC 4: Xây dựng "SIÊU PROMPT" (Thay thế Weaviate) ----
        # -----------------------------------------------------------------
        sql_prompt = f"""
        Bạn là một chuyên gia MySQL. Dựa vào CẤU TRÚC SCHEMA (CONTEXT) được cung cấp dưới đây:
        {FULL_SCHEMA_CONTEXT}
        
        Hãy viết MỘT câu lệnh SQL (chỉ SQL) để trả lời câu hỏi sau:
        "{standalone_query}" 

        QUY TẮC BẮT BUỘC (PHẢI TUÂN THỦ 100%):
        1. Chỉ trả về code SQL. Không giải thích.
        
        2. **TUYỆT ĐỐI CẤM** tự ý bịa ra tên bảng hoặc tên cột. Dùng tên chính xác 100% như trong CONTEXT.
        
        3. **BẢNG TRA CỨU CỘT (PHẢI NHỚ):**
           - 'Màu sắc' nằm ở `bienthesp.MauSac`.
           - 'Loại switch' nằm ở `bienthesp.LoaiSwitch`.
           - 'Giá' nằm ở `sanpham.Gia`.
           - 'Tên sản phẩm' nằm ở `sanpham.TenSP`.
           - 'Tên danh mục' nằm ở `danhmuc.TenDM`.
           - 'Sản phẩm rẻ nhất' -> `ORDER BY sanpham.Gia ASC LIMIT 1`
           - 'Sản phẩm đắt nhất' -> `ORDER BY sanpham.Gia DESC LIMIT 1`

        4. **LOGIC TÌM KIẾM:** Dùng `LIKE '%từ_khóa%'` cho các cột văn bản (như `TenDM`, `TenSP`) thay vì `='từ_khóa'`.

        5. **LOGIC JOIN (QUAN TRỌNG):**
           - **BẮT BUỘC** JOIN `bienthesp` (dùng `sp.MaSP = bp.MaSP`) nếu câu hỏi chứa 'màu sắc' hoặc 'loại switch'.
           - CHỈ JOIN `danhmuc` (dùng `sp.MaSP = sd.MaSP` VÀ `sd.MaDM = d.MaDM`) nếu câu hỏi lọc theo danh mục (như 'bàn phím', 'chuột').
           
        6. **LOGIC KHÓA (KEYS):**
           - Khi JOIN `sanpham` (sp) và `bienthesp` (bp), BẮT BUỘC dùng `sp.MaSP = bp.MaSP`.
           - Khi JOIN `sanpham` (sp) và `sanpham_danhmuc` (sd), BẮT BUỘC dùng `sp.MaSP = sd.MaSP`.

        7. **GUARDRAIL MỚI:** - Nếu câu hỏi không thể trả lời bằng cách truy vấn các bảng đã cho (ví dụ: 'đổi mật khẩu', 'đăng ký', 'tên của bạn là gì?'), 
           - hãy chỉ trả về MỘT TỪ: `CANNOT_ANSWER`
        """
        
        # ---- BƯỚC 5: Gọi Groq để Viết SQL ----
        print("GROQ (SQL): Đang tạo SQL...")
        sql_query = call_groq(sql_prompt)

        # --- DỌN RÁC NÂNG CAO ---
        # (Giữ nguyên logic dọn rác 'l', '```sql', ...)
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"): sql_query = sql_query[5:]
        if sql_query.endswith("```"): sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        select_pos = sql_query.lower().find("select")
        if select_pos != -1:
            sql_query = sql_query[select_pos:]
        else:
            # Nếu Groq trả về "CANNOT_ANSWER", nó sẽ không tìm thấy "select"
            # và sql_query sẽ bị gán rỗng (hoặc giữ nguyên "CANNOT_ANSWER")
            pass # Để logic guardrail mới xử lý
        # --- KẾT THÚC DỌN RÁC ---

        print(f"GROQ (SQL): Đã tạo SQL (đã làm sạch): {sql_query}")

        # -----------------------------------------------------------------
        # ---- BƯỚC 6 (Phần 1): GUARDRAIL MỚI & KIỂM TRA AN TOÀN ----
        # -----------------------------------------------------------------
        # 1. Kiểm tra Guardrail (LLM tự từ chối)
        if "CANNOT_ANSWER" in sql_query.upper():
            print("GUARDRAIL (LLM): Câu hỏi ngoài phạm vi. Trả lời từ chối.")
            return JSONResponse(content={"answer": "Xin lỗi, tôi chỉ có thể trả lời các câu hỏi liên quan đến sản phẩm, danh mục và thương hiệu."})

        # 2. Kiểm tra an toàn (SQL Injection)
       # 2. Kiểm tra an toàn (SQL Injection, DELETE, UPDATE...)
        if not is_safe_select(sql_query):
            print(f"AN NINH: Query không an toàn bị chặn (ví dụ: DELETE, UPDATE): {sql_query}")

            # Trả về câu trả lời thân thiện theo yêu cầu của bạn
            return JSONResponse(content={"answer": "Xin lỗi, tôi chỉ có thể trả lời các câu hỏi liên quan đến sản phẩm, danh mục và thương hiệu."})
        # ---- BƯỚC 6 (Phần 2): Thực thi SQL trên MySQL ----
        print(f"MYSQL: Đang chạy: {sql_query}")
        conn = get_db_connection()
        if not conn:
            return JSONResponse(status_code=500, content={"answer": "Lỗi: Không thể kết nối CSDL."})
        
        cursor = conn.cursor(dictionary=True) 
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        
        print(f"MYSQL: Đã trả về {len(results)} dòng.")

        if not results:
            return JSONResponse(content={"answer": "Xin lỗi, tôi không tìm thấy kết quả nào."})

        # ---- BƯỚC 7: Gọi Groq (Lần 2) để Diễn giải kết quả ----
        print("GROQ (HUMANIZE): Đang diễn giải kết quả...")
        humanize_prompt = f"""
        Dựa vào câu hỏi gốc (đã được viết lại): "{standalone_query}"
        Và dữ liệu SQL trả về (dạng JSON):
        {json.dumps(results, default=str, ensure_ascii=False)}

        Hãy viết một câu trả lời thân thiện, đầy đủ ý cho người dùng.
        """
        
        final_answer = call_groq(humanize_prompt, model="openai/gpt-oss-20b")
        
        # ---- BƯỚC 8: Trả về Frontend ----
        return JSONResponse(content={"answer": final_answer})

    except Exception as e:
        print(f"LỖI TOÀN HỆ THỐNG: {e}")
        return JSONResponse(status_code=500, content={"answer": f"Đã xảy ra lỗi: {e}"})

# -----------------------------------------------------------------
# 6. CHẠY LOCAL
# -----------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("Khởi động server local tại [http://127.0.0.1:8000](http://127.0.0.1:8000)")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)