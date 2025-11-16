import weaviate
import os
from dotenv import load_dotenv
import json
import pymysql
from weaviate.auth import AuthApiKey
from decimal import Decimal

load_dotenv()

# --- ENV ---
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

PRODUCT_VARIANT_CLASS_NAME = "ProductVariant"


# --- HÀM LẤY DỮ LIỆU TỪ MYSQL ---
def get_product_variants_from_mysql():
    variants = []

    sql = """
    SELECT
        p.TenSP AS name,
        p.MoTa AS description,
        p.Gia AS price,
        p.GiaGoc AS original_price,
        p.TrangThai AS status,
        th.TenTH AS category,
        bt.MauSac AS color,
        bt.LoaiSwitch AS switch_type,
        bt.SoLuongTon AS stock
    FROM bienthesp bt
    INNER JOIN sanpham p ON bt.MaSP = p.MaSP
    LEFT JOIN thuonghieu th ON p.MaTH = th.MaTH
    """

    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        )

        cur = conn.cursor()
        cur.execute(sql)

        for row in cur:
            price = float(row["price"]) if isinstance(row["price"], Decimal) else float(row["price"] or 0)
            original_price = float(row["original_price"]) if isinstance(row["original_price"], Decimal) else float(row["original_price"] or 0)

            if original_price == 0:
                original_price = price

            row["price"] = price
            row["original_price"] = original_price

            # --- SALE ---
            row["on_sale"] = original_price > price
            row["discount_amount"] = original_price - price if row["on_sale"] else 0
            row["discount_percentage"] = round((original_price - price) / original_price, 2) if row["on_sale"] else 0

            # Fix null
            row["color"] = row["color"] or "N/A"
            row["switch_type"] = row["switch_type"] or "N/A"
            row["category"] = row["category"] or "N/A"
            row["stock"] = int(row["stock"] or 0)
            row["status"] = row["status"] or "N/A"

            variants.append(row)

    except Exception as e:
        print("LỖI MYSQL:", e)

    return variants


# --- KẾT NỐI WEAVIATE ---
client = weaviate.Client(
    url=WEAVIATE_URL,
    auth_client_secret=AuthApiKey(WEAVIATE_API_KEY),
    additional_headers={"X-Weaviate-Cluster-Url": WEAVIATE_URL},
)

if not client.is_ready():
    print("❌ Weaviate chưa sẵn sàng!")
    exit()

print("✅ Đã kết nối Weaviate.")


# --- XOÁ SCHEMA CŨ ---
schema = client.schema.get()

if "classes" in schema:
    for c in schema["classes"]:
        client.schema.delete_class(c["class"])
        print(f"🗑️ Đã xoá class: {c['class']}")


# --- TẠO SCHEMA MỚI ---
schema_new = {
    "class": PRODUCT_VARIANT_CLASS_NAME,
    "description": "Biến thể sản phẩm",
    "vectorizer": "text2vec-weaviate",
    "moduleConfig": {
        "text2vec-weaviate": {
            "vectorizeClassName": False,
            "model": "Snowflake/snowflake-arctic-embed-l-v2.0"
        }
    },
    "properties": [
        {"name": "name", "dataType": ["text"]},
        {"name": "description", "dataType": ["text"]},
        {"name": "category", "dataType": ["text"]},
        {"name": "status", "dataType": ["text"]},
        {"name": "color", "dataType": ["text"]},
        {"name": "switch_type", "dataType": ["text"]},
        {"name": "stock", "dataType": ["int"]},
        {"name": "price", "dataType": ["number"]},
        {"name": "original_price", "dataType": ["number"]},
        {"name": "on_sale", "dataType": ["boolean"]},
        {"name": "discount_amount", "dataType": ["number"]},
        {"name": "discount_percentage", "dataType": ["number"]},
    ],
}

client.schema.create_class(schema_new)
print("✅ Đã tạo schema ProductVariant.")


# --- LẤY DỮ LIỆU MYSQL ---
variants = get_product_variants_from_mysql()

print(f"📦 Lấy được {len(variants)} biến thể từ MySQL.")


# --- IMPORT WEAVIATE ---
with client.batch as batch:
    batch.batch_size = 100

    for item in variants:
        batch.add_data_object(item, PRODUCT_VARIANT_CLASS_NAME)

print(f"🎉 Đã import {len(variants)} biến thể vào Weaviate thành công!")
