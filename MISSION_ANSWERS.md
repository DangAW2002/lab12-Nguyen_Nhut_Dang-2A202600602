# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcoded secrets:** `OPENAI_API_KEY` và `DATABASE_URL` bị viết cứng trong code. Nếu đẩy code lên GitHub, các thông tin nhạy cảm này sẽ bị lộ.
2. **Không có cấu hình tập trung (Config management):** Các biến cấu hình như `DEBUG`, `MAX_TOKENS` bị gán cứng thay vì đọc từ biến môi trường (environment variables).
3. **Sử dụng print thay vì logging chuẩn:** Sử dụng hàm `print()` cho debug, nguy hiểm hơn là log cả secrets (`OPENAI_API_KEY`) ra console.
4. **Thiếu endpoint kiểm tra sức khỏe (Health checks):** Không có route `/health` hay `/ready` để nền tảng cloud biết khi nào ứng dụng bị crash để tự động restart.
5. **Cấu hình host/port cứng và bật reload:** `host="localhost"` khiến app chỉ nhận kết nối nội bộ (không nhận được kết nối từ container/internet), `port=8000` bị cố định (trong khi cloud tự inject cổng qua biến `PORT`), và bật `reload=True` trong môi trường sản xuất làm giảm hiệu năng.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| **Config**  | Viết cứng trong file `app.py` | Sử dụng biến môi trường (env vars) thông qua class `Settings` và `.env` | Bảo mật bí mật (secrets), linh hoạt thay đổi cấu hình giữa các môi trường khác nhau mà không cần thay đổi mã nguồn. |
| **Health Check** | Không hỗ trợ | Có endpoint `/health` (liveness probe) và `/ready` (readiness probe) | Giúp nền tảng triển khai giám sát tình trạng ứng dụng, tự động restart khi lỗi và chỉ chuyển traffic khi ứng dụng sẵn sàng. |
| **Logging** | Dùng hàm `print()`, in cả secret | Dùng structured JSON logging qua module `logging` chuẩn, không in secret | Dễ dàng parse, lọc và phân tích log tự động bằng các công cụ gom log tập trung (Datadog, Kibana, Loki). |
| **Shutdown** | Tắt đột ngột | Xử lý tín hiệu `SIGTERM`, trì hoãn để hoàn tất request dở dang (Graceful) | Tránh làm gián đoạn request của khách hàng đang xử lý nửa chừng, tránh làm mất dữ liệu và đóng kết nối sạch sẽ. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image là gì?**
   - Base image là `python:3.11`. Đây là phiên bản Debian đầy đủ của Python (full Python distribution) chứa rất nhiều build tools (gcc, make...) nên dung lượng rất lớn (~1 GB).
2. **Working directory là gì?**
   - Working directory là `/app`. Đây là thư mục gốc trong container nơi các câu lệnh tiếp theo (`COPY`, `RUN`, `CMD`) được thực thi.
3. **Tại sao COPY requirements.txt trước?**
   - Để tận dụng cơ chế **Docker Layer Caching**. Docker lưu lại cache của mỗi lớp (layer). Nếu file `requirements.txt` không đổi ở lần build sau, Docker sẽ bỏ qua bước chạy `pip install` (vốn tốn nhiều thời gian tải thư viện) giúp tốc độ build nhanh hơn nhiều.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - Cả hai đều dùng để định nghĩa câu lệnh mặc định khi container chạy. Tuy nhiên:
     - `ENTRYPOINT` định nghĩa câu lệnh chính cố định của container (ví dụ: `python`), khó bị ghi đè khi chạy lệnh `docker run`. Các tham số truyền vào lúc chạy container sẽ được ghép tiếp vào sau.
     - `CMD` định nghĩa câu lệnh mặc định hoặc tham số cho `ENTRYPOINT`. Lệnh trong `CMD` sẽ bị ghi đè hoàn toàn nếu người dùng truyền câu lệnh khác khi chạy `docker run`.

