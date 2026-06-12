import requests
import json
import os
import sys
import io

# Đảm bảo console Windows in tiếng Việt UTF-8 không lỗi
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_rich_text(blocks):
    if not blocks:
        return ""
    if isinstance(blocks, str):
        return blocks.strip()
    if not isinstance(blocks, list):
        return str(blocks)
        
    paragraphs = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        children = block.get("children", [])
        block_text = ""
        for child in children:
            if not isinstance(child, dict):
                continue
            child_type = child.get("type", "text")
            if child_type == "text":
                txt = child.get("text", "")
                if child.get("bold"):
                    txt = f"**{txt}**"
                if child.get("italic"):
                    txt = f"*{txt}*"
                block_text += txt
            elif child_type == "link":
                link_children = child.get("children", [])
                link_txt = "".join(c.get("text", "") for c in link_children if isinstance(c, dict))
                url = child.get("url", "")
                if url:
                    block_text += f"[{link_txt}]({url})"
                else:
                    block_text += link_txt
        paragraphs.append(block_text.strip())
    return "\n\n".join(p for p in paragraphs if p)

def api_scrape_doctors():
    # Lấy thư mục chứa script (doctors/scripts/main/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Lấy thư mục cha của thư mục cha (doctors/)
    workspace_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    output_file = os.path.join(workspace_dir, "doctors.json")
    
    url = "https://api.tiemchunglongchau.com.vn/gw/v1/public/vac-web-bff-before-order/doctors?size=200&page=1"
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Đang gửi yêu cầu lấy danh sách   chuyên khoa tới API...")
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
        print(f"Đã nhận phản hồi thành công! Tổng số   từ API: {total_records}. Lấy về: {len(items)}")
        
        parsed_doctors = []
        for item in items:
            doc_id = item.get("id")
            name = item.get("name", "").strip()
            specialize = item.get("specialize", "").strip()
            slug = item.get("slug", "").strip()
            degree = item.get("degree", "").strip()
            position = item.get("position", "").strip()
            
            experience_raw = item.get("experience")
            experience = parse_rich_text(experience_raw)
            
            biography_raw = item.get("biography")
            biography = parse_rich_text(biography_raw)
            
            # Lấy thông tin avatar
            avatar_url = ""
            avatar_obj = item.get("avatar")
            if avatar_obj and isinstance(avatar_obj, dict):
                avatar_url = avatar_obj.get("src") or ""
                
            parsed_doctors.append({
                "id": doc_id,
                "name": name,
                "specialization": specialize,
                "degree": degree,
                "position": position,
                "biography": biography,
                "experience": experience,
                "avatar_url": avatar_url,
                "profile_slug": slug,
                "profile_url": f"https://tiemchunglongchau.com.vn/bac-si/{slug}" if slug else ""
            })
            
        # Ghi ra file JSON
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parsed_doctors, f, indent=2, ensure_ascii=False)
            
        print(f"Đã trích xuất thành công {len(parsed_doctors)}   và lưu vào {output_file}")
        return True
        
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi API hoặc phân tích dữ liệu  : {e}")
        return False

if __name__ == "__main__":
    api_scrape_doctors()
