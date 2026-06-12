import os
import json
import re
import requests
import random
import logging
import math
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional, Generator
from abc import ABC, abstractmethod
from openai import OpenAI
import uuid
from google import genai
from google.genai import types

# Configure logging for the agent module
logger = logging.getLogger("vaccine-assistant-agent")

# Paths to databases
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "mock_data")

# Databases cached in memory
VACCINES_DB = []
COMBOS_DB = []
DOCTORS_DB = []
STORES_DB = []

def load_databases():
    global VACCINES_DB, COMBOS_DB, DOCTORS_DB, STORES_DB
    logger.info("Khởi chạy nạp cơ sở dữ liệu Long Châu vào bộ nhớ...")
    
    # 1. Load vaccines
    vaccine_path = os.path.join(DATA_DIR, "vaccin_mock_data.json")
    if os.path.exists(vaccine_path):
        with open(vaccine_path, "r", encoding="utf-8") as f:
            VACCINES_DB = json.load(f)
            logger.info(f"Nạp thành công {len(VACCINES_DB)} bản ghi vaccine từ {vaccine_path}")
    else:
        logger.warning(f"Không tìm thấy tệp dữ liệu vaccine tại {vaccine_path}")
            
    # 2. Load combos
    combo_path = os.path.join(DATA_DIR, "combos", "combos.json")
    if os.path.exists(combo_path):
        with open(combo_path, "r", encoding="utf-8") as f:
            COMBOS_DB = json.load(f)
            combo_count = sum(len(g.get("packages", [])) for g in COMBOS_DB.get("combo_groups", []))
            logger.info(f"Nạp thành công {combo_count} gói vaccine từ {combo_path}")
    else:
        logger.warning(f"Không tìm thấy tệp dữ liệu combo tại {combo_path}")
            
    # 3. Load doctors
    doctor_path = os.path.join(DATA_DIR, "doctors", "doctors.json")
    if os.path.exists(doctor_path):
        with open(doctor_path, "r", encoding="utf-8") as f:
            DOCTORS_DB = json.load(f)
            logger.info(f"Nạp thành công {len(DOCTORS_DB)}  từ {doctor_path}")
    else:
        logger.warning(f"Không tìm thấy tệp dữ liệu  tại {doctor_path}")
            
    # 4. Load stores
    store_path = os.path.join(DATA_DIR, "stores", "stores.json")
    if os.path.exists(store_path):
        with open(store_path, "r", encoding="utf-8") as f:
            STORES_DB = json.load(f)
            logger.info(f"Nạp thành công {len(STORES_DB)} trung tâm tiêm chủng từ {store_path}")
    else:
        logger.warning(f"Không tìm thấy tệp dữ liệu trung tâm tiêm chủng tại {store_path}")

# Load databases immediately on module load
load_databases()

# Helper search functions (Tools)
# RAG Embeddings Cache
VACCINES_EMBEDDINGS = []
COMBOS_EMBEDDINGS = []
EMBEDDINGS_CACHE_FILE = os.path.join(DATA_DIR, "vaccine_embeddings_cache.json")