### Exercise 2.3: Image size comparison
- **Develop (Basic):** 1.66 GB (1660 MB)
- **Production (Advanced):** 236 MB
- **Difference:** Giảm khoảng **85.78%** dung lượng.
- **Giải thích:**
  1. **Base image tối ưu:** Develop sử dụng `python:3.11` (full Debian, chứa nhiều build tools, dev libraries nặng) trong khi Production sử dụng `python:3.11-slim` (chỉ chứa runtime tối giản cần thiết để chạy Python).
  2. **Multi-stage Build:** Stage 1 (builder) thực hiện compile các thư viện và tải dependencies. Stage 2 (runtime) chỉ copy thư mục package đã cài đặt hoàn tất, loại bỏ hoàn toàn các build tools cồng kềnh như `gcc`, `make`, `apt-get` cache và mã nguồn trung gian không cần thiết.

### Exercise 2.3: Multi-stage build questions
- **Stage 1 (Builder):** Sử dụng `python:3.11-slim` làm môi trường để cài đặt các build dependencies cần thiết (như `gcc`, `libpq-dev`), sao chép `requirements.txt` và cài đặt dependencies vào thư mục người dùng (`/root/.local`).
- **Stage 2 (Runtime):** Khởi tạo một image sạch từ `python:3.11-slim`, tạo non-root user `appuser` để tăng tính bảo mật, chỉ copy thư mục python packages đã được build/compile từ Stage 1 sang (`/home/appuser/.local`), copy mã nguồn ứng dụng và cấu hình port/health check/CMD khởi chạy.

### Exercise 2.4: Docker Compose stack
- **Các service được khởi tạo:**
  1. **agent:** Ứng dụng FastAPI AI Agent chứa code chính.
  2. **redis:** Cơ sở dữ liệu in-memory dùng để quản lý session, lưu cache lịch sử hội thoại và quản lý rate limiting.
  3. **qdrant:** Vector Database dùng để lưu trữ và tìm kiếm vector embeddings phục vụ tính năng RAG.
  4. **nginx:** Reverse proxy và Load balancer, đóng vai trò là cổng đón tiếp traffic duy nhất từ bên ngoài (cổng 80/443), phân tán các request đến các replica của `agent`.
- **Cách thức giao tiếp:**
  - Các service nằm chung trong một mạng ảo bridge nội bộ cô lập tên là `internal`.
  - Chúng giao tiếp với nhau bằng tên service (ví dụ: `agent` gọi Redis qua URL `redis://redis:6379`, gọi Qdrant qua URL `http://qdrant:6333`).
  - Các service `agent`, `redis`, `qdrant` không mở port trực tiếp ra máy host (không thể gọi trực tiếp từ bên ngoài). Chỉ có `nginx` expose port 80/443 ra ngoài để nhận request từ Client và định tuyến nội bộ.
- **Sơ đồ kiến trúc:**
```
Client --[Port 80/443]--> Nginx (LB/Proxy)
                            | (Internal Bridge Network)
                            ├--> Agent (Replica 1) ---> Redis & Qdrant
                            └--> Agent (Replica 2) ---> Redis & Qdrant
```

## Part 3: Cloud Deployment

### Exercise 3.1: Render/Railway deployment
- **Public URL:** [Sẽ điền sau khi hoàn thành deployment ở Part 6]
- **Platform:** Render / Railway

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results

**1. Test API Key Authentication (develop version):**
- **Không gửi API Key:** Trả về `401 Unauthorized`
  ```json
  {"detail":"Missing API key. Include header: X-API-Key: <your-key>"}
  ```
- **Gửi sai API Key:** Trả về `403 Forbidden`
  ```json
  {"detail":"Invalid API key."}
  ```
- **Gửi đúng API Key:** Trả về `200 OK` và response của mock LLM.
  ```json
  {"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}
  ```

**2. Test JWT Authentication & Rate Limiting (production version):**
- Gửi yêu cầu lấy token thành công cho user `student`:
  ```json
  {"access_token":"eyJhbGciOiJIUzI1Ni...","token_type":"bearer","expires_in_minutes":60}
  ```
- Gọi liên tiếp 12 request với token của user (limit = 10 req/min):
  - Request 1-10: Trả về thành công `200 OK` (giảm dần số request còn lại từ 9 về 0).
  - Request 11 & 12: Bị block và trả về lỗi `429 Too Many Requests`:
    ```json
    {"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}}
    ```

