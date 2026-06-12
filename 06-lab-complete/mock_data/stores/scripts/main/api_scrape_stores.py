import requests
import json
import os
import sys
import io

# Đảm bảo console Windows in tiếng Việt UTF-8 không lỗi
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def api_scrape_stores():
    # Lấy thư mục chứa script (stores/scripts/main/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Lấy thư mục cha của thư mục cha (stores/)
    workspace_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    output_file = os.path.join(workspace_dir, "stores.json")
    
    url = "https://api.tiemchunglongchau.com.vn/gw/v1/public/vac-web-bff-before-order/store/search-stores?numberPerPage=1000&page=1"
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Đang gửi yêu cầu lấy danh sách trung tâm tiêm chủng tới API...")
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"Lỗi: API trả về mã lỗi HTTP {res.status_code}")
            return False
            
        response_data = res.json()
        if 'data' not in response_data or 'items' not in response_data['data']:
            print("Lỗi: Cấu trúc response API không hợp lệ")
            return False
            
        items = response_data['data']['items']
        total_records = response_data['data'].get('totalRecords', len(items))
        print(f"Đã nhận phản hồi thành công! Tổng số trung tâm từ API: {total_records}. Lấy về: {len(items)}")
        
        parsed_stores = []
        for item in items:
            store_id = item.get("id")
            name = item.get("displayName") or item.get("name") or ""
            name = name.strip()
            
            address = item.get("address") or ""
            address = address.strip()
            
            regulated_address = item.get("regulatedAddress") or ""
            regulated_address = regulated_address.strip()
            
            latitude = item.get("latitude")
            longitude = item.get("longitude")
            google_link = item.get("googleLink") or ""
            
            province = item.get("regulatedProvinceName") or ""
            province = province.strip()
            
            district = item.get("regulatedDistrictName") or ""
            district = district.strip()
            
            ward = item.get("regulatedWardName") or ""
            ward = ward.strip()
            
            phone = item.get("phone") or ""
            phone = phone.strip()
            
            # Lấy thông tin thời gian mở cửa
            schedule_times = item.get("scheduleTimes") or []
            schedules = []
            for s in schedule_times:
                schedules.append({
                    "open_time": s.get("openTime"),
                    "close_time": s.get("closeTime"),
                    "display_text": s.get("displayText") or ""
                })
                
            # Lấy link ảnh đại diện
            image_url = ""
            primary_image = item.get("primaryImage")
            if primary_image and isinstance(primary_image, dict):
                image_url = primary_image.get("src") or ""
                
            parsed_stores.append({
                "id": store_id,
                "name": name,
                "address": address,
                "regulated_address": regulated_address,
                "province": province,
                "district": district,
                "ward": ward,
                "latitude": latitude,
                "longitude": longitude,
                "google_map_link": google_link,
                "phone": phone,
                "opening_hours": schedules,
                "image_url": image_url
            })
            
        # Ghi ra file JSON
        # Đảm bảo tạo thư mục cha nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parsed_stores, f, indent=2, ensure_ascii=False)
            
        print(f"Đã trích xuất thành công {len(parsed_stores)} trung tâm và lưu vào {output_file}")
        return True
        
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi API hoặc phân tích dữ liệu: {e}")
        return False

if __name__ == "__main__":
    api_scrape_stores()