def load_embeddings_cache() -> bool:
    global VACCINES_EMBEDDINGS, COMBOS_EMBEDDINGS
    if not os.path.exists(EMBEDDINGS_CACHE_FILE):
        return False
    try:
        with open(EMBEDDINGS_CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
            
            # Reconstruct VACCINES_EMBEDDINGS
            VACCINES_EMBEDDINGS = []
            for item in cache.get("vaccines", []):
                vac = item["vac"]
                emb = item["emb"]
                VACCINES_EMBEDDINGS.append((vac, emb))
                
            # Reconstruct COMBOS_EMBEDDINGS
            COMBOS_EMBEDDINGS = []
            for item in cache.get("combos", []):
                pkg = item["pkg"]
                emb = item["emb"]
                COMBOS_EMBEDDINGS.append((pkg, emb))
                
            logger.info(f"Nạp thành công {len(VACCINES_EMBEDDINGS)} vaccine embeddings và {len(COMBOS_EMBEDDINGS)} combo embeddings từ bộ nhớ cache trên đĩa.")
            return True
    except Exception as e:
        logger.error(f"Lỗi khi đọc file cache embeddings: {e}")
    return False

def save_embeddings_cache():
    try:
        # Create mock_data dir if not exists
        os.makedirs(os.path.dirname(EMBEDDINGS_CACHE_FILE), exist_ok=True)
        cache = {
            "vaccines": [{"vac": vac, "emb": emb} for vac, emb in VACCINES_EMBEDDINGS],
            "combos": [{"pkg": pkg, "emb": emb} for pkg, emb in COMBOS_EMBEDDINGS]
        }
        with open(EMBEDDINGS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        logger.info(f"Đã lưu {len(VACCINES_EMBEDDINGS) + len(COMBOS_EMBEDDINGS)} embeddings vào file cache {EMBEDDINGS_CACHE_FILE}")
    except Exception as e:
        logger.error(f"Lỗi khi lưu file cache embeddings: {e}")

def get_embedding(text: str, api_key: str) -> List[float]:
    """
    Get embedding for a text string using OpenAI's SDK.
    """
    try:
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[text]
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
    return []

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_prod = sum(a * b for a, b in zip(v1, v2))
    mag1 = sum(a * a for a in v1) ** 0.5
    mag2 = sum(b * b for b in v2) ** 0.5
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_prod / (mag1 * mag2)

def compute_db_embeddings():
    global VACCINES_EMBEDDINGS, COMBOS_EMBEDDINGS
    
    # 1. Try to load from cache file first
    if load_embeddings_cache():
        return
        
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.info("Không tìm thấy OPENAI_API_KEY. Bỏ qua pre-computation của embeddings cho RAG.")
        return
        
    logger.info("Bắt đầu tính toán vector embeddings cho cơ sở dữ liệu vaccine (RAG)...")
    
    # Precompute for vaccines
    VACCINES_EMBEDDINGS = []
    for vac in VACCINES_DB:
        name = vac.get("name", "")
        prevention = vac.get("prevention", "")
        origin = vac.get("origin", "")
        phac_do = vac.get("sections", {}).get("Phác đồ lịch tiêm", "")
        
        doc_text = f"Vaccine: {name}. Phòng ngừa: {prevention}. Xuất xứ: {origin}. Lịch tiêm: {phac_do}."
        emb = get_embedding(doc_text, api_key)
        if emb:
            VACCINES_EMBEDDINGS.append((vac, emb))
            
    # Precompute for combos
    COMBOS_EMBEDDINGS = []
    packages_list = COMBOS_DB.get("combo_groups", [])
    for group in packages_list:
        for pkg in group.get("packages", []):
            title = pkg.get("title", "")
            doc_text = f"Gói vaccine / Combo: {title}."
            emb = get_embedding(doc_text, api_key)
            if emb:
                COMBOS_EMBEDDINGS.append((pkg, emb))
                
    logger.info(f"Tính toán xong embeddings cho {len(VACCINES_EMBEDDINGS)} vaccines và {len(COMBOS_EMBEDDINGS)} combos.")
    
    # 2. Save to cache file
    if VACCINES_EMBEDDINGS or COMBOS_EMBEDDINGS:
        save_embeddings_cache()

def search_vaccine_tool(search_term: str) -> Dict[str, Any]:
    """
    Search for vaccines and vaccine combos/packages in Long Chau DB using RAG (semantic embedding) if OpenAI is available.
    """
    search_term_lower = search_term.lower()
    
    # Default keyword search matches
    matched_vaccines = []
    matched_combos = []
    
    # 1. Try semantic search first if embeddings are available
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Lazy load embeddings if key exists but not computed yet
    global VACCINES_EMBEDDINGS, COMBOS_EMBEDDINGS
    if api_key and not VACCINES_EMBEDDINGS:
        compute_db_embeddings()
        
    if api_key and VACCINES_EMBEDDINGS:
        try:
            logger.info(f"Đang thực hiện Tìm kiếm Ngữ nghĩa RAG cho cụm từ: '{search_term}'")
            query_emb = get_embedding(search_term, api_key)
            if query_emb:
                # Rank vaccines
                vac_scores = []
                for vac, emb in VACCINES_EMBEDDINGS:
                    score = cosine_similarity(query_emb, emb)
                    
                    # Boost keyword matches slightly to keep exact matches on top
                    name_lower = vac.get("name", "").lower()
                    prevention_lower = vac.get("prevention", "").lower()
                    if search_term_lower in name_lower or search_term_lower in prevention_lower:
                        score += 0.15
                        
                    vac_scores.append((vac, score))
                
                # Sort by score descending and filter threshold
                vac_scores.sort(key=lambda x: x[1], reverse=True)
                for vac, score in vac_scores:
                    if score >= 0.35: # Threshold for semantic matching
                        matched_vaccines.append({
                            "name": vac.get("name"),
                            "prevention": vac.get("prevention"),
                            "price": vac.get("price"),
                            "origin": vac.get("origin"),
                            "unit": vac.get("unit"),
                            "image_url": vac.get("image_url"),
                            "detail_url": vac.get("detail_url"),
                            "phac_do": vac.get("sections", {}).get("Phác đồ lịch tiêm", ""),
                            "chong_chi_dinh": vac.get("sections", {}).get("Chống chỉ định", ""),
                            "luu_y_mang_thai": vac.get("sections", {}).get("Lưu ý với phụ nữ mang thai", "")
                        })
                
                # Rank combos
                combo_scores = []
                for pkg, emb in COMBOS_EMBEDDINGS:
                    score = cosine_similarity(query_emb, emb)
                    title_lower = pkg.get("title", "").lower()
                    if search_term_lower in title_lower:
                        score += 0.15
                    combo_scores.append((pkg, score))
                
                combo_scores.sort(key=lambda x: x[1], reverse=True)
                for pkg, score in combo_scores:
                    if score >= 0.35:
                        matched_combos.append({
                            "title": pkg.get("title"),
                            "total_price": pkg.get("total_price"),
                            "final_price": pkg.get("final_price"),
                            "discount_amount": pkg.get("discount_amount"),
                            "image_url": pkg.get("image_url"),
                            "detail_url": pkg.get("detail_url")
                        })
                        
                logger.info(f"Kết quả RAG: Tìm thấy {len(matched_vaccines)} vaccines và {len(matched_combos)} combos có độ khớp cao.")
                if matched_vaccines or matched_combos:
                    return {
                        "vaccines": matched_vaccines[:5],
                        "combos": matched_combos[:3]
                    }
        except Exception as rag_err:
            logger.error(f"Lỗi tìm kiếm ngữ nghĩa RAG: {rag_err}. Chuyển sang keyword search.")
            
    # --- FALLBACK KEYWORD SEARCH ---
    logger.info(f"Thực hiện Tìm kiếm Từ khóa (Keyword Match) cho cụm từ: '{search_term}'")
    # Split query into words and filter out common stop words to get search tokens
    stop_words = {"vaccine", "vắc", "xin", "cho", "bé", "trẻ", "em", "dành", "riêng", "tư", "vấn", "tìm", "loại", "người", "lớn", "phòng", "bệnh"}
    words = [w for w in re.split(r'\s+', search_term_lower) if w and w not in stop_words]
    
    # If all words were stop words, fall back to the original search term words
    if not words:
        words = [w for w in re.split(r'\s+', search_term_lower) if w]
        
    # Search in main vaccine database
    for vac in VACCINES_DB:
        name = vac.get("name", "").lower()
        prevention = vac.get("prevention", "").lower()
        
        is_match = False
        if search_term_lower in name or search_term_lower in prevention:
            is_match = True
        else:
            for word in words:
                if len(word) >= 2 and (word in name or word in prevention):
                    is_match = True
                    break
                    
        if is_match:
            matched_vaccines.append({
                "name": vac.get("name"),
                "prevention": vac.get("prevention"),
                "price": vac.get("price"),
                "origin": vac.get("origin"),
                "unit": vac.get("unit"),
                "image_url": vac.get("image_url"),
                "detail_url": vac.get("detail_url"),
                "phac_do": vac.get("sections", {}).get("Phác đồ lịch tiêm", ""),
                "chong_chi_dinh": vac.get("sections", {}).get("Chống chỉ định", ""),
                "luu_y_mang_thai": vac.get("sections", {}).get("Lưu ý với phụ nữ mang thai", "")
            })
            
    # Search in packages/combos
    packages_list = COMBOS_DB.get("combo_groups", [])
    for group in packages_list:
        for pkg in group.get("packages", []):
            title = pkg.get("title", "").lower()
            is_match = False
            if search_term_lower in title:
                is_match = True
            else:
                for word in words:
                    if len(word) >= 3 and word in title:
                        is_match = True
                        break
            if is_match:
                matched_combos.append({
                    "title": pkg.get("title"),
                    "total_price": pkg.get("total_price"),
                    "final_price": pkg.get("final_price"),
                    "discount_amount": pkg.get("discount_amount"),
                    "image_url": pkg.get("image_url"),
                    "detail_url": pkg.get("detail_url")
                })
                
    return {
        "vaccines": matched_vaccines[:5],
        "combos": matched_combos[:3]
    }

def search_stores_tool(province: str, search_term: str = "") -> List[Dict[str, Any]]:
    """
    Search for Long Chau vaccination centers.
    """
    province_lower = province.lower()
    search_term_lower = search_term.lower() if search_term else ""
    matched_stores = []
    
    for store in STORES_DB:
        store_prov = store.get("province", "")
        store_name = store.get("name", "")
        store_addr = store.get("address", "")
        store_ward = store.get("ward", "")
        
        is_prov_match = False
        if "hcm" in province_lower or "hồ chí minh" in province_lower or "thành phố hồ chí minh" in province_lower:
            is_prov_match = "hồ chí minh" in store_prov.lower() or "hcm" in store_prov.lower()
        elif "hà nội" in province_lower or "ha noi" in province_lower:
            is_prov_match = "hà nội" in store_prov.lower()
        else:
            is_prov_match = province_lower in store_prov.lower() or store_prov.lower() in province_lower
            
        if is_prov_match:
            if search_term_lower:
                alt_term = None
                match_q = re.match(r"(quận|q\.?)\s*(\d+|bình tân|bình thạnh|tân bình|tân phú|phú nhuận|gò vấp|thủ đức)", search_term_lower)
                if match_q:
                    q_num = match_q.group(2)
                    if match_q.group(1).startswith("quận"):
                        alt_term = f"q. {q_num}"
                    else:
                        alt_term = f"quận {q_num}"

                is_term_match = (
                    search_term_lower in store_name.lower() or 
                    search_term_lower in store_addr.lower() or 
                    search_term_lower in store_ward.lower()
                )
                if not is_term_match and alt_term:
                    is_term_match = (
                        alt_term in store_name.lower() or 
                        alt_term in store_addr.lower() or 
                        alt_term in store_ward.lower()
                    )
                if is_term_match:
                    matched_stores.append(store)
            else:
                matched_stores.append(store)
                
    result = []
    for store in matched_stores[:5]:
        result.append({
            "id": store.get("id"),
            "name": store.get("name"),
            "address": store.get("address"),
            "google_map_link": store.get("google_map_link"),
            "image_url": store.get("image_url"),
            "phone": store.get("phone", "18006928")
        })
    return result

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách giữa 2 điểm (lat1, lon1) và (lat2, lon2) trên Trái Đất (đơn vị: km)
    """
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def search_nearest_stores_by_coordinates_tool(latitude: float, longitude: float) -> List[Dict[str, Any]]:
    """
    Tìm kiếm danh sách 5 trung tâm tiêm chủng Long Châu gần tọa độ vị trí của khách hàng nhất.
    """
    valid_stores = []
    for store in STORES_DB:
        lat = store.get("latitude")
        lon = store.get("longitude")
        if lat is not None and lon is not None:
            try:
                dist = haversine(latitude, longitude, float(lat), float(lon))
                store_copy = store.copy()
                store_copy["distance"] = dist
                valid_stores.append(store_copy)
            except (ValueError, TypeError):
                continue
    
    valid_stores.sort(key=lambda x: x["distance"])
    
    result = []
    for store in valid_stores[:5]:
        result.append({
            "id": store.get("id"),
            "name": store.get("name"),
            "address": store.get("address"),
            "google_map_link": store.get("google_map_link") or f"https://www.google.com/maps/search/?api=1&query={store.get('latitude')},{store.get('longitude')}",
            "image_url": store.get("image_url"),
            "phone": store.get("phone", "18006928"),
            "distance": store.get("distance")
        })
    return result

def search_doctors_tool(specialty: str) -> List[Dict[str, Any]]:
    """
    Search for consulting doctors by specialty.
    """
    specialty_lower = specialty.lower()
    matched_doctors = []
    
    for doc in DOCTORS_DB:
        doc_spec = doc.get("specialization", "")
        if specialty_lower in doc_spec.lower():
            matched_doctors.append(doc)
            
    result = []
    for doc in matched_doctors[:3]:
        result.append({
            "id": doc.get("id"),
            "name": doc.get("name"),
            "specialization": doc.get("specialization"),
            "degree": doc.get("degree"),
            "position": doc.get("position"),
            "biography": doc.get("biography"),
            "avatar_url": doc.get("avatar_url")
        })
    return result

def book_appointment_tool(center_id: int, date: str, time: str, phone: str, name: str, vaccine_name: str = "") -> Dict[str, Any]:
    """
    Simulate booking an appointment for vaccination.
    """
    # Validate appointment date to prevent bookings in the past
    try:
        # Vietnam timezone (UTC+7)
        utc_now = datetime.now(timezone.utc)
        vn_tz = timezone(timedelta(hours=7))
        vn_now = utc_now.astimezone(vn_tz)
        current_date = vn_now.date()
    except Exception as e:
        logger.error(f"Error getting Vietnam local time: {e}")
        current_date = datetime.now().date()

    parsed_date = None
    date_str = date.strip()
    
    # Try common formats
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            break
        except ValueError:
            continue
            
    if parsed_date is None:
        # Fallback to regex numbers extraction DD/MM/YYYY
        match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            try:
                parsed_date = datetime(year, month, day).date()
            except ValueError:
                try:
                    parsed_date = datetime(year, day, month).date()
                except ValueError:
                    pass
        else:
            match_iso = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", date_str)
            if match_iso:
                year = int(match_iso.group(1))
                month = int(match_iso.group(2))
                day = int(match_iso.group(3))
                try:
                    parsed_date = datetime(year, month, day).date()
                except ValueError:
                    pass

    if parsed_date is not None:
        if parsed_date < current_date:
            return {
                "status": "error",
                "message": f"Ngày hẹn {date} là ngày trong quá khứ. Không thể đặt lịch hẹn trước ngày hiện tại ({current_date.strftime('%d/%m/%Y')})."
            }
    else:
        # If we cannot parse it, we should reject it to enforce proper formatting
        return {
            "status": "error",
            "message": f"Định dạng ngày '{date}' không hợp lệ. Vui lòng sử dụng định dạng DD/MM/YYYY (ví dụ: 15/06/2026) và đảm bảo không đặt lịch trước ngày hiện tại."
        }

    booking_code = f"LCB-{random.randint(100000, 999999)}"
    
    center_name = "Trung tâm Tiêm chủng FPT Long Châu"
    center_address = "Địa chỉ được chọn"
    for store in STORES_DB:
        if store.get("id") == center_id:
            center_name = store.get("name")
            center_address = store.get("address")
            break
            
    return {
        "status": "success",
        "booking_code": booking_code,
        "center_name": center_name,
        "center_address": center_address,
        "date": date,
        "time": time,
        "phone": phone,
        "name": name,
        "vaccine_name": vaccine_name or "Vaccine đã tư vấn",
        "sms_preview": f"[Tiêm chủng Long Châu] Xac nhan lich hen tiem vaccine {vaccine_name or 'da chon'} cho KH {name}. TG: {time} ngay {date} tai {center_name}. LH 18006928 de ho tro."
    }

# Mapping of tools
TOOLS_MAP = {
    "search_vaccine_tool": search_vaccine_tool,
    "search_stores_tool": search_stores_tool,
    "search_nearest_stores_by_coordinates_tool": search_nearest_stores_by_coordinates_tool,
    "search_doctors_tool": search_doctors_tool,
    "book_appointment_tool": book_appointment_tool
}

GEMINI_TOOLS_DECLARATIONS = [
    {
        "name": "search_vaccine_tool",
        "description": "Tìm kiếm thông tin chi tiết về các loại vaccine (giá, xuất xứ, phác đồ, chống chỉ định) hoặc các gói vaccine tại FPT Long Châu.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "search_term": {
                    "type": "STRING",
                    "description": "Tên vaccine hoặc tên bệnh phòng ngừa cần tìm (ví dụ: 'cúm', 'hpv', 'thủy đậu', '6 trong 1')."
                }
            },
            "required": ["search_term"]
        }
    },
    {
        "name": "search_stores_tool",
        "description": "Tìm kiếm danh sách trung tâm tiêm chủng Long Châu gần nhất theo tỉnh/thành phố và quận/huyện.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "province": {
                    "type": "STRING",
                    "description": "Tỉnh/thành phố (ví dụ: 'Hồ Chí Minh', 'Hà Nội')."
                },
                "search_term": {
                    "type": "STRING",
                    "description": "Quận/huyện cụ thể khách hàng nhập vào (ví dụ: 'Quận 7', 'Cầu Giấy')."
                }
            },
            "required": ["province"]
        }
    },
    {
        "name": "search_nearest_stores_by_coordinates_tool",
        "description": "Tìm kiếm danh sách 5 trung tâm tiêm chủng Long Châu gần nhất dựa trên tọa độ vĩ độ (latitude) và kinh độ (longitude) do người dùng cung cấp.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "latitude": {
                    "type": "NUMBER",
                    "description": "Vĩ độ của vị trí hiện tại (ví dụ: 10.756796)."
                },
                "longitude": {
                    "type": "NUMBER",
                    "description": "Kinh độ của vị trí hiện tại (ví dụ: 106.622597)."
                }
            },
            "required": ["latitude", "longitude"]
        }
    },
    {
        "name": "search_doctors_tool",
        "description": "Tìm kiếm danh sách các  tư vấn tiêm chủng theo chuyên khoa cụ thể (ví dụ: 'Nhi khoa', 'Sản khoa').",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "specialty": {
                    "type": "STRING",
                    "description": "Chuyên khoa  cần tìm (ví dụ: 'nhi khoa', 'sản khoa')."
                }
            },
            "required": ["specialty"]
        }
    },
    {
        "name": "book_appointment_tool",
        "description": "Đặt lịch hẹn tiêm chủng tại một trung tâm cụ thể với ngày, giờ, số điện thoại và tên của khách hàng.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "center_id": {
                    "type": "INTEGER",
                    "description": "Mã số ID của trung tâm Long Châu đã chọn."
                },
                "date": {
                    "type": "STRING",
                    "description": "Ngày tiêm chủng (định dạng DD/MM/YYYY). Bắt buộc phải là ngày hiện tại hoặc các ngày trong tương lai, không được chọn ngày trong quá khứ."
                },
                "time": {
                    "type": "STRING",
                    "description": "Khung giờ tiêm chủng (ví dụ: '09:00', '15:30')."
                },
                "phone": {
                    "type": "STRING",
                    "description": "Số điện thoại liên lạc."
                },
                "name": {
                    "type": "STRING",
                    "description": "Họ và tên của người tiêm chủng."
                },
                "vaccine_name": {
                    "type": "STRING",
                    "description": "Tên loại vaccine đăng ký tiêm chủng (không bắt buộc)."
                }
            },
            "required": ["center_id", "date", "time", "phone", "name"]
        }
    }
]

# ----------------- Safety Guardrails -----------------
def local_check_safety_guardrails(message: str) -> Dict[str, Any]:
    """
    Perform local quick regex check for key safety red flags.
    """
    msg = message.lower()
    
    # 1. High Fever / Acute Illness
    fever_patterns = [
        r"sốt\s*(cao|hơn|trên)?\s*(\d+[\.,]\d+|\d+)\s*(độ)?",
        r"co giật", r"khó thở", r"đang ốm", r"nhiễm trùng cấp", r"sốt sắng"
    ]
    for pattern in fever_patterns:
        match = re.search(pattern, msg)
        if match:
            if "sốt" in pattern:
                try:
                    temp_str = match.group(2).replace(",", ".")
                    temp = float(temp_str)
                    if temp < 38.5:
                        continue
                except ValueError:
                    pass
            return {
                "is_dangerous": True,
                "type": "fever",
                "warning_message": "CẢNH BÁO Y TẾ: Trẻ em hoặc người lớn đang có triệu chứng sốt cao hoặc biểu hiện ốm cấp tính KHÔNG ĐỦ ĐIỀU KIỆN TIÊM CHỦNG lúc này. Hãy hoãn tiêm cho tới khi hết sốt ít nhất 3 ngày và sức khỏe ổn định. Vui lòng liên hệ Hotline tư vấn khẩn cấp của  để được xử trí.",
                "actions": ["hotline", "callback"]
            }

    # 2. Pregnancy + Live Vaccines (Measles, Mumps, Rubella, Chickenpox/Varicella, Dengue)
    pregnancy_indicators = ["có bầu", "mang thai", "thai kỳ", "có thai", "nuôi em bé trong bụng", "chuẩn bị làm mẹ", "kế hoạch có con", "kế hoạch bầu", "thả bầu"]
    live_vaccine_keywords = ["sởi", "quai bị", "rubella", "thủy đậu", "barycela", "proquad", "qdenga", "sốt xuất huyết"]
    
    has_preg = any(x in msg for x in pregnancy_indicators)
    has_live_vac = any(x in msg for x in live_vaccine_keywords)
    
    if has_preg:
        if has_live_vac or "tư vấn" in msg or "tiêm" in msg:
            return {
                "is_dangerous": True,
                "type": "pregnancy_contraindication",
                "warning_message": "CẢNH BÁO Y TẾ: Phụ nữ mang thai CHỐNG CHỈ ĐỊNH hoàn toàn với các vắc-xin sống giảm độc lực (như Sởi - Quai bị - Rubella, Thủy đậu, Sốt xuất huyết). Tiêm các loại vắc-xin này trong thai kỳ có thể gây rủi ro nghiêm trọng cho thai nhi. Vui lòng liên hệ Hotline tư vấn  hoặc đăng ký gọi lại để nhận tư vấn chuyên sâu về các vaccine an toàn khi mang thai (như Uốn ván, Ho gà, Bạch hầu, Cúm).",
                "actions": ["hotline", "callback"]
            }

    # 3. Anaphylaxis history
    anaphylaxis_keywords = ["sốc phản vệ", "dị ứng nặng", "từng bị dị ứng vaccine", "phản vệ", "co giật sau tiêm", "dị ứng nghiêm trọng"]
    if any(x in msg for x in anaphylaxis_keywords):
        return {
            "is_dangerous": True,
            "type": "anaphylaxis",
            "warning_message": "CẢNH BÁO Y TẾ: Khách hàng có tiền sử sốc phản vệ hoặc phản ứng dị ứng nghiêm trọng sau khi tiêm vaccine cần được khám sàng lọc và thực hiện tiêm chủng tại bệnh viện hoặc cơ sở y tế chuyên khoa có đầy đủ trang thiết bị cấp cứu chống sốc, KHÔNG tự ý đăng ký tiêm chủng thông thường. Vui lòng liên hệ Hotline  khẩn cấp để được tư vấn lộ trình tiêm an toàn.",
            "actions": ["hotline", "callback"]
        }

    return {"is_dangerous": False}

def run_safety_guardrails(message: str, api_key: str = None) -> Dict[str, Any]:
    """
    Runs safety checks. Uses LLM semantic analysis first if API key is present.
    Falls back to local check if LLM fails or is not configured.
    """
    if api_key:
        logger.info(f"Khởi chạy phân tích an toàn ngữ nghĩa (Semantic Safety Guardrails) bằng LLM cho tin nhắn: '{message}'")
        try:
            is_openrouter = api_key.startswith("sk-or-")
            is_compatible = (api_key == os.getenv("COMPATIBLE_API_KEY")) if os.getenv("COMPATIBLE_API_KEY") else False
            is_openai = api_key.startswith("sk-") and not is_openrouter and not is_compatible
            
            prompt = f"""Bạn là một chuyên gia sàng lọc y khoa của Hệ thống Tiêm chủng FPT Long Châu.
Nhiệm vụ của bạn là phân tích tin nhắn của khách hàng dưới đây và xác định xem họ có đang khai báo các tình trạng CHỐNG CHỈ ĐỊNH hoặc NGUY HIỂM sau đây hay không:
1. Đang mang thai hoặc nghi ngờ có thai mà muốn tư vấn tiêm các loại vaccine sống giảm độc lực (như sởi, quai bị, rubella, thủy đậu, sốt xuất huyết) hoặc hỏi về vaccine nói chung nhưng có nguy cơ rủi ro.
2. Đang có triệu chứng cấp tính nghiêm trọng: Sốt cao (>38.5 độ C), co giật, khó thở, ốm nặng.
3. Có tiền sử dị ứng nghiêm trọng, sốc phản vệ ở các mũi tiêm trước.

Dưới đây là một số cách nói ẩn dụ/tử lóng bạn cần nhận biết:
- Có thai: "đang nuôi em bé trong bụng", "mang balo ngược", "có tin vui", "chuẩn bị làm mẹ", "đang bầu bí", "hai vạch", "ôm bụng bầu".

Lưu ý đặc biệt quan trọng: Nếu khách hàng phủ định tình trạng đó (ví dụ: "không sốt", "không có thai", "không bị dị ứng", "không sốc phản vệ", "không sao cả"), bạn phải xác định là AN TOÀN và đặt "is_dangerous" = false.

Hãy trả về kết quả định dạng JSON duy nhất như sau, không có markdown, không giải thích:
{{
  "is_dangerous": true/false,
  "type": "fever" hoặc "pregnancy_contraindication" hoặc "anaphylaxis" hoặc "none",
  "reason": "Giải thích ngắn gọn lý do bằng tiếng Việt nếu nguy hiểm",
  "warning_message": "Lời khuyên y tế ngắn gọn và cảnh báo cảnh giác cho khách hàng bằng tiếng Việt"
}}

Tin nhắn khách hàng: "{message}"
"""
            text_out = ""
            if is_openai:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    max_tokens=1024,
                    temperature=0.2
                )
                text_out = response.choices[0].message.content.strip()
            elif is_compatible:
                base_url = os.getenv("COMPATIBLE_BASE_URL", "http://localhost:8000/v1")
                model_name = os.getenv("COMPATIBLE_MODEL_NAME", "mimo-v2.5-pro")
                client = OpenAI(api_key=api_key, base_url=base_url)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    max_tokens=1024,
                    temperature=0.2
                )
                text_out = response.choices[0].message.content.strip()
            elif is_openrouter:
                client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
                response = client.chat.completions.create(
                    model="google/gemini-2.5-flash",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    max_tokens=1024,
                    temperature=0.2
                )
                text_out = response.choices[0].message.content.strip()
            else:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                text_out = response.text.strip()
            
            result = json.loads(text_out)
            logger.info(f"Kết quả phân tích an toàn ngữ nghĩa: is_dangerous={result.get('is_dangerous')}, type={result.get('type')}, reason='{result.get('reason')}'")
            
            if result.get("is_dangerous"):
                return {
                    "is_dangerous": True,
                    "type": result.get("type", "general"),
                    "warning_message": result.get("warning_message", "Cảnh báo y tế: Vui lòng tham khảo ý kiến  trước khi tiêm chủng."),
                    "actions": ["hotline", "callback"]
                }
            else:
                return {"is_dangerous": False}
        except Exception as e:
            logger.error(f"Lỗi xảy ra trong quá trình phân tích an toàn ngữ nghĩa: {e}", exc_info=True)
            
    # Fallback to local check
    local_check = local_check_safety_guardrails(message)
    if local_check["is_dangerous"]:
        logger.warning(f"Kích hoạt bộ lọc an toàn y khoa cục bộ (Local Guardrails) do fallback: loại={local_check['type']}, tin nhắn='{message}'")
        return local_check
        
    return {"is_dangerous": False}

# ----------------- Agent System Instruction Builder -----------------
def get_agent_system_instruction() -> str:
    # 1. Determine Operating System
    os_name = sys.platform
    if os_name == "win32":
        os_name = "windows"
    elif os_name == "darwin":
        os_name = "macOS"
    else:
        os_name = "linux"

    # 2. Get current time in Vietnam (UTC+7)
    utc_now = datetime.now(timezone.utc)
    vn_tz = timezone(timedelta(hours=7))
    vn_now = utc_now.astimezone(vn_tz)
    
    current_time_str = vn_now.strftime("%d/%m/%Y, %I:%M:%S %p")
    
    # Mapping English day of week to Vietnamese
    days_map = {
        "Monday": "Thứ Hai",
        "Tuesday": "Thứ Ba",
        "Wednesday": "Thứ Tư",
        "Thursday": "Thứ Năm",
        "Friday": "Thứ Sáu",
        "Saturday": "Thứ Bảy",
        "Sunday": "Chủ Nhật"
    }
    vn_day = days_map.get(vn_now.strftime("%A"), vn_now.strftime("%A"))
    
    # 3. Workspace path
    workspace_path = BASE_DIR

    return f"""Bạn là  Trợ lý AI tư vấn và Đặt lịch Tiêm chủng của Hệ thống Tiêm chủng FPT Long Châu.
Nhiệm vụ của bạn là hỗ trợ khách hàng tìm hiểu vaccine, tư vấn phác đồ tiêm chủng và hỗ trợ đặt lịch tiêm chủng dựa trên hồ sơ khách hàng.

Bạn PHẢI tuân thủ nghiêm ngặt quy trình tư vấn và các quy tắc ra quyết định sau (Flow Agent):

1. PHẢN HỒI BẰNG TIẾNG VIỆT:
- Luôn luôn giao tiếp và trả lời khách hàng bằng tiếng Việt một cách lịch sự, thân thiện và chuyên nghiệp.

2. YÊU CẦU LÀM RÕ THÔNG TIN & ĐIỀU KIỆN GỌI TOOL (CLARIFICATION & TOOL CONSTRAINTS):
- Trước khi gọi bất kỳ công cụ tìm kiếm vaccine nào (`search_vaccine_tool`), bạn PHẢI kiểm tra xem đã biết đối tượng tiêm là ai và độ tuổi/tháng tuổi của đối tượng đó chưa. Nếu chưa có thông tin cơ bản này, hãy lịch sự hỏi khách hàng trước, KHÔNG được gọi công cụ tìm kiếm một cách vô định.
- Trước khi gọi công cụ đặt lịch hẹn (`book_appointment_tool`), bạn PHẢI thu thập đầy đủ các thông tin bắt buộc sau từ khách hàng:
  - Họ và tên của người tiêm chủng.
  - Số điện thoại liên lạc hợp lệ.
  - Trung tâm tiêm chủng được chọn (`center_id` từ kết quả gọi `search_stores_tool`).
  - Ngày tiêm và Giờ tiêm mong muốn.
- Khi đặt lịch hẹn, bạn PHẢI kiểm tra ngày hẹn của khách hàng so với ngày hiện tại (được cung cấp ở phần Environment Context bên dưới). KHÔNG được đặt lịch hoặc gọi `book_appointment_tool` cho bất kỳ ngày nào trước ngày hiện tại (trong quá khứ). Nếu khách hàng yêu cầu một ngày trong quá khứ, hãy lịch sự thông báo rằng không thể đặt lịch hẹn trước ngày hiện tại và yêu cầu họ chọn ngày từ hôm nay trở đi.
- Nếu thiếu bất kỳ thông tin đặt lịch nào ở trên, bạn PHẢI dừng lại ngay lập tức và yêu cầu khách hàng cung cấp. Tuyệt đối KHÔNG được gọi `book_appointment_tool` khi thiếu tham số đầu vào.

3. QUY TRÌNH FLOW AGENT TỪNG BƯỚC (EXPECTED WORKFLOW):
- Bước 1: Chào hỏi khách hàng và thu thập thông tin hồ sơ (tuổi, thai kỳ, bệnh nền, dị ứng).
- Bước 2: Phân tích nhu cầu tiêm chủng y khoa dựa trên độ tuổi và thể trạng.
- Bước 3: Gọi `search_vaccine_tool` để truy xuất vaccine chính xác có sẵn trong cơ sở dữ liệu Long Châu. Tư vấn rõ tên vaccine, tác dụng phòng ngừa, giá cả, xuất xứ và phác đồ tiêm.
- Bước 4: Đề xuất đặt lịch và hỏi vị trí (Tỉnh/Thành, Quận/Huyện) của khách. Gọi `search_stores_tool` để tìm các trung tâm Long Châu phù hợp.
- Bước 5: Yêu cầu thông tin cá nhân (Họ tên + SĐT) và thực hiện gọi `book_appointment_tool` để xác nhận lịch hẹn.

4. CHỐNG CHỈ ĐỊNH VÀ AN TOÀN Y KHOA (GUARDRAILS):
- Nếu phát hiện khách hàng đang có tình trạng nguy hiểm/chống chỉ định nghiêm trọng (như có thai hỏi tiêm vaccine sống như sởi-quai bị-rubella/thủy đậu, hoặc sốt cao >38.5 độ C, tiền sử sốc phản vệ nặng), bạn PHẢI cảnh báo ngay lập tức, từ chối đề xuất các loại vaccine nguy hiểm đó và hướng dẫn họ liên hệ hotline hoặc khám trực tiếp tại bệnh viện.

5. TÍNH XÁC THỰC CỦA DỮ LIỆU (GROUNDING):
- Tuyệt đối KHÔNG tự bịa ra thông tin chi tiết vaccine, giá cả, phác đồ hay địa chỉ trung tâm, mã lịch hẹn. Mọi dữ liệu phải lấy trực tiếp từ kết quả trả về của các công cụ `search_vaccine_tool` và `search_stores_tool`.

Giao tiếp lịch sự, xưng hô 'em' hoặc 'Trợ lý Long Châu' và gọi khách hàng là 'Anh/chị' hoặc 'Quý khách'.

Environment Context:
OS: {os_name}
Date: {current_time_str} ({vn_day}, Giờ Việt Nam)
"""

def to_openai_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return schema
    new_schema = {}
    for k, v in schema.items():
        if k == "type" and isinstance(v, str):
            new_schema[k] = v.lower()
        elif isinstance(v, dict):
            new_schema[k] = to_openai_schema(v)
        elif isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, dict):
                    new_list.append(to_openai_schema(item))
                else:
                    new_list.append(item)
            new_schema[k] = new_list
        else:
            new_schema[k] = v
    return new_schema

def to_gemini_contents(messages: List[Dict[str, Any]]) -> List[types.Content]:
    contents = []
    for msg in messages:
        role = msg["role"]
        if role == "assistant":
            role = "model"
        
        if role == "tool":
            parts = [
                types.Part(
                    function_response=types.FunctionResponse(
                        name=msg.get("name"),
                        response={"result": json.loads(msg.get("content", "{}"))}
                    )
                )
            ]
            contents.append(types.Content(role="tool", parts=parts))
        else:
            parts = []
            if "tool_calls" in msg and msg["tool_calls"]:
                if msg.get("content"):
                    parts.append(types.Part.from_text(text=msg["content"]))
                for tc in msg["tool_calls"]:
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            name=tc["name"],
                            args=tc["args"]
                        )
                    ))
            else:
                text_val = msg.get("content") or msg.get("text", "")
                if text_val:
                    parts.append(types.Part.from_text(text=text_val))
            
            if parts:
                contents.append(types.Content(role=role, parts=parts))
    return contents

class LLMMessage:
    def __init__(self, content: Optional[str] = None, tool_calls: Optional[List[Dict[str, Any]]] = None):
        self.content = content
        self.tool_calls = tool_calls  # List of {"id": str, "name": str, "args": dict}

class LLMProvider(ABC):
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate_chat(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMMessage:
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        super().__init__(model_name, api_key or os.getenv("OPENAI_API_KEY") or "")
        self.client = OpenAI(api_key=self.api_key)

    def generate_chat(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMMessage:
        payload_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            payload_messages.append(msg)

        kwargs = {
            "model": self.model_name,
            "messages": payload_messages,
            "max_tokens": 2048,
            "temperature": 0.2
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        tool_calls = None
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": args
                })
        return LLMMessage(content=message.content, tool_calls=tool_calls)

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        payload_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            payload_messages.append(msg)

        kwargs = {
            "model": self.model_name,
            "messages": payload_messages,
            "max_tokens": 2048,
            "temperature": 0.2,
            "stream": True
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        
        tool_calls_delta = {}
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                yield {"type": "text", "content": delta.content}
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    index = tc_delta.index
                    if index not in tool_calls_delta:
                        tool_calls_delta[index] = {
                            "id": "",
                            "name": "",
                            "arguments": ""
                        }
                    if tc_delta.id:
                        tool_calls_delta[index]["id"] = tc_delta.id
                    if tc_delta.function and tc_delta.function.name:
                        tool_calls_delta[index]["name"] = tc_delta.function.name
                    if tc_delta.function and tc_delta.function.arguments:
                        tool_calls_delta[index]["arguments"] += tc_delta.function.arguments

        if tool_calls_delta:
            final_tool_calls = []
            for idx, tc in sorted(tool_calls_delta.items()):
                try:
                    args = json.loads(tc["arguments"])
                except Exception:
                    args = {}
                final_tool_calls.append({
                    "id": tc["id"],
                    "name": tc["name"],
                    "args": args
                })
            yield {"type": "tool_calls", "content": final_tool_calls}

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, model_name: str, base_url: str, api_key: Optional[str] = None):
        super().__init__(model_name, api_key or os.getenv("COMPATIBLE_API_KEY") or "")
        self.base_url = base_url
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate_chat(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMMessage:
        payload_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            payload_messages.append(msg)

        kwargs = {
            "model": self.model_name,
            "messages": payload_messages,
            "max_tokens": 2048,
            "temperature": 0.2
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        tool_calls = None
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": args
                })
        return LLMMessage(content=message.content, tool_calls=tool_calls)

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        payload_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            payload_messages.append(msg)

        kwargs = {
            "model": self.model_name,
            "messages": payload_messages,
            "max_tokens": 2048,
            "temperature": 0.2,
            "stream": True
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        
        tool_calls_delta = {}
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                yield {"type": "text", "content": delta.content}
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    index = tc_delta.index
                    if index not in tool_calls_delta:
                        tool_calls_delta[index] = {
                            "id": "",
                            "name": "",
                            "arguments": ""
                        }
                    if tc_delta.id:
                        tool_calls_delta[index]["id"] = tc_delta.id
                    if tc_delta.function and tc_delta.function.name:
                        tool_calls_delta[index]["name"] = tc_delta.function.name
                    if tc_delta.function and tc_delta.function.arguments:
                        tool_calls_delta[index]["arguments"] += tc_delta.function.arguments

        if tool_calls_delta:
            final_tool_calls = []
            for idx, tc in sorted(tool_calls_delta.items()):
                try:
                    args = json.loads(tc["arguments"])
                except Exception:
                    args = {}
                final_tool_calls.append({
                    "id": tc["id"],
                    "name": tc["name"],
                    "args": args
                })
            yield {"type": "tool_calls", "content": final_tool_calls}

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key or os.getenv("GEMINI_API_KEY") or "")
        self.client = genai.Client(api_key=self.api_key)

    def generate_chat(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMMessage:
        contents = to_gemini_contents(messages)
        
        gemini_tools = [{"function_declarations": tools}] if tools else None
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=gemini_tools,
            temperature=0.2
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )
        
        text_content = response.text
        
        tool_calls = []
        if response.function_calls:
            for fc in response.function_calls:
                args_dict = dict(fc.args) if fc.args else {}
                tool_calls.append({
                    "id": f"call_{uuid.uuid4().hex[:12]}",
                    "name": fc.name,
                    "args": args_dict
                })
        
        return LLMMessage(content=text_content or None, tool_calls=tool_calls if tool_calls else None)

    def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        contents = to_gemini_contents(messages)
        
        gemini_tools = [{"function_declarations": tools}] if tools else None
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=gemini_tools,
            temperature=0.2
        )
        
        response_stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=contents,
            config=config
        )
        
        tool_calls = []
        for chunk in response_stream:
            if chunk.text:
                yield {"type": "text", "content": chunk.text}
            if chunk.function_calls:
                for fc in chunk.function_calls:
                    args_dict = dict(fc.args) if fc.args else {}
                    tool_calls.append({
                        "id": f"call_{uuid.uuid4().hex[:12]}",
                        "name": fc.name,
                        "args": args_dict
                    })
        
        if tool_calls:
            yield {"type": "tool_calls", "content": tool_calls}

class VaccineAssistantAgent:
    def __init__(self, llm: LLMProvider, max_turns: int = 10):
        self.llm = llm
        self.max_turns = max_turns

    def run(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"Khởi chạy AI Agent Loop với {len(history)} tin nhắn. Model: {self.llm.model_name}")
        
        messages = []
        for msg in history:
            role = "user" if msg["from"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["text"]})

        system_instruction = get_agent_system_instruction()
        tool_data = {}

        if isinstance(self.llm, (OpenAIProvider, OpenAICompatibleProvider)):
            llm_tools = []
            for tool in GEMINI_TOOLS_DECLARATIONS:
                llm_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": to_openai_schema(tool["parameters"])
                    }
                })
        else:
            llm_tools = GEMINI_TOOLS_DECLARATIONS

        for turn in range(self.max_turns):
            logger.info(f"[Lượt {turn + 1}] Gửi yêu cầu tới model...")
            try:
                current_system_instruction = system_instruction
                active_messages = messages
                if turn == self.max_turns - 1:
                    current_system_instruction += "\n\n⚠️ QUAN TRỌNG: Đây là lượt phản hồi cuối cùng của bạn. Bạn PHẢI đưa ra câu trả lời trực tiếp bằng văn bản cho khách hàng ngay lập tức. KỂ CẢ CÓ ĐỦ THÔNG TIN HAY CHƯA, TUYỆT ĐỐI KHÔNG gọi thêm bất kỳ công cụ (tool call) nào nữa."
                    active_messages = messages.copy()
                    active_messages.append({
                        "role": "user",
                        "content": "[HỆ THỐNG] Đây là lượt phản hồi cuối cùng. Bạn hãy bỏ qua việc gọi tool, tổng hợp thông tin hiện có và phản hồi trực tiếp kết quả cuối cùng cho khách hàng ngay lập tức bằng văn bản (kể cả có đủ thông tin hay chưa)."
                    })

                response = self.llm.generate_chat(
                    messages=active_messages,
                    system_instruction=current_system_instruction,
                    tools=llm_tools
                )

                assistant_msg = {"role": "assistant"}
                if response.content is not None:
                    assistant_msg["content"] = response.content
                if response.tool_calls:
                    if isinstance(self.llm, (OpenAIProvider, OpenAICompatibleProvider)):
                        assistant_msg["tool_calls"] = [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["args"], ensure_ascii=False)
                                }
                            }
                            for tc in response.tool_calls
                        ]
                    else:
                        assistant_msg["tool_calls"] = response.tool_calls

                messages.append(assistant_msg)

                if not response.tool_calls:
                    logger.info(f"[Lượt {turn + 1}] Phản hồi cuối cùng nhận được (Không có tool call).")
                    return {
                        "text": response.content or "Dạ em đã ghi nhận thông tin.",
                        "tool_data": tool_data
                    }

                logger.info(f"[Lượt {turn + 1}] Nhận được yêu cầu gọi {len(response.tool_calls)} công cụ.")
                for tc in response.tool_calls:
                    tc_id = tc["id"]
                    fn_name = tc["name"]
                    fn_args = tc["args"]

                    logger.info(f"-> Đang thực thi công cụ '{fn_name}' với tham số: {fn_args}")

                    if fn_name in TOOLS_MAP:
                        try:
                            tool_result = TOOLS_MAP[fn_name](**fn_args)
                            
                            if fn_name == "search_vaccine_tool":
                                v_count = len(tool_result.get("vaccines", []))
                                c_count = len(tool_result.get("combos", []))
                                logger.info(f"<- Kết quả '{fn_name}': Tìm thấy {v_count} vaccine, {c_count} combos.")
                                tool_data["vaccines"] = tool_result.get("vaccines", [])
                                tool_data["combos"] = tool_result.get("combos", [])
                            elif fn_name in ["search_stores_tool", "search_nearest_stores_by_coordinates_tool"]:
                                logger.info(f"<- Kết quả '{fn_name}': Tìm thấy {len(tool_result)} chi nhánh.")
                                tool_data["stores"] = tool_result
                            elif fn_name == "search_doctors_tool":
                                logger.info(f"<- Kết quả '{fn_name}': Tìm thấy {len(tool_result)} .")
                                tool_data["doctors"] = tool_result
                            elif fn_name == "book_appointment_tool":
                                logger.info(f"<- Kết quả '{fn_name}': Đặt lịch thành công. Mã: {tool_result.get('booking_code')}")
                                tool_data["booking"] = tool_result

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc_id,
                                "name": fn_name,
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })
                        except Exception as err:
                            logger.error(f"Lỗi khi thực thi công cụ {fn_name}: {err}", exc_info=True)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc_id,
                                "name": fn_name,
                                "content": json.dumps({"error": str(err)})
                            })
            except Exception as e:
                logger.error(f"Lỗi agent loop: {e}", exc_info=True)
                return {
                    "text": f"Dạ, trợ lý Long Châu gặp chút sự cố kết nối AI ({str(e)}). Em xin phép hỗ trợ tư vấn trực tiếp cho mình ạ.",
                    "tool_data": {}
                }

        return {
            "text": messages[-1].get("content") or "Dạ em đã ghi nhận thông tin. Anh/chị cần tư vấn thêm gì nữa không ạ?",
            "tool_data": tool_data
        }

    def run_stream(self, history: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
        logger.info(f"Khởi chạy AI Agent Stream Loop với {len(history)} tin nhắn. Model: {self.llm.model_name}")
        
        messages = []
        for msg in history:
            role = "user" if msg["from"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["text"]})

        system_instruction = get_agent_system_instruction()
        tool_data = {}

        if isinstance(self.llm, (OpenAIProvider, OpenAICompatibleProvider)):
            llm_tools = []
            for tool in GEMINI_TOOLS_DECLARATIONS:
                llm_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": to_openai_schema(tool["parameters"])
                    }
                })
        else:
            llm_tools = GEMINI_TOOLS_DECLARATIONS

        for turn in range(self.max_turns):
            logger.info(f"[Lượt {turn + 1}] Gửi yêu cầu stream tới model...")
            try:
                current_system_instruction = system_instruction
                active_messages = messages
                if turn == self.max_turns - 1:
                    current_system_instruction += "\n\n⚠️ QUAN TRỌNG: Đây là lượt phản hồi cuối cùng của bạn. Bạn PHẢI đưa ra câu trả lời trực tiếp bằng văn bản cho khách hàng ngay lập tức. KỂ CẢ CÓ ĐỦ THÔNG TIN HAY CHƯA, TUYỆT ĐỐI KHÔNG gọi thêm bất kỳ công cụ (tool call) nào nữa."
                    active_messages = messages.copy()
                    active_messages.append({
                        "role": "user",
                        "content": "[HỆ THỐNG] Đây là lượt phản hồi cuối cùng. Bạn hãy bỏ qua việc gọi tool, tổng hợp thông tin hiện có và phản hồi trực tiếp kết quả cuối cùng cho khách hàng ngay lập tức bằng văn bản (kể cả có đủ thông tin hay chưa)."
                    })

                stream = self.llm.stream_chat(
                    messages=active_messages,
                    system_instruction=current_system_instruction,
                    tools=llm_tools
                )
                
                current_text = ""
                current_tool_calls = None
                
                for chunk in stream:
                    if chunk["type"] == "text":
                        current_text += chunk["content"]
                        yield {"type": "text", "content": chunk["content"]}
                    elif chunk["type"] == "tool_calls":
                        current_tool_calls = chunk["content"]
                
                assistant_msg = {"role": "assistant"}
                if current_text:
                    assistant_msg["content"] = current_text
                if current_tool_calls:
                    if isinstance(self.llm, (OpenAIProvider, OpenAICompatibleProvider)):
                        assistant_msg["tool_calls"] = [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["args"], ensure_ascii=False)
                                }
                            }
                            for tc in current_tool_calls
                        ]
                    else:
                        assistant_msg["tool_calls"] = current_tool_calls
                
                messages.append(assistant_msg)
                
                if not current_tool_calls:
                    logger.info(f"[Lượt {turn + 1}] Phản hồi stream hoàn thành (Không có tool call).")
                    return
                    
                logger.info(f"[Lượt {turn + 1}] Nhận được yêu cầu gọi {len(current_tool_calls)} công cụ.")
                for tc in current_tool_calls:
                    tc_id = tc["id"]
                    fn_name = tc["name"]
                    fn_args = tc["args"]
                    
                    logger.info(f"-> Đang thực thi công cụ '{fn_name}' với tham số: {fn_args}")
                    
                    if fn_name in TOOLS_MAP:
                        try:
                            tool_result = TOOLS_MAP[fn_name](**fn_args)
                            
                            if fn_name == "search_vaccine_tool":
                                tool_data["vaccines"] = tool_result.get("vaccines", [])
                                tool_data["combos"] = tool_result.get("combos", [])
                            elif fn_name in ["search_stores_tool", "search_nearest_stores_by_coordinates_tool"]:
                                tool_data["stores"] = tool_result
                            elif fn_name == "search_doctors_tool":
                                tool_data["doctors"] = tool_result
                            elif fn_name == "book_appointment_tool":
                                tool_data["booking"] = tool_result
                                
                            yield {"type": "tool_data", "content": tool_data}
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc_id,
                                "name": fn_name,
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })
                        except Exception as err:
                            logger.error(f"Lỗi khi thực thi công cụ {fn_name}: {err}", exc_info=True)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc_id,
                                "name": fn_name,
                                "content": json.dumps({"error": str(err)})
                            })
            except Exception as e:
                logger.error(f"Lỗi agent stream loop: {e}", exc_info=True)
                yield {
                    "type": "text",
                    "content": f"Dạ, trợ lý Long Châu gặp chút sự cố kết nối AI ({str(e)}). Em xin phép hỗ trợ tư vấn trực tiếp cho mình ạ."
                }
                return

# ----------------- Backward-Compatible Wrapper Agent Loops -----------------

def execute_openai_agent(history: List[Dict[str, Any]], api_key: str) -> Dict[str, Any]:
    """
    Run GPT-4o-mini LLM via OpenAI API using official OpenAI SDK.
    """
    provider = OpenAIProvider(
        model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        api_key=api_key
    )
    agent = VaccineAssistantAgent(llm=provider)
    return agent.run(history)

def execute_openai_compatible_agent(
    history: List[Dict[str, Any]], 
    api_key: str, 
    base_url: str, 
    model_name: str
) -> Dict[str, Any]:
    """
    Run any OpenAI-compatible LLM using official OpenAI SDK.
    """
    provider = OpenAICompatibleProvider(
        model_name=model_name,
        base_url=base_url,
        api_key=api_key
    )
    agent = VaccineAssistantAgent(llm=provider)
    return agent.run(history)

def execute_openrouter_agent(history: List[Dict[str, Any]], api_key: str) -> Dict[str, Any]:
    """
    Run LLM via OpenRouter API using OpenAI-compatible tools and function calling.
    """
    provider = OpenAICompatibleProvider(
        model_name=os.getenv("OPENROUTER_MODEL_NAME", "google/gemini-2.5-flash"),
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    agent = VaccineAssistantAgent(llm=provider)
    return agent.run(history)

def execute_gemini_agent(history: List[Dict[str, Any]], api_key: str) -> Dict[str, Any]:
    """
    Run Gemini LLM using direct HTTP API or route to OpenRouter.
    """
    if api_key.startswith("sk-or-"):
        return execute_openrouter_agent(history, api_key)
    provider = GeminiProvider(
        model_name="gemini-2.5-flash",
        api_key=api_key
    )
    agent = VaccineAssistantAgent(llm=provider)
    return agent.run(history)

# ----------------- Mock Fallback Agent -----------------
def execute_mock_agent(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Rule-based mock agent simulation that executes the 4 paths perfectly based on input.
    """
    # Dynamically compute tomorrow's date for mock bookings to ensure they are always in the future.
    try:
        # Vietnam timezone (UTC+7)
        utc_now = datetime.now(timezone.utc)
        vn_tz = timezone(timedelta(hours=7))
        vn_now = utc_now.astimezone(vn_tz)
        mock_date_dt = vn_now + timedelta(days=1)
        mock_date_str = mock_date_dt.strftime("%d/%m/%Y")
    except Exception:
        mock_date_str = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    if not history:
        return {
            "text": "Chào mừng Anh/Chị đến với Tiêm chủng Long Châu. Em có thể hỗ trợ gì cho mình ạ?",
            "tool_data": {}
        }
        
    last_msg = history[-1]["text"]
    msg_lower = last_msg.lower()
    
    # Check if coords are provided in msg
    coord_match = re.search(r"vĩ độ:?\s*([\d\.-]+),\s*kinh độ:?\s*([\d\.-]+)", msg_lower)
    if coord_match:
        try:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            stores = search_nearest_stores_by_coordinates_tool(lat, lon)
            return {
                "text": "Dạ em đã tìm thấy các trung tâm tiêm chủng Long Châu gần vị trí tọa độ của Anh/Chị nhất. Vui lòng chọn chi nhánh thuận tiện bên dưới để chuẩn bị đặt lịch nhé ạ:",
                "tool_data": {
                    "stores": stores
                }
            }
        except Exception as e:
            logger.error(f"Error parsing mock agent coordinates: {e}")
            
    # 1. Check for Low Confidence Path (Complex Medical Query)
    low_conf_keywords = ["viêm da cơ địa", "uống thuốc trị mụn", "đang điều trị thuốc", "được không ", "bệnh hiếm", "bị thận"]
    if any(k in msg_lower for k in low_conf_keywords):
        doctors = search_doctors_tool("Nhi khoa")
        return {
            "text": "Câu hỏi chuyên sâu y khoa về việc tiêm vaccine khi đang điều trị bệnh lý/uống thuốc cần được  chuyên khoa Nhi/Sản sàng lọc lâm sàng trực tiếp. Để đảm bảo an toàn tuyệt đối, trợ lý Long Châu xin phép chuyển thông tin của mình cho  Trực hotline gọi lại tư vấn chi tiết cho mình trong 10-15 phút tới. Anh/chị vui lòng đăng ký số điện thoại và tên qua biểu mẫu dưới đây nhé.",
            "tool_data": {
                "doctors": doctors,
                "callback_form": True
            }
        }
        
    # 2. Check for Correction Path during booking
    has_seen_stores = False
    has_seen_booking = False
    for h in history:
        t = h["text"].lower()
        if "trung tâm" in t or "chi nhánh" in t or "quận 7" in t or "quận 1" in t:
            has_seen_stores = True
        if "số điện thoại" in t or "lịch hẹn" in t or "gửi sms" in t:
            has_seen_booking = True
            
    if has_seen_stores and not has_seen_booking:
        location_change = None
        if "quận 1" in msg_lower or "q1" in msg_lower or "quan 1" in msg_lower:
            location_change = "Quận 1"
        elif "thủ đức" in msg_lower or "thu duc" in msg_lower:
            location_change = "Thủ Đức"
            
        if location_change:
            stores = search_stores_tool("Hồ Chí Minh", location_change)
            return {
                "text": f"Dạ em đã cập nhật vị trí sang {location_change}. Dưới đây là các Trung tâm Tiêm chủng Long Châu gần nhất tại {location_change} để anh/chị chọn ạ:",
                "tool_data": {
                    "stores": stores
                }
            }

    if has_seen_booking:
        time_change = None
        if "3h chiều" in msg_lower or "15:00" in msg_lower or "15h" in msg_lower:
            time_change = "15:00"
        elif "10h sáng" in msg_lower or "10:00" in msg_lower or "10h" in msg_lower:
            time_change = "10:00"
            
        if time_change:
            booking = book_appointment_tool(2040, mock_date_str, time_change, "0987654321", "Tuấn Anh", "Vắc xin Vaxigrip Tetra (Cúm)")
            return {
                "text": f"Dạ em đã điều chỉnh giờ hẹn sang {time_change} chiều ngày {mock_date_str}. Lịch hẹn mới đã được cập nhật thành công!",
                "tool_data": {
                    "booking": booking
                }
            }

    # 3. Happy Path Chat Flow
    if any(k in msg_lower for k in ["cúm", "influvac", "vaxigrip", "cho con", "cho bé", "trẻ em"]):
        vac_info = search_vaccine_tool("cúm")
        return {
            "text": "Dạ vắc-xin cúm cho bé từ 6 tháng tuổi trở lên hiện Long Châu có sẵn đầy đủ dòng cao cấp của Pháp (Vaxigrip Tetra) và Hà Lan (Influvac Tetra) giúp phòng ngừa 4 chủng virus cúm nguy hiểm.\n\nAnh/chị vui lòng cho em biết bé nhà mình được mấy tháng tuổi và sức khỏe hiện tại thế nào để em kiểm tra phác đồ mũi tiêm cho bé ạ?",
            "tool_data": {
                "vaccines": vac_info.get("vaccines", [])
            }
        }
        
    age_match = re.search(r"(\d+)\s*(tháng|tuổi)", msg_lower)
    if age_match or "1 tuổi" in msg_lower or "khỏe mạnh" in msg_lower or "bé bình thường" in msg_lower:
        return {
            "text": "Dạ tuyệt vời ạ! Bé 12 tháng tuổi khỏe mạnh sẽ có phác đồ tiêm vaccine cúm như sau:\n• Mũi 1: Tiêm lần đầu.\n• Mũi 2: Sau mũi một ít nhất 1 tháng.\n• Mũi nhắc: Tiêm nhắc lại 1 mũi hàng năm để duy trì kháng thể bảo vệ bé trước các chủng cúm biến đổi mới.\n\nChi phí vaccine cúm Vaxigrip Tetra (Pháp) là 320.571đ/mũi. Để đăng ký giữ vaccine và đặt lịch hẹn tiêm cho bé, Anh/chị cho em xin Tỉnh/Thành phố hoặc Quận/Huyện mình đang ở để em tìm trung tâm gần nhất còn thuốc nhé ạ?",
            "tool_data": {}
        }
        
    location = None
    if "quận 7" in msg_lower or "q7" in msg_lower or "quan 7" in msg_lower:
        location = "Quận 7"
    elif "hà nội" in msg_lower or "ha noi" in msg_lower:
        location = "Hà Nội"
    elif "hồ chí minh" in msg_lower or "hcm" in msg_lower:
        location = "Hồ Chí Minh"
        
    if location:
        stores = search_stores_tool("Hồ Chí Minh", location)
        return {
            "text": f"Dạ, tại khu vực {location}, Long Châu có các trung tâm tiêm chủng khang trang, luôn sẵn thuốc và phòng khám sàng lọc riêng. Dưới đây là các chi nhánh gần mình nhất. Anh/chị vui lòng chọn chi nhánh phù hợp bên dưới nha:",
            "tool_data": {
                "stores": stores
            }
        }
        
    phone_match = re.search(r"(0\d{9})", msg_lower)
    if phone_match or "đặt lịch" in msg_lower or "hẹn tiêm" in msg_lower or "nhập sđt" in msg_lower:
        booking = book_appointment_tool(2040, mock_date_str, "09:00", "0987654321", "Tuấn Anh", "Vắc xin Vaxigrip Tetra (Cúm)")
        return {
            "text": f"Dạ vâng ạ! Trợ lý Long Châu đã lên lịch hẹn tiêm chủng thành công cho mình vào ngày {mock_date_str}. Thông tin đặt lịch chi tiết được tóm tắt bên dưới. Hệ thống cũng đã gửi một tin nhắn SMS xác nhận kèm mã lịch hẹn về số điện thoại của mình ạ. Chúc bé và gia đình nhiều sức khỏe!",
            "tool_data": {
                "booking": booking
            }
        }
        
    return {
        "text": "Dạ em luôn sẵn sàng hỗ trợ tư vấn vaccine, phác đồ tiêm chủng hoặc đăng ký lịch hẹn tiêm tại FPT Long Châu. Anh/chị quan tâm đến vắc-xin cho bé hay người lớn, hoặc cần tìm chi nhánh gần mình ạ?",
        "tool_data": {}
    }