### Exercise 4.4: Cost guard implementation
- **Cách thức hoạt động:**
  1. **Token Cost Configuration:** Định nghĩa giá cho mỗi 1000 input/output tokens (dựa trên giá GPT-4o-mini là $0.15/1M input và $0.60/1M output).
  2. **Daily Budget Check:** Trước mỗi lần gọi LLM, server gọi `check_budget(user_id)`. Nó sẽ truy xuất bản ghi sử dụng của ngày hôm đó từ in-memory record (hoặc Redis trong prod). Nếu chi phí tích lũy của user đã chạm hoặc vượt quá `$1.00`, hệ thống ném ra lỗi `402 Payment Required` để chặn request.
  3. **Global Budget Check:** Đồng thời, hệ thống kiểm tra chi phí tích lũy của toàn hệ thống trong ngày. Nếu vượt quá `$10.00`, hệ thống ném ra lỗi `503 Service Unavailable` để dừng dịch vụ tạm thời nhằm tránh phát sinh chi phí ngoài ý muốn.
  4. **Usage Recording:** Sau mỗi lần LLM trả lời, hàm `record_usage(...)` được gọi để tính toán chi phí thực tế dựa trên số token đã dùng, cộng dồn vào tổng chi phí của user và hệ thống, và ghi log lại.

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

- **Health Checks (Exercise 5.1):**
  - **Liveness Probe (`/health`):** Kiểm tra tiến trình ứng dụng có phản hồi bình thường không và giám sát dung lượng RAM còn lại (sử dụng thư viện `psutil`). Nếu RAM > 90% hoặc gặp lỗi khác, nó sẽ chuyển sang trạng thái `degraded` để hệ thống tự động khởi động lại.
  - **Readiness Probe (`/ready`):** Kiểm tra xem kết nối tới Redis/Database phụ thuộc có thông suốt không trước khi cho phép load balancer route traffic vào container.
- **Graceful Shutdown (Exercise 5.2):**
  - Sử dụng tham số `timeout_graceful_shutdown=30` trong uvicorn và lắng nghe tín hiệu hệ thống `SIGTERM`, `SIGINT`.
  - Khi có tín hiệu tắt container, biến trạng thái `_is_ready` chuyển thành `False` để chặn các request mới ở Readiness Probe.
  - Sử dụng một HTTP middleware đếm số request đang xử lý dở dang (`_in_flight_requests`). Tiến trình shutdown sẽ đợi cho đến khi đếm này về `0` hoặc hết timeout 30 giây rồi mới giải phóng tài nguyên kết nối và tắt hẳn process.
- **Stateless Design & Load Balancing (Exercise 5.3 - 5.5):**
  - **Lưu trữ State:** Lịch sử trò chuyện (`history`) và session được tách khỏi RAM của server và lưu trữ tập trung vào cơ sở dữ liệu in-memory Redis.
  - **Kết quả kiểm thử:**
    - Chúng tôi đã scale hệ thống lên 3 replica agents cùng Nginx Load Balancer và 1 Redis.
    - Chạy file `test_stateless.py` gửi 5 request liên tiếp.
    - Kết quả cho thấy các request lần lượt được xử lý bởi các instance khác nhau (`instance-7def4e`, `instance-c82747`, `instance-143484`) do Nginx round-robin.
    - Mặc dù đi qua các instance khác nhau, lịch sử chat (10 messages) vẫn hoàn toàn đầy đủ và liên tục vì được đồng bộ chung qua Redis.
    - **Kết quả chạy script test thực tế:**
      ```
      ============================================================
      Stateless Scaling Demo
      ============================================================

      Session ID: 367f0da3-6a49-4f6c-b1ae-9558b20eb19e

      Request 1: [instance-7def4e]
        Q: What is Docker?
        A: Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!...

      Request 2: [instance-c82747]
        Q: Why do we need containers?
        A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ O...

      Request 3: [instance-143484]
        Q: What is Kubernetes?
        A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ O...

      Request 4: [instance-7def4e]
        Q: How does load balancing work?
        A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ O...

      Request 5: [instance-c82747]
        Q: What is Redis used for?
        A: Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé....

      ------------------------------------------------------------
      Total requests: 5
      Instances used: {'instance-143484', 'instance-c82747', 'instance-7def4e'}
      ✅ All requests served despite different instances!

      --- Conversation History ---
      Total messages: 10
        [user]: What is Docker?...
        [assistant]: Container là cách đóng gói app để chạy ở mọi nơi. Build once...
        ...
      ✅ Session history preserved across all instances via Redis!
      ```
