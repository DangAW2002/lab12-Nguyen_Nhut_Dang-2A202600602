import requests
import json
import os
import sys
import io

# Đảm bảo console Windows in tiếng Việt UTF-8 không lỗi
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def api_scrape_combos():
    # Lấy thư mục chứa script (combos/scripts/main/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Lấy thư mục cha của thư mục cha (combos/)
    workspace_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    output_file = os.path.join(workspace_dir, "combos.json")
    
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Endpoint 1: Lấy danh sách gói vắc-xin kèm giá tiền, chiết khấu, commitments
    url_combos = "https://api.tiemchunglongchau.com.vn/gw/v1/public/vac-web-bff-before-order/product/combos"
    
    print("Đang gửi yêu cầu lấy danh sách gói vắc-xin từ API...")
    try:
        res = requests.get(url_combos, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"Lỗi: API combos trả về mã lỗi HTTP {res.status_code}")
            return False
            
        data = res.json()
        if 'data' not in data:
            print("Lỗi: Cấu trúc response API combos không hợp lệ")
            return False
            
        data_content = data['data']
        combos_list = data_content.get("combos", [])
        commitments = data_content.get("commitments", [])
        detail = data_content.get("detail", [])
        note = data_content.get("note", [])
        
        # Đếm tổng số gói vắc-xin
        total_packages = sum(len(group.get("items", [])) for group in combos_list)
        print(f"Đã nhận phản hồi combos thành công! Tìm thấy {len(combos_list)} nhóm gói, tổng số {total_packages} gói vắc-xin.")
        
        # Cấu trúc lại dữ liệu đầu ra sạch hơn
        formatted_combos = []
        for group in combos_list:
            group_title = group.get("title") or ""
            group_items = []
            
            for item in group.get("items", []):
                # Định dạng số tiền thành chuỗi tiền tệ dễ đọc
                total_amount = item.get("totalAmount")
                final_amount = item.get("finalAmount")
                discount = item.get("discount")
                
                total_str = f"{int(total_amount):,}đ".replace(",", ".") if total_amount else "Liên hệ"
                final_str = f"{int(final_amount):,}đ".replace(",", ".") if final_amount else "Liên hệ"
                discount_str = f"{int(discount):,}đ".replace(",", ".") if discount else "0đ"
                
                group_items.append({
                    "id": item.get("id"),
                    "title": item.get("title", "").strip(),
                    "sku": item.get("sku", "").strip(),
                    "slug": item.get("slug", "").strip(),
                    "combo_id": item.get("comboId", "").strip(),
                    "total_price": total_str,
                    "final_price": final_str,
                    "discount_amount": discount_str,
                    "image_url": item.get("image", {}).get("src", ""),
                    "detail_url": f"https://tiemchunglongchau.com.vn/vacxin/{item.get('slug')}" if item.get('slug') else ""
                })
                
            formatted_combos.append({
                "group_title": group_title,
                "packages": group_items
            })
            
        # Định dạng chi tiết các nhóm vắc-xin gợi ý
        formatted_detail = []
        for category in detail:
            cat_name = category.get("categoryDisplayName") or category.get("categoryTitle") or ""
            doc_id = category.get("categoryDocumentId") or ""
            
            vaccines = []
            for vac in category.get("vaccines", []):
                current_price = vac.get("currentPrice")
                original_price = vac.get("originalPrice")
                
                price_str = f"{int(current_price):,}đ".replace(",", ".") if current_price else "Liên hệ"
                orig_price_str = f"{int(original_price):,}đ".replace(",", ".") if original_price else "Liên hệ"
                
                vaccines.append({
                    "name": vac.get("name", "").strip(),
                    "sku": vac.get("sku", "").strip(),
                    "origin": vac.get("national", "").strip(),
                    "price": price_str,
                    "original_price": orig_price_str,
                    "slug": vac.get("slug", "").strip(),
                    "image_url": vac.get("image", {}).get("src", "")
                })
                
            formatted_detail.append({
                "category_name": cat_name.strip(),
                "category_id": doc_id,
                "vaccines": list({v['sku']: v for v in vaccines}.values()) # Loại trùng lặp theo SKU nếu có
            })
            
        # Định dạng cam kết dịch vụ
        formatted_commitments = []
        for com in commitments:
            formatted_commitments.append({
                "name": com.get("name", "").strip(),
                "description": com.get("description", "").strip(),
                "icon_url": com.get("icon", {}).get("src", "")
            })
            
        # Tạo cấu trúc lưu trữ cuối cùng
        output_data = {
            "combo_groups": formatted_combos,
            "vaccine_categories_detail": formatted_detail,
            "commitments": formatted_commitments,
            "notes": [n.get("children", [{}])[0].get("text", "") for n in note if n.get("children")]
        }
        
        # Đảm bảo tạo thư mục cha nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        print(f"Đã trích xuất thành công dữ liệu gói vắc-xin và lưu vào {output_file}")
        return True
        
    except Exception as e:
        print(f"Đã xảy ra lỗi khi cào dữ liệu gói vắc-xin: {e}")
        return False

if __name__ == "__main__":
    api_scrape_combos()
