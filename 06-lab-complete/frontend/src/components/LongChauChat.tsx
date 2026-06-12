import { useEffect, useMemo, useRef, useState } from "react";
import {
  Search,
  ChevronDown,
  Send,
  Paperclip,
  X,
  Phone,
  ShoppingCart,
  Syringe,
  ShieldCheck,
  MapPin,
  Calendar,
  Clock,
  User,
  AlertTriangle,
  CheckCircle2,
  Maximize2,
  Minimize2,
  Info,
} from "lucide-react";
import heroBg from "@/assets/longchau-hero.jpg";
import healthtechChatAvatar from "@/assets/healthtech-chat-avatar.png";
import { ChatLauncher } from "@/components/healthtech";

export interface Vaccine {
  name: string;
  prevention: string;
  price: string | number;
  origin: string;
  unit: string;
  image_url: string;
  detail_url: string;
  phac_do?: string;
  chong_chi_dinh?: string;
  luu_y_mang_thai?: string;
}

export interface Combo {
  title: string;
  total_price: string | number;
  final_price: string | number;
  discount_amount: string | number;
  image_url: string;
  detail_url: string;
}

export interface Store {
  id: number;
  name: string;
  address: string;
  google_map_link: string;
  image_url: string;
  phone: string;
  distance?: number;
}

export interface Doctor {
  id: number;
  name: string;
  specialization: string;
  degree: string;
  position: string;
  biography: string;
  avatar_url: string;
}

export interface Booking {
  status: string;
  booking_code: string;
  center_name: string;
  center_address: string;
  date: string;
  time: string;
  phone: string;
  name: string;
  vaccine_name: string;
  sms_preview: string;
}

type Msg = {
  id: number;
  from: "bot" | "user";
  text: string;
  quickReplies?: string[];
  toolData?: {
    vaccines?: Vaccine[];
    combos?: Combo[];
    stores?: Store[];
    doctors?: Doctor[];
    booking?: Booking;
    callback_form?: boolean;
    safety_escalation?: boolean;
  };
  safetyTriggered?: boolean;
  isStreaming?: boolean;
};

const NAV = [
  "Vắc xin phòng bệnh",
  "Gói vắc xin",
  "Khuyến mãi 🔥",
  "Hệ thống tiêm chủng",
  "Tôi nên tiêm gì",
  "Đội ngũ chuyên môn",
  "Kiến thức tiêm chủng",
];

const COMMITMENTS = [
  {
    name: "Miễn phí nhắc lịch hẹn",
    description: "Chính xác và khoa học cho cả gia đình",
    icon_url: "https://cdn.tiemchunglongchau.com.vn/unsafe/Icon_combo_1_4c45b4fc06.png"
  },
  {
    name: "Cam kết giữ giá vắc xin",
    description: "Suốt thời gian tiêm theo phác đồ",
    icon_url: "https://cdn.tiemchunglongchau.com.vn/unsafe/Icon_combo_2_cab7fce76a.png"
  },
  {
    name: "Cam kết luôn đủ vắc xin",
    description: "Không lo hàng khan hiếm",
    icon_url: "https://cdn.tiemchunglongchau.com.vn/unsafe/Icon_combo_3_aa9373ad3e.png"
  }
];

const AGE_PACKAGES = [
  {
    id: 5425,
    title: "GÓI COMBO 6 THÁNG",
    sku: "00042221",
    total_price: "15.023.800đ",
    final_price: "14.305.110đ",
    discount_amount: "718.689đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/minh_hoa_goi_VECTOR_e6af7e1c7f.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-vac-xin-combo-6-thang"
  },
  {
    id: 7181,
    title: "GÓI COMBO 12 THÁNG",
    sku: "00042222",
    total_price: "29.272.100đ",
    final_price: "28.164.820đ",
    discount_amount: "1.107.279đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/Illus_Goi_blue_2_10add6a475.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-vac-xin-combo-12-thang"
  },
  {
    id: 6801,
    title: "GÓI COMBO 24 THÁNG",
    sku: "00042223",
    total_price: "30.314.900đ",
    final_price: "29.029.929đ",
    discount_amount: "1.284.970đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/Illus_Goi_blue_8a16579a53.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-vac-xin-combo-24-thang"
  },
  {
    id: 6963,
    title: "GÓI TRẺ TIỀN HỌC ĐƯỜNG (TỪ 3 TUỔI - 9 TUỔI)",
    sku: "00042224",
    total_price: "19.154.300đ",
    final_price: "18.246.310đ",
    discount_amount: "907.990đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/Illus_Goi_blue_1_e4effbd2a2.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-tre-tien-hoc-duong-tu-3-tuoi-9-tuoi"
  },
  {
    id: 9744,
    title: "GÓI THANH THIẾU NIÊN (TỪ 9 TUỔI - 18 TUỔI)",
    sku: "00042217",
    total_price: "29.208.300đ",
    final_price: "28.026.109đ",
    discount_amount: "1.182.190đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/Illus_Goi_blue_3_ad13668bfe.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-thanh-thieu-nien-tu-9-tuoi-18-tuoi"
  },
  {
    id: 8499,
    title: "GÓI CHO NGƯỜI TRƯỞNG THÀNH",
    sku: "00042219",
    total_price: "26.238.300đ",
    final_price: "25.137.110đ",
    discount_amount: "1.101.189đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/Illus_Goi_blue_4_3111f89e24.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-vac-xin-cho-nguoi-truong-thanh"
  }
];

const TARGET_PACKAGES = [
  {
    id: 9196,
    title: "GÓI TIỀN HÔN NHÂN TOÀN DIỆN 7 LOẠI",
    sku: "00044085",
    total_price: "18.818.800đ",
    final_price: "18.205.560đ",
    discount_amount: "613.240đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/Illus_Goi_blue_1_5eeb7f570b.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-tien-hon-nhan-toan-dien-7-loai"
  },
  {
    id: 8343,
    title: "GÓI PHỤ NỮ TRƯỚC KHI MANG THAI",
    sku: "00042218",
    total_price: "6.509.800đ",
    final_price: "6.332.260đ",
    discount_amount: "177.540đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/Illus_02e6955310.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-phu-nu-truoc-khi-mang-thai"
  },
  {
    id: 3563,
    title: "GÓI NGƯỜI CÓ BỆNH MÃN TÍNH",
    sku: "00042220",
    total_price: "16.547.300đ",
    final_price: "15.555.210đ",
    discount_amount: "992.089đ",
    image_url: "https://cdn.tiemchunglongchau.com.vn/Illus_Goi_blue_2_0121d2fee9.png",
    detail_url: "https://tiemchunglongchau.com.vn/vacxin/goi-nguoi-co-benh-man-tinh"
  }
];

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export function LongChauChat() {
  const [chatOpen, setChatOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");

  const packagesRef = useRef<HTMLDivElement>(null);
  const handleScrollToPackages = () => {
    packagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  const [typing, setTyping] = useState(false);
  const [locating, setLocating] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Determine which message's card data is active in the right details panel
  const activeMessage = useMemo(() => {
    if (selectedMessageId !== null) {
      return messages.find((m) => m.id === selectedMessageId && m.toolData && !m.isStreaming) || null;
    }
    // Default to the latest message that contains toolData
    const hasTool = messages
      .slice()
      .reverse()
      .find((m) => m.toolData && !m.isStreaming);
    return hasTool || null;
  }, [messages, selectedMessageId]);

  const activeMessageId = activeMessage?.id ?? null;

  // Compute styling classes dynamically for smooth transition
  const containerClasses = useMemo(() => {
    let base =
      "fixed z-50 transition-all duration-500 ease-in-out flex flex-col overflow-hidden bg-white shadow-2xl ring-1 ring-black/10";

    if (chatOpen) {
      base += " opacity-100 scale-100 pointer-events-auto";
    } else {
      base += " opacity-0 scale-95 pointer-events-none";
    }

    if (isExpanded) {
      base +=
        " bottom-0 right-0 w-full h-full rounded-none translate-x-0 translate-y-0 sm:bottom-1/2 sm:right-1/2 sm:translate-x-1/2 sm:translate-y-1/2 sm:w-[95vw] sm:max-w-6xl sm:h-[90vh] sm:rounded-3xl delay-0";
    } else {
      base +=
        " bottom-0 right-0 w-full h-full max-w-full rounded-none sm:bottom-4 sm:right-4 sm:w-[420px] sm:max-w-[95vw] sm:h-[680px] sm:rounded-2xl delay-150";
      if (!chatOpen) {
        base += " translate-y-4";
      } else {
        base += " translate-y-0";
      }
    }

    return base;
  }, [chatOpen, isExpanded]);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      alert("Trình duyệt của bạn không hỗ trợ Geolocation (Định vị).");
      return;
    }

    setLocating(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        setLocating(false);
        handleSend(
          `Tôi muốn tìm trung tâm tiêm chủng gần tọa độ vĩ độ: ${lat.toFixed(6)}, kinh độ: ${lon.toFixed(6)}`,
        );
      },
      (error) => {
        setLocating(false);
        let errorMsg = "Không thể lấy vị trí hiện tại của bạn.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMsg =
              "Quyền truy cập vị trí bị từ chối. Vui lòng cấp quyền trong cài đặt trình duyệt hoặc nhập thủ công Tỉnh/Thành phố hoặc Quận/Huyện của bạn.";
            break;
          case error.POSITION_UNAVAILABLE:
            errorMsg = "Thông tin tọa độ vị trí hiện tại không khả dụng.";
            break;
          case error.TIMEOUT:
            errorMsg = "Yêu cầu định vị vị trí đã hết thời gian chờ.";
            break;
        }
        alert(errorMsg);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    );
  };
  const idRef = useRef(0);
  const today = useMemo(() => new Date(), []);
  const timeLabel = `${today.getHours().toString().padStart(2, "0")}:${today
    .getMinutes()
    .toString()
    .padStart(2, "0")}`;

  // Helper to append message
  const push = (m: Omit<Msg, "id">) => {
    idRef.current += 1;
    const newMsg = { ...m, id: idRef.current };
    setMessages((p) => [...p, newMsg]);
    return newMsg;
  };

  // Fetch initial welcome message from API or set default
  useEffect(() => {
    const initChat = async () => {
      setTyping(true);
      try {
        const response = await fetch(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: [] }),
        });
        if (!response.ok) {
          throw new Error("API failed");
        }

        idRef.current += 1;
        const botMsgId = idRef.current;
        const botMsgPlaceholder: Msg = {
          id: botMsgId,
          from: "bot",
          text: "",
          isStreaming: true,
          quickReplies: [
            "Tư vấn vắc-xin cúm cho con",
            "Bé sốt 39.2 độ muốn tiêm cúm",
            "Viêm da cơ địa có tiêm được không",
            "Địa chỉ trung tâm Quận 7",
          ],
        };
        setMessages([botMsgPlaceholder]);

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No reader");

        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let accumulatedText = "";
        let accumulatedToolData: Msg["toolData"] = {};

        setTyping(false);

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              const trimmed = line.trim();
              if (!trimmed) continue;
              try {
                const chunk = JSON.parse(trimmed);
                if (chunk.type === "text") {
                  accumulatedText += chunk.content;
                  setMessages((prev) =>
                    prev.map((m) => (m.id === botMsgId ? { ...m, text: accumulatedText } : m)),
                  );
                } else if (chunk.type === "tool_data") {
                  accumulatedToolData = { ...accumulatedToolData, ...chunk.content };
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === botMsgId ? { ...m, toolData: accumulatedToolData } : m,
                    ),
                  );
                }
              } catch (e) {
                console.warn("Init chat stream parse error:", e);
              }
            }
          }
        } finally {
          setMessages((prev) =>
            prev.map((m) => (m.id === botMsgId ? { ...m, isStreaming: false } : m)),
          );
        }
      } catch (err) {
        // Fallback static greeting if backend is temporarily starting up
        setMessages([
          {
            id: 1,
            from: "bot",
            text: "Chào mừng Anh/Chị đến với Tiêm chủng Long Châu.  Long Châu có thể giúp gì cho mình ạ?",
            quickReplies: [
              "Tư vấn vắc-xin cúm cho con",
              "Bé sốt 39.2 độ muốn tiêm cúm",
              "Viêm da cơ địa có tiêm được không",
              "Địa chỉ trung tâm Quận 7",
            ],
          },
        ]);
        idRef.current = 1;
        setTyping(false);
      }
    };
    initChat();
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;

      // Secondary scroll to handle delayed card expansions and image rendering
      const timer = setTimeout(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messages, typing, chatOpen]);

  const handleSend = async (raw?: string) => {
    const text = (raw ?? input).trim();
    if (!text) return;

    // Add user message to UI immediately
    push({ from: "user", text });
    setInput("");
    setTyping(true);
    setSelectedMessageId(null); // Reset detail panel selection to follow the latest bot answer

    // Push a temporary empty bot message so we can update it as stream comes in
    idRef.current += 1;
    const botMsgId = idRef.current;
    const botMsgPlaceholder: Msg = {
      id: botMsgId,
      from: "bot",
      text: "",
      isStreaming: true,
    };
    setMessages((p) => [...p, botMsgPlaceholder]);

    try {
      // Map current UI messages to format expected by backend
      const historyPayload = messages.map((m) => ({
        from: m.from,
        text: m.text,
      }));
      // Append the new user message
      historyPayload.push({ from: "user", text });

      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: historyPayload }),
      });

      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body reader available.");
      }

      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let accumulatedText = "";
      let accumulatedToolData: Msg["toolData"] = {};
      let safetyTriggered = false;

      // We turn off the typing state once we start receiving chunks
      let startedReceiving = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        if (!startedReceiving) {
          startedReceiving = true;
          setTyping(false);
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          try {
            const chunk = JSON.parse(trimmed);
            if (chunk.type === "text") {
              accumulatedText += chunk.content;
              setMessages((prev) =>
                prev.map((m) => (m.id === botMsgId ? { ...m, text: accumulatedText } : m)),
              );
            } else if (chunk.type === "tool_data") {
              accumulatedToolData = { ...accumulatedToolData, ...chunk.content };
              setMessages((prev) =>
                prev.map((m) => (m.id === botMsgId ? { ...m, toolData: accumulatedToolData } : m)),
              );
            } else if (chunk.type === "safety_triggered") {
              safetyTriggered = chunk.content;
              accumulatedText = chunk.text || accumulatedText;
              accumulatedToolData = chunk.tool_data || accumulatedToolData;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === botMsgId
                    ? {
                        ...m,
                        text: accumulatedText,
                        toolData: accumulatedToolData,
                        safetyTriggered: safetyTriggered,
                      }
                    : m,
                ),
              );
            }
          } catch (e) {
            console.warn("Failed to parse stream line:", trimmed, e);
          }
        }
      }
    } catch (error) {
      console.error("Failed to connect to chat API:", error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === botMsgId
            ? {
                ...m,
                text: "Dạ, máy chủ tư vấn của Long Châu đang bận. Anh/chị vui lòng thử lại sau hoặc gọi điện trực tiếp đến Hotline 1800 6928 để gặp  tư vấn ạ.",
              }
            : m,
        ),
      );
    } finally {
      setTyping(false);
      setMessages((prev) =>
        prev.map((m) => (m.id === botMsgId ? { ...m, isStreaming: false } : m)),
      );
    }
  };

  const handleCallbackSubmit = async (name: string, phone: string, details: string) => {
    try {
      await fetch(`${API_BASE}/callback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, phone, details }),
      });
    } catch (err) {
      console.error("Callback API error:", err);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--stage)] flex flex-col font-sans">
      {/* Sticky Header wrapper */}
      <div className="sticky top-0 z-30 shadow-md bg-white shrink-0">
        <TopBar />
        <NavBar onPackagesClick={handleScrollToPackages} />
      </div>

      {/* Hero */}
      <main className="flex-1 px-4 py-4 lg:px-8 flex justify-center items-center">
        <div
          className="relative w-full h-[640px] max-w-[1400px] overflow-hidden rounded-3xl shadow-xl transition-all duration-300"
          style={{
            backgroundImage: `linear-gradient(180deg, rgba(170,235,235,0.0) 0%, rgba(170,235,235,0.2) 60%, rgba(170,235,235,0) 100%), url(${heroBg})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        >
          {/* Brand lockup overlay */}
          <div className="absolute left-12 top-12 hidden lg:flex items-center gap-3 text-[var(--brand-deep)]">
            <div className="grid h-12 w-12 place-items-center rounded-md bg-white shadow-sm">
              <BrandMark className="h-8 w-8" />
            </div>
            <div className="leading-tight">
              <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--brand)]">
                FPT Retail
              </div>
              <div className="text-2xl font-extrabold tracking-tight">
                TIÊM CHỦNG
                <br />
                LONG CHÂU
              </div>
            </div>
          </div>

          {/* Ribbons */}
          <PinkRibbon
            className="left-8 top-[230px] hidden lg:flex"
            icon={<Syringe className="h-5 w-5" />}
            line1="Đầy đủ Vắc xin"
            small="từ các hãng dược"
            line2="HÀNG ĐẦU THẾ GIỚI"
          />
          <PinkRibbon
            className="left-16 top-[420px] hidden lg:flex"
            icon={<ShieldCheck className="h-5 w-5" />}
            line1="Bảo quản Vắc xin"
            small="chuẩn Quốc Tế"
            line2="GSP - WHO"
          />

          {/* CTA pill */}
          <div className="absolute bottom-12 left-1/2 hidden -translate-x-1/2 lg:block">
            <button
              onClick={() => setChatOpen(true)}
              className="rounded-full bg-white px-8 py-3.5 text-lg font-extrabold tracking-wide text-[var(--brand-pink-deep)] shadow-lg ring-1 ring-[var(--brand-pink)]/40 transition duration-300 hover:scale-105 cursor-pointer"
            >
              &gt; Trò chuyện tư vấn ngay &lt;
            </button>
          </div>
        </div>
      </main>

      {/* Vaccine Packages Section */}
      <section ref={packagesRef} className="bg-slate-50 py-16 px-6 lg:px-8 shrink-0">
        <div className="mx-auto max-w-[1400px] space-y-12">
          {/* Commitments Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {COMMITMENTS.map((item, idx) => (
              <div key={idx} className="flex items-center gap-4 bg-white rounded-2xl p-5 border border-slate-100 shadow-sm hover:shadow-md transition duration-300">
                <img src={item.icon_url} alt={item.name} className="h-12 w-12 object-contain" />
                <div>
                  <h4 className="font-extrabold text-slate-800 text-[14.5px]">{item.name}</h4>
                  <p className="text-slate-500 text-[12px] font-semibold mt-0.5">{item.description}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Section Title */}
          <div className="text-center space-y-2">
            <h2 className="text-2xl lg:text-3xl font-black text-slate-900 uppercase tracking-tight">
              Bảng giá gói vắc xin tiêm chủng
            </h2>
            <p className="text-slate-500 text-sm max-w-xl mx-auto font-medium">
              Thiết kế phác đồ tiêm chủng trọn gói khoa học cho mọi lứa tuổi, tối ưu chi phí và luôn cam kết đủ vắc xin.
            </p>
          </div>

          {/* Group 1: Theo độ tuổi */}
          <div className="space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-200 pb-3">
              <span className="h-5 w-1.5 bg-[var(--brand)] rounded-full" />
              <h3 className="text-lg font-black text-slate-800 uppercase tracking-wider">
                Gói vắc xin theo độ tuổi
              </h3>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {AGE_PACKAGES.map((pkg) => (
                <div key={pkg.id} className="bg-white rounded-3xl overflow-hidden border border-slate-100 shadow-md hover:shadow-xl transition duration-300 flex flex-col group">
                  {/* Image container */}
                  <div className="h-[180px] bg-sky-50/50 flex items-center justify-center p-6 relative overflow-hidden shrink-0">
                    <img 
                      src={pkg.image_url} 
                      alt={pkg.title} 
                      className="max-h-[140px] object-contain transition-transform duration-300 group-hover:scale-105" 
                    />
                    <span className="absolute top-4 left-4 bg-emerald-50 text-emerald-600 font-extrabold text-[11px] px-2.5 py-1 rounded-full border border-emerald-100 shadow-sm">
                      Tiết kiệm {pkg.discount_amount}
                    </span>
                  </div>
                  
                  {/* Content */}
                  <div className="p-6 flex-1 flex flex-col justify-between space-y-4">
                    <div className="space-y-1.5">
                      <h4 className="font-extrabold text-slate-800 text-[15px] leading-snug group-hover:text-[var(--brand)] transition duration-200 uppercase">
                        {pkg.title}
                      </h4>
                      <p className="text-slate-400 text-[11px] font-semibold">SKU: {pkg.sku}</p>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Pricing */}
                      <div className="flex items-baseline gap-2">
                        <span className="text-xl font-black text-[var(--brand-pink-deep)]">{pkg.final_price}</span>
                        <span className="text-slate-400 text-xs line-through font-semibold">{pkg.total_price}</span>
                      </div>
                      
                      {/* Action buttons */}
                      <div className="grid grid-cols-2 gap-2.5">
                        <a 
                          href={pkg.detail_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="py-2.5 px-3 rounded-xl border border-slate-200 hover:border-[var(--brand)] text-[var(--brand)] font-bold text-[12px] text-center transition duration-200 flex items-center justify-center gap-1 cursor-pointer bg-slate-50/50"
                        >
                          Xem chi tiết
                        </a>
                        <button 
                          onClick={() => {
                            setChatOpen(true);
                            handleSend(`Tôi muốn tư vấn đăng ký gói vắc xin: ${pkg.title}`);
                          }}
                          className="py-2.5 px-3 rounded-xl bg-[var(--brand)] hover:bg-[var(--brand-deep)] text-white font-extrabold text-[12px] text-center transition duration-200 shadow-md shadow-blue-500/10 cursor-pointer"
                        >
                          Tư vấn ngay
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Group 2: Theo đối tượng */}
          <div className="space-y-6 pt-6">
            <div className="flex items-center gap-3 border-b border-slate-200 pb-3">
              <span className="h-5 w-1.5 bg-[var(--brand-pink)] rounded-full" />
              <h3 className="text-lg font-black text-slate-800 uppercase tracking-wider">
                Gói vắc xin theo đối tượng
              </h3>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {TARGET_PACKAGES.map((pkg) => (
                <div key={pkg.id} className="bg-white rounded-3xl overflow-hidden border border-slate-100 shadow-md hover:shadow-xl transition duration-300 flex flex-col group">
                  {/* Image container */}
                  <div className="h-[180px] bg-pink-50/20 flex items-center justify-center p-6 relative overflow-hidden shrink-0">
                    <img 
                      src={pkg.image_url} 
                      alt={pkg.title} 
                      className="max-h-[140px] object-contain transition-transform duration-300 group-hover:scale-105" 
                    />
                    <span className="absolute top-4 left-4 bg-emerald-50 text-emerald-600 font-extrabold text-[11px] px-2.5 py-1 rounded-full border border-emerald-100 shadow-sm">
                      Tiết kiệm {pkg.discount_amount}
                    </span>
                  </div>
                  
                  {/* Content */}
                  <div className="p-6 flex-1 flex flex-col justify-between space-y-4">
                    <div className="space-y-1.5">
                      <h4 className="font-extrabold text-slate-800 text-[15px] leading-snug group-hover:text-[var(--brand)] transition duration-200 uppercase">
                        {pkg.title}
                      </h4>
                      <p className="text-slate-400 text-[11px] font-semibold">SKU: {pkg.sku}</p>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Pricing */}
                      <div className="flex items-baseline gap-2">
                        <span className="text-xl font-black text-[var(--brand-pink-deep)]">{pkg.final_price}</span>
                        <span className="text-slate-400 text-xs line-through font-semibold">{pkg.total_price}</span>
                      </div>
                      
                      {/* Action buttons */}
                      <div className="grid grid-cols-2 gap-2.5">
                        <a 
                          href={pkg.detail_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="py-2.5 px-3 rounded-xl border border-slate-200 hover:border-[var(--brand)] text-[var(--brand)] font-bold text-[12px] text-center transition duration-200 flex items-center justify-center gap-1 cursor-pointer bg-slate-50/50"
                        >
                          Xem chi tiết
                        </a>
                        <button 
                          onClick={() => {
                            setChatOpen(true);
                            handleSend(`Tôi muốn tư vấn đăng ký gói vắc xin: ${pkg.title}`);
                          }}
                          className="py-2.5 px-3 rounded-xl bg-[var(--brand)] hover:bg-[var(--brand-deep)] text-white font-extrabold text-[12px] text-center transition duration-200 shadow-md shadow-blue-500/10 cursor-pointer"
                        >
                          Tư vấn ngay
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <ChatLauncher
        chatOpen={chatOpen}
        chatExpanded={isExpanded}
        onOpenChat={() => setChatOpen(true)}
      />

      {/* Backdrop overlay */}
      <div
        className={`fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-500 ease-in-out ${
          chatOpen && isExpanded
            ? "opacity-100 pointer-events-auto"
            : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setIsExpanded(false)}
      />

      {/* Chat panel */}
      <div className={containerClasses}>
        <div className="flex h-full w-full flex-row overflow-hidden">
          {/* Chat column */}
          <div
            className={`flex flex-col h-full overflow-hidden transition-all duration-500 ease-in-out bg-white ${
              isExpanded ? "w-full md:w-[52%] border-r border-slate-100" : "w-full"
            }`}
          >
            {/* Header */}
            <div
              className="flex items-center gap-2.5 px-4 py-3.5 text-white shrink-0"
              style={{
                background: "linear-gradient(135deg, var(--brand) 0%, var(--brand-deep) 100%)",
              }}
            >
              <DoctorAvatar className="h-9 w-9 ring-2 ring-white/90" />
              <div className="flex-1 text-[13px] font-extrabold uppercase tracking-wider">
                Chat với  Long Châu
              </div>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="hidden sm:block rounded-full p-1 hover:bg-white/10 cursor-pointer mr-1"
                title={isExpanded ? "Thu nhỏ" : "Mở rộng"}
              >
                {isExpanded ? <Minimize2 className="h-5 w-5" /> : <Maximize2 className="h-5 w-5" />}
              </button>
              <button
                onClick={() => setChatOpen(false)}
                className="rounded-full p-1 hover:bg-white/10 cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Messages list */}
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto bg-[var(--chat-bg)] px-4 py-4 space-y-4"
            >
              <div className="text-center text-[11px] text-muted-foreground">
                Hôm nay {timeLabel}
              </div>

              {messages.map((m) => {
                const isUser = m.from === "user";
                if (!isUser && !m.text && !m.toolData && !m.quickReplies) {
                  return null;
                }
                return (
                  <div
                    key={m.id}
                    className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
                  >
                    <div
                      className={`flex items-end gap-2 max-w-[90%] ${isUser ? "justify-end" : "justify-start"}`}
                    >
                      {!isUser && <DoctorAvatar className="h-8 w-8 shrink-0 mb-1" />}
                      <div
                        className={`rounded-2xl px-4 py-2.5 text-[13.5px] leading-relaxed shadow-sm whitespace-pre-line ${
                          isUser
                            ? "bg-[var(--brand)] text-white rounded-tr-sm"
                            : "bg-white text-slate-800 rounded-bl-sm border border-black/5"
                        }`}
                      >
                        {isUser ? m.text : <MarkdownText text={m.text} />}
                      </div>
                    </div>

                    {/* Render custom card data returned from backend tools */}
                    {!isUser && m.toolData && !m.isStreaming && (
                      <div className="w-full mt-3 pl-10 pr-4 space-y-3">
                        {isExpanded ? (
                          // In expanded mode, show a small interactive badge/button pointing to the right details panel
                          <div className="rounded-xl border border-slate-100 bg-white p-3.5 shadow-sm hover:shadow-md transition duration-200">
                            <div className="flex items-center gap-2 text-xs font-extrabold text-[var(--brand)]">
                              <Info className="h-4 w-4 text-[var(--brand)]" />
                              <span>
                                {m.toolData.stores && m.toolData.stores.length > 0
                                  ? "Danh sách Trung tâm Tiêm chủng"
                                  : m.toolData.vaccines && m.toolData.vaccines.length > 0
                                    ? "Danh sách Vắc xin đề xuất"
                                    : m.toolData.combos && m.toolData.combos.length > 0
                                      ? "Danh sách Gói vắc xin"
                                      : m.toolData.doctors && m.toolData.doctors.length > 0
                                        ? "Đội ngũ  tư vấn"
                                        : m.toolData.booking
                                          ? "Thông tin Phiếu hẹn tiêm"
                                          : m.toolData.callback_form
                                            ? "Đăng ký Dược sĩ gọi lại"
                                            : "Thông tin bổ sung"}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-500 mt-1 leading-normal font-semibold">
                              Thông tin chi tiết đã được tự động hiển thị ở bảng điều khiển bên
                              phải.
                            </p>
                            {activeMessageId !== m.id && (
                              <button
                                onClick={() => setSelectedMessageId(m.id)}
                                className="mt-2 w-full py-1 rounded bg-slate-50 text-[var(--brand)] text-[10.5px] font-bold border border-slate-200 hover:bg-slate-100 transition cursor-pointer"
                              >
                                Hiển thị bảng này ở bên phải
                              </button>
                            )}
                          </div>
                        ) : (
                          // Standard inline view
                          <>
                            {/* Safety Warning Red Box */}
                            {(m.safetyTriggered || m.toolData.safety_escalation) && (
                              <SafetyEscalationPanel
                                type="Medical Alert"
                                message={m.text}
                                onSubmitCallback={handleCallbackSubmit}
                              />
                            )}

                            {/* Vaccines list card */}
                            {m.toolData.vaccines && m.toolData.vaccines.length > 0 && (
                              <div className="grid grid-cols-1 gap-2.5">
                                {m.toolData.vaccines.map((vac, idx) => (
                                  <VaccineCard
                                    key={idx}
                                    vac={vac}
                                    onSelect={(name) =>
                                      handleSend(`Đăng ký tiêm chủng vắc xin ${name}`)
                                    }
                                  />
                                ))}
                              </div>
                            )}

                            {/* Combos list card */}
                            {m.toolData.combos && m.toolData.combos.length > 0 && (
                              <div className="grid grid-cols-1 gap-2.5">
                                {m.toolData.combos.map((combo, idx) => (
                                  <ComboCard
                                    key={idx}
                                    combo={combo}
                                    onSelect={(title) => handleSend(`Đăng ký gói vắc xin ${title}`)}
                                  />
                                ))}
                              </div>
                            )}

                            {/* Stores selection */}
                            {m.toolData.stores && m.toolData.stores.length > 0 && (
                              <div className="grid grid-cols-1 gap-2.5">
                                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                                  Chọn trung tâm tiêm chủng:
                                </div>
                                {m.toolData.stores.map((store, idx) => (
                                  <StoreCard
                                    key={idx}
                                    store={store}
                                    onSelect={(id, name) =>
                                      handleSend(`Tôi chọn trung tâm: ${name} (ID: ${id})`)
                                    }
                                  />
                                ))}
                              </div>
                            )}

                            {/* Doctors list */}
                            {m.toolData.doctors && m.toolData.doctors.length > 0 && (
                              <div className="grid grid-cols-1 gap-2.5">
                                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                                  Đội ngũ  tư vấn trực ca:
                                </div>
                                {m.toolData.doctors.map((doc, idx) => (
                                  <DoctorCard
                                    key={idx}
                                    doc={doc}
                                    onSelect={(name) =>
                                      handleSend(`Tôi muốn đặt lịch tư vấn với  ${name}`)
                                    }
                                  />
                                ))}
                              </div>
                            )}

                            {/* Booking appointment ticket */}
                            {m.toolData.booking && (
                              <div className="space-y-3">
                                <BookingTicket booking={m.toolData.booking} />
                                <SMSSimulator smsText={m.toolData.booking.sms_preview} />
                              </div>
                            )}

                            {/* Callback Form */}
                            {m.toolData.callback_form && (
                              <CallbackForm onSubmit={handleCallbackSubmit} />
                            )}
                          </>
                        )}
                      </div>
                    )}

                    {/* Render Quick Replies */}
                    {!isUser && m.quickReplies && m.quickReplies.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pl-10 mt-2 max-w-[90%]">
                        {m.quickReplies.map((q) => (
                          <button
                            key={q}
                            onClick={() => handleSend(q)}
                            className="rounded-full border border-[var(--brand)]/30 bg-white px-3 py-1.5 text-[11px] font-semibold text-[var(--brand)] transition hover:bg-[var(--brand)] hover:text-white cursor-pointer"
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Bouncing loading indicator */}
              {typing && (
                <div className="flex items-end gap-2">
                  <DoctorAvatar className="h-8 w-8 shrink-0 mb-1" />
                  <div className="rounded-2xl rounded-bl-sm bg-white border border-black/5 px-4 py-3 shadow-sm">
                    <div className="flex gap-1.5 items-center">
                      <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--brand)] [animation-delay:-0.3s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--brand)] [animation-delay:-0.15s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--brand)]" />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Composer */}
            <div className="flex items-center gap-2 border-t border-black/5 bg-white px-3 py-2.5">
              <button
                onClick={handleGetLocation}
                disabled={locating}
                title="Lấy vị trí hiện tại của bạn"
                className="p-2 text-muted-foreground hover:text-[var(--brand)] disabled:opacity-50 cursor-pointer transition relative group"
              >
                <MapPin
                  className={`h-4.5 w-4.5 ${locating ? "animate-pulse text-[var(--brand)]" : ""}`}
                />
              </button>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder={locating ? "Đang xác định vị trí..." : "Nhập tin nhắn..."}
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400 py-1"
                disabled={locating}
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || locating}
                className="text-[var(--brand)] hover:text-[var(--brand-deep)] disabled:text-slate-300 p-1 cursor-pointer transition"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>

            {/* Disclaimer Footer */}
            <div className="bg-slate-50 px-4 py-2 text-[10px] text-slate-400 border-t border-black/5 text-center leading-relaxed shrink-0">
              * Lưu ý: Các tư vấn của Trợ lý AI chỉ mang tính chất tham khảo. Quý khách sẽ được Bác
              sĩ khám sàng lọc lâm sàng trực tiếp trước khi chỉ định tiêm chủng.
            </div>
          </div>

          {/* Right Details Column (Only in expanded mode on desktop/tablet) */}
          <div
            className={`hidden md:flex flex-col h-full overflow-hidden bg-slate-50 border-l border-slate-100 transition-all ease-in-out
              ${
                isExpanded
                  ? "w-[48%] opacity-100 duration-300 delay-300"
                  : "w-0 opacity-0 pointer-events-none border-l-0 duration-200 delay-0"
              }
            `}
          >
            {/* Header of Details Panel */}
            <div className="flex items-center gap-2.5 px-6 py-4 bg-white border-b border-slate-100 shrink-0">
              <div className="h-8 w-8 rounded-full bg-[var(--brand-soft)]/50 flex items-center justify-center text-[var(--brand)]">
                <Syringe className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-extrabold text-slate-800 uppercase tracking-wider">
                  {activeMessage?.toolData
                    ? activeMessage.toolData.stores && activeMessage.toolData.stores.length > 0
                      ? "Hệ thống Trung tâm Tiêm chủng"
                      : activeMessage.toolData.vaccines &&
                          activeMessage.toolData.vaccines.length > 0
                        ? "Danh mục Vắc xin đề xuất"
                        : activeMessage.toolData.combos && activeMessage.toolData.combos.length > 0
                          ? "Danh sách Gói vắc xin ưu đãi"
                          : activeMessage.toolData.doctors &&
                              activeMessage.toolData.doctors.length > 0
                            ? "Danh sách  trực ca"
                            : activeMessage.toolData.booking
                              ? "Thông tin đăng ký lịch tiêm"
                              : activeMessage.toolData.callback_form
                                ? "Yêu cầu Gọi lại tư vấn"
                                : "Chi tiết dịch vụ"
                    : "Bảng điều khiển chi tiết"}
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  {activeMessage
                    ? `Hiển thị từ tin nhắn của  lúc ${timeLabel}`
                    : "Hệ thống hỗ trợ y tế chuyên sâu Long Châu"}
                </p>
              </div>
            </div>

            {/* Details Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {activeMessage?.toolData ? (
                <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                  {/* Safety Warning Red Box */}
                  {(activeMessage.safetyTriggered || activeMessage.toolData.safety_escalation) && (
                    <div className="mb-4">
                      <SafetyEscalationPanel
                        type="Medical Alert"
                        message={activeMessage.text}
                        onSubmitCallback={handleCallbackSubmit}
                      />
                    </div>
                  )}

                  {/* Vaccines List */}
                  {activeMessage.toolData.vaccines &&
                    activeMessage.toolData.vaccines.length > 0 && (
                      <div className="space-y-3">
                        <div className="text-[11px] font-extrabold text-slate-500 uppercase tracking-widest">
                          Vắc xin đề xuất ({activeMessage.toolData.vaccines.length})
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          {activeMessage.toolData.vaccines.map((vac, idx) => (
                            <VaccineCard
                              key={idx}
                              vac={vac}
                              onSelect={(name) => handleSend(`Đăng ký tiêm chủng vắc xin ${name}`)}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Combos List */}
                  {activeMessage.toolData.combos && activeMessage.toolData.combos.length > 0 && (
                    <div className="space-y-3">
                      <div className="text-[11px] font-extrabold text-slate-500 uppercase tracking-widest">
                        Gói Vắc xin đề xuất ({activeMessage.toolData.combos.length})
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        {activeMessage.toolData.combos.map((combo, idx) => (
                          <ComboCard
                            key={idx}
                            combo={combo}
                            onSelect={(title) => handleSend(`Đăng ký gói vắc xin ${title}`)}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Stores Selection */}
                  {activeMessage.toolData.stores && activeMessage.toolData.stores.length > 0 && (
                    <div className="space-y-3">
                      <div className="text-[11px] font-extrabold text-slate-500 uppercase tracking-widest">
                        Danh sách trung tâm tiêm chủng ({activeMessage.toolData.stores.length})
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        {activeMessage.toolData.stores.map((store, idx) => (
                          <StoreCard
                            key={idx}
                            store={store}
                            onSelect={(id, name) =>
                              handleSend(`Tôi chọn trung tâm: ${name} (ID: ${id})`)
                            }
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Doctors List */}
                  {activeMessage.toolData.doctors && activeMessage.toolData.doctors.length > 0 && (
                    <div className="space-y-3">
                      <div className="text-[11px] font-extrabold text-slate-500 uppercase tracking-widest">
                         chuyên môn trực ca ({activeMessage.toolData.doctors.length})
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        {activeMessage.toolData.doctors.map((doc, idx) => (
                          <DoctorCard
                            key={idx}
                            doc={doc}
                            onSelect={(name) =>
                              handleSend(`Tôi muốn đặt lịch tư vấn với  ${name}`)
                            }
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Booking Appointment Ticket */}
                  {activeMessage.toolData.booking && (
                    <div className="max-w-md mx-auto space-y-4">
                      <div className="text-[11px] font-extrabold text-slate-500 uppercase tracking-widest text-center">
                        Phiếu hẹn dịch vụ của bạn
                      </div>
                      <BookingTicket booking={activeMessage.toolData.booking} />
                      <SMSSimulator smsText={activeMessage.toolData.booking.sms_preview} />
                    </div>
                  )}

                  {/* Callback Form */}
                  {activeMessage.toolData.callback_form && (
                    <div className="max-w-md mx-auto space-y-3 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
                      <div className="text-[11px] font-extrabold text-slate-500 uppercase tracking-widest text-center mb-2">
                        Đăng ký gọi lại tư vấn chuyên sâu
                      </div>
                      <CallbackForm onSubmit={handleCallbackSubmit} />
                    </div>
                  )}
                </div>
              ) : (
                // Empty State Dashboard when no cards are active
                <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4">
                  <div className="h-16 w-16 rounded-full bg-blue-50 flex items-center justify-center text-[var(--brand)] text-3xl">
                    🏥
                  </div>
                  <div className="max-w-sm space-y-2">
                    <h4 className="text-sm font-extrabold text-slate-700 uppercase tracking-wider">
                      Dịch vụ Tiêm chủng FPT Long Châu
                    </h4>
                    <p className="text-xs text-slate-500 leading-relaxed font-semibold">
                      Hỏi  Long Châu để tìm kiếm trung tâm tiêm chủng gần nhất, xem thông tin
                      vắc-xin, các gói tiêm chủng ưu đãi và đặt lịch hẹn tiêm trực tuyến.
                    </p>
                  </div>

                  {/* Short guides or highlights */}
                  <div className="grid grid-cols-2 gap-3 w-full max-w-md pt-6 border-t border-slate-100 mt-4">
                    <div className="p-3 bg-white rounded-xl border border-slate-100 text-left">
                      <div className="text-[11px] font-bold text-slate-800">
                        📍 Định vị trung tâm
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        Tìm địa chỉ tiêm chủng gần bạn nhất chỉ trong 1 giây
                      </div>
                    </div>
                    <div className="p-3 bg-white rounded-xl border border-slate-100 text-left">
                      <div className="text-[11px] font-bold text-slate-800">💉 Tra cứu Vắc xin</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        Đầy đủ thông tin nguồn gốc, phác đồ tiêm chi tiết
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Details Panel Footer */}
            <div className="bg-white border-t border-slate-100 px-6 py-3 text-center shrink-0">
              <span className="text-[10.5px] font-bold text-slate-500">
                📞 Hỗ trợ tiêm chủng khẩn cấp:{" "}
                <a href="tel:18006928" className="text-[var(--brand)] hover:underline">
                  1800 6928
                </a>{" "}
                (Miễn phí)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Sub-components for Cards ---------- */

function VaccineCard({ vac, onSelect }: { vac: Vaccine; onSelect: (name: string) => void }) {
  return (
    <div className="flex flex-col rounded-xl border border-slate-100 bg-white p-3 shadow-sm hover:shadow-md transition duration-200">
      {vac.image_url &&
        (vac.detail_url ? (
          <a href={vac.detail_url} target="_blank" rel="noopener noreferrer">
            <img
              src={vac.image_url}
              alt={vac.name}
              className="h-28 w-full object-cover rounded-lg mb-2 hover:opacity-90 transition"
            />
          </a>
        ) : (
          <img
            src={vac.image_url}
            alt={vac.name}
            className="h-28 w-full object-cover rounded-lg mb-2"
          />
        ))}
      {vac.detail_url ? (
        <a
          href={vac.detail_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[13px] font-extrabold text-slate-800 hover:text-[var(--brand)] transition line-clamp-1"
        >
          {vac.name}
        </a>
      ) : (
        <div className="text-[13px] font-extrabold text-slate-800">{vac.name}</div>
      )}
      <div className="text-[11px] text-slate-500 mt-0.5 leading-snug">
        Phòng bệnh: {vac.prevention}
      </div>

      {vac.phac_do && (
        <div className="text-[10px] text-slate-400 mt-1 bg-slate-50 p-1.5 rounded line-clamp-2">
          <strong>Lịch tiêm:</strong> {vac.phac_do}
        </div>
      )}

      <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-100">
        <div>
          <div className="text-[9px] text-slate-400 uppercase tracking-wider">Giá bán lẻ</div>
          <div className="text-[13.5px] font-black text-[var(--brand-pink-deep)]">
            {typeof vac.price === "number" ? vac.price.toLocaleString("vi-VN") + "đ" : vac.price}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[9px] text-slate-400 uppercase tracking-wider">Xuất xứ</div>
          <div className="text-[11.5px] font-bold text-slate-700">{vac.origin}</div>
        </div>
      </div>
      <button
        onClick={() => onSelect(vac.name)}
        className="mt-2.5 w-full py-1.5 rounded-lg bg-[var(--brand)] text-white text-[11px] font-bold hover:bg-[var(--brand-deep)] transition cursor-pointer"
      >
        Đăng ký mũi tiêm này
      </button>
    </div>
  );
}

function ComboCard({ combo, onSelect }: { combo: Combo; onSelect: (title: string) => void }) {
  return (
    <div className="flex flex-col rounded-xl border border-slate-100 bg-white p-3 shadow-sm hover:shadow-md transition duration-200">
      {combo.image_url &&
        (combo.detail_url ? (
          <a href={combo.detail_url} target="_blank" rel="noopener noreferrer">
            <img
              src={combo.image_url}
              alt={combo.title}
              className="h-28 w-full object-cover rounded-lg mb-2 hover:opacity-90 transition"
            />
          </a>
        ) : (
          <img
            src={combo.image_url}
            alt={combo.title}
            className="h-28 w-full object-cover rounded-lg mb-2"
          />
        ))}
      {combo.detail_url ? (
        <a
          href={combo.detail_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[13px] font-extrabold text-slate-800 hover:text-[var(--brand)] transition line-clamp-1"
        >
          {combo.title}
        </a>
      ) : (
        <div className="text-[13px] font-extrabold text-slate-800">{combo.title}</div>
      )}

      <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-100">
        <div>
          <div className="text-[9px] text-slate-400 line-through">
            {typeof combo.total_price === "number"
              ? combo.total_price.toLocaleString("vi-VN") + "đ"
              : combo.total_price}
          </div>
          <div className="text-[14px] font-black text-[var(--brand-pink-deep)]">
            {typeof combo.final_price === "number"
              ? combo.final_price.toLocaleString("vi-VN") + "đ"
              : combo.final_price}
          </div>
        </div>
        {combo.discount_amount && (
          <span className="text-[9px] bg-rose-50 border border-rose-100 text-rose-600 font-extrabold px-2 py-0.5 rounded-full">
            Tiết kiệm{" "}
            {typeof combo.discount_amount === "number"
              ? combo.discount_amount.toLocaleString("vi-VN") + "đ"
              : combo.discount_amount}
          </span>
        )}
      </div>
      <button
        onClick={() => onSelect(combo.title)}
        className="mt-2.5 w-full py-1.5 rounded-lg bg-[var(--brand)] text-white text-[11px] font-bold hover:bg-[var(--brand-deep)] transition cursor-pointer"
      >
        Đăng ký gói vaccine
      </button>
    </div>
  );
}

function StoreCard({
  store,
  onSelect,
}: {
  store: Store;
  onSelect: (id: number, name: string) => void;
}) {
  return (
    <div className="flex flex-col rounded-xl border border-slate-100 bg-white p-3 shadow-sm hover:shadow-md transition duration-200">
      {store.image_url && (
        <img
          src={store.image_url}
          alt={store.name}
          className="h-24 w-full object-cover rounded-lg mb-2"
        />
      )}
      <div className="text-[12.5px] font-extrabold text-slate-800 leading-snug line-clamp-2">
        {store.name}
      </div>
      <div className="text-[11px] text-slate-500 mt-1 leading-snug">📍 {store.address}</div>
      {store.distance !== undefined && store.distance !== null && (
        <div className="text-[11.5px] text-[var(--brand)] font-bold mt-1 bg-sky-50 px-2 py-0.5 rounded-md inline-flex items-center gap-1 w-max">
          🚶 Cách bạn:{" "}
          {store.distance < 1
            ? `${(store.distance * 1000).toFixed(0)} m`
            : `${store.distance.toFixed(2)} km`}
        </div>
      )}
      <div className="flex gap-2 mt-3 pt-2 border-t border-slate-50">
        {store.google_map_link && (
          <a
            href={store.google_map_link}
            target="_blank"
            rel="noreferrer"
            className="flex-1 text-center py-1.5 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 text-[10.5px] font-bold transition"
          >
            Chỉ đường
          </a>
        )}
        <button
          onClick={() => onSelect(store.id, store.name)}
          className="flex-[2] py-1.5 rounded-lg bg-[var(--brand)] text-white text-[10.5px] font-extrabold hover:bg-[var(--brand-deep)] transition cursor-pointer"
        >
          Chọn trung tâm này
        </button>
      </div>
    </div>
  );
}

function DoctorCard({ doc, onSelect }: { doc: Doctor; onSelect: (name: string) => void }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-slate-100 bg-white p-3 shadow-sm hover:shadow-md transition duration-200">
      {doc.avatar_url && (
        <img
          src={doc.avatar_url}
          alt={doc.name}
          className="h-11 w-11 rounded-full object-cover ring-2 ring-[var(--brand)]/10 shrink-0"
        />
      )}
      <div className="flex-1 min-w-0">
        <div className="text-[12.5px] font-extrabold text-slate-800">
          {doc.degree} {doc.name}
        </div>
        <div className="text-[10px] font-bold text-[var(--brand)] mt-0.5">
          {doc.specialization} • {doc.position}
        </div>
        {doc.biography && (
          <div className="text-[10px] text-slate-500 mt-1 line-clamp-2 italic leading-relaxed">
            "{doc.biography}"
          </div>
        )}
        <button
          onClick={() => onSelect(doc.name)}
          className="mt-2 text-[10.5px] font-extrabold text-[var(--brand)] hover:underline cursor-pointer"
        >
          Đăng ký tư vấn với 
        </button>
      </div>
    </div>
  );
}

function BookingTicket({ booking }: { booking: Booking }) {
  return (
    <div className="relative rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200/50 p-4 shadow-sm overflow-hidden">
      <div className="absolute top-1/2 -left-3 h-5 w-5 -translate-y-1/2 rounded-full bg-[var(--chat-bg)] border-r border-blue-200/50" />
      <div className="absolute top-1/2 -right-3 h-5 w-5 -translate-y-1/2 rounded-full bg-[var(--chat-bg)] border-l border-blue-200/50" />

      <div className="text-center pb-3 border-b border-dashed border-blue-200">
        <div className="text-[10px] font-extrabold uppercase tracking-widest text-[var(--brand)]">
          PHIẾU HẸN TIÊM CHỦNG
        </div>
        <div className="text-[19px] font-black text-slate-800 mt-1 tracking-wider">
          {booking.booking_code}
        </div>
      </div>

      <div className="space-y-2 mt-3 text-[11.5px] text-slate-700">
        <div className="flex justify-between">
          <span className="text-slate-400">Khách hàng:</span>
          <span className="font-extrabold text-slate-800">{booking.name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Số điện thoại:</span>
          <span className="font-extrabold text-slate-800">{booking.phone}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Vaccine:</span>
          <span className="font-extrabold text-slate-800">{booking.vaccine_name}</span>
        </div>
        <div className="border-t border-slate-200/50 pt-2 mt-2">
          <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
            Trung tâm tiêm chủng:
          </div>
          <div className="font-extrabold text-slate-800 mt-0.5 leading-snug">
            {booking.center_name}
          </div>
          <div className="text-[10.5px] text-slate-500 mt-0.5 leading-snug">
            {booking.center_address}
          </div>
        </div>
        <div className="flex justify-between border-t border-slate-200/50 pt-2">
          <span className="text-slate-400">Ngày tiêm:</span>
          <span className="font-extrabold text-[var(--brand)]">{booking.date}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Khung giờ:</span>
          <span className="font-extrabold text-[var(--brand)]">{booking.time}</span>
        </div>
      </div>
    </div>
  );
}

function SMSSimulator({ smsText }: { smsText: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-100 p-2 shadow-inner">
      <div className="bg-white rounded-xl p-3 border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100 mb-2">
          <div className="h-6 w-6 rounded-full bg-blue-600 flex items-center justify-center text-white text-[9px] font-bold">
            LC
          </div>
          <div className="leading-tight">
            <div className="text-[10px] font-extrabold text-slate-800">FPT Long Châu</div>
            <div className="text-[8px] text-slate-400 uppercase tracking-wider font-semibold">
              SMS Xác nhận
            </div>
          </div>
        </div>
        <div className="bg-slate-100 text-slate-800 p-2.5 rounded-2xl rounded-tl-sm text-[11px] leading-relaxed font-mono whitespace-pre-wrap">
          {smsText}
        </div>
      </div>
    </div>
  );
}

function SafetyEscalationPanel({
  type,
  message,
  onSubmitCallback,
}: {
  type: string;
  message: string;
  onSubmitCallback: (name: string, phone: string, details: string) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !phone) return;
    setLoading(true);
    await onSubmitCallback(name, phone, `Cảnh báo an toàn [${type}]: ${message}`);
    setLoading(false);
    setSubmitted(true);
  };

  return (
    <div className="rounded-2xl bg-rose-50 border border-rose-200 p-4 space-y-3.5 text-slate-800">
      <div className="flex items-start gap-2.5 text-rose-700">
        <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
        <div className="leading-snug">
          <div className="font-black text-[12px] uppercase tracking-wider">
            CẢNH BÁO AN TOÀN Y KHOA
          </div>
          <div className="text-[11.5px] mt-1 font-semibold leading-relaxed">
            Hệ thống phát hiện tình trạng sức khỏe hoặc chỉ định vaccine cần kiểm tra y tế trực
            tiếp. Để đảm bảo an toàn tuyệt đối, Anh/Chị không nên tự ý đặt lịch tiêm chủng trực
            tuyến cho trường hợp này.
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        <a
          href="tel:18006928"
          className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-[11.5px] font-black shadow-sm transition"
        >
          📞 Gọi Hotline 1800 6928
        </a>
      </div>

      {!submitted ? (
        <form onSubmit={handleSubmit} className="border-t border-rose-200 pt-3.5 space-y-2">
          <div className="text-[10px] font-extrabold text-rose-800 uppercase tracking-wider">
             tư vấn gọi lại khẩn cấp:
          </div>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Họ và tên người cần tiêm..."
            className="w-full text-[11.5px] px-3 py-2 rounded-lg border border-rose-200 bg-white focus:outline-none focus:ring-1 focus:ring-rose-500"
          />
          <input
            required
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="Số điện thoại liên lạc..."
            className="w-full text-[11.5px] px-3 py-2 rounded-lg border border-rose-200 bg-white focus:outline-none focus:ring-1 focus:ring-rose-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-lg bg-rose-700 hover:bg-rose-800 text-white text-[11px] font-extrabold transition disabled:opacity-50 cursor-pointer"
          >
            {loading ? "Đang gửi đăng ký..." : "Gửi yêu cầu Gọi lại ngay"}
          </button>
        </form>
      ) : (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-2.5 rounded-xl text-[11px] font-bold text-center flex items-center justify-center gap-1.5">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          <span> đã nhận yêu cầu và sẽ gọi lại trong 5 phút!</span>
        </div>
      )}
    </div>
  );
}

function CallbackForm({
  onSubmit,
}: {
  onSubmit: (name: string, phone: string, details: string) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [details, setDetails] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !phone) return;
    setLoading(true);
    await onSubmit(name, phone, details);
    setLoading(false);
    setSubmitted(true);
  };

  return (
    <div className="rounded-xl border border-slate-100 bg-white p-3.5 shadow-sm space-y-3">
      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-2.5">
          <div className="text-[11px] font-extrabold text-slate-700 uppercase tracking-wider flex items-center gap-1">
            <User className="h-3.5 w-3.5 text-[var(--brand)]" />
            <span>Đăng ký Dược sĩ tư vấn chuyên sâu</span>
          </div>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Họ và tên..."
            className="w-full text-[11.5px] px-3 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-[var(--brand)]"
          />
          <input
            required
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="Số điện thoại..."
            className="w-full text-[11.5px] px-3 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-[var(--brand)]"
          />
          <textarea
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder="Nêu thắc mắc y tế của bạn (ví dụ: đang dùng thuốc...)"
            rows={2}
            className="w-full text-[11.5px] px-3 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-[var(--brand)] resize-none leading-relaxed"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full py-1.5 rounded-lg bg-[var(--brand)] text-white text-[11px] font-bold hover:bg-[var(--brand-deep)] transition disabled:opacity-50 cursor-pointer"
          >
            {loading ? "Đang gửi thông tin..." : "Yêu cầu Gọi lại tư vấn"}
          </button>
        </form>
      ) : (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg text-[11.5px] text-center space-y-1">
          <div className="font-extrabold flex items-center justify-center gap-1">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span>Đăng ký tư vấn thành công!</span>
          </div>
          <div className="text-[10px] text-emerald-700">
            Dược sĩ chuyên môn sẽ liên hệ đến số của Anh/Chị trong 15 phút tới.
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Basic static visual helpers ---------- */

function TopBar() {
  return (
    <div className="border-b border-black/5 bg-white shadow-sm z-10">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3 sm:px-6 sm:gap-6">
        {/* logo */}
        <div className="flex items-center gap-2 text-[var(--brand-deep)] shrink-0">
          <div className="grid h-9 w-9 place-items-center rounded-md bg-[var(--brand)] text-white shadow-sm shrink-0">
            <BrandMark className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <div className="text-[9px] font-semibold uppercase tracking-widest text-[var(--brand)]">
              FPT Retail
            </div>
            <div className="text-base font-extrabold tracking-tight">TIÊM CHỦNG LONG CHÂU</div>
          </div>
        </div>

        {/* search */}
        <div className="hidden md:flex flex-1 items-center gap-2 rounded-full border border-[var(--brand)]/35 bg-white px-4 py-2 text-sm shadow-inner max-w-md lg:max-w-xl mx-auto">
          <input
            placeholder="Bạn cần vắc xin đi nước ngoài, du học, vắc xin cúm...?"
            className="flex-1 bg-transparent outline-none placeholder:text-slate-400 py-0.5"
            disabled
          />
          <button className="grid h-7 w-7 place-items-center rounded-full bg-[var(--brand)] text-white shadow-sm hover:bg-[var(--brand-deep)] transition cursor-pointer">
            <Search className="h-4 w-4" />
          </button>
        </div>

        {/* user */}
        <button className="hidden sm:flex items-center gap-2 rounded-full border border-black/10 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 hover:border-[var(--brand)]/40 transition shrink-0">
          <div className="grid h-7 w-7 place-items-center rounded-full bg-[var(--brand-cyan)] text-[var(--brand-deep)] font-bold">
            <Phone className="h-3.5 w-3.5" />
          </div>
          <span className="hidden md:inline">Hotline: 1800 6928</span>
          <span className="inline md:hidden">1800 6928</span>
        </button>

        {/* cart */}
        <button
          className="flex items-center gap-2 rounded-full px-3.5 py-1.5 sm:px-4 sm:py-2 text-xs sm:text-sm font-black text-white shadow-md hover:shadow-lg transition cursor-pointer shrink-0"
          style={{
            background:
              "linear-gradient(135deg, var(--brand-pink) 0%, var(--brand-pink-deep) 100%)",
          }}
        >
          <ShoppingCart className="h-4 w-4" />
          <span>Đăng ký</span>
        </button>
      </div>
    </div>
  );
}

function NavBar({ onPackagesClick }: { onPackagesClick?: () => void }) {
  return (
    <nav className="border-b border-black/5 bg-white z-10 hidden md:block">
      <div className="mx-auto flex max-w-[1400px] items-center gap-7 px-6 py-3 text-[13px] font-bold text-[var(--brand-deep)]">
        {NAV.map((item) => (
          <button
            key={item}
            onClick={() => {
              if (item === "Gói vắc xin" && onPackagesClick) {
                onPackagesClick();
              }
            }}
            className="flex items-center gap-1 hover:text-[var(--brand)] transition cursor-pointer"
          >
            {item}
            {(item.includes("phòng bệnh") ||
              item.includes("Gói") ||
              item.includes("Khuyến") ||
              item.includes("Kiến thức")) && <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        ))}
      </div>
    </nav>
  );
}

function PinkRibbon({
  className = "",
  icon,
  line1,
  small,
  line2,
}: {
  className?: string;
  icon: React.ReactNode;
  line1: string;
  small: string;
  line2: string;
}) {
  return (
    <div className={`absolute ${className}`}>
      <div className="flex items-stretch shadow-2xl rounded-2xl overflow-hidden hover:scale-[1.02] transition duration-300">
        {/* badge */}
        <div
          className="grid w-16 place-items-center text-white"
          style={{
            background:
              "linear-gradient(135deg, var(--brand-pink) 0%, var(--brand-pink-deep) 100%)",
          }}
        >
          <div className="grid h-9 w-9 place-items-center rounded-full ring-2 ring-white/60">
            {icon}
          </div>
        </div>
        {/* body */}
        <div
          className="px-5 py-3 pr-8 text-white"
          style={{
            background: "linear-gradient(135deg, var(--brand) 0%, var(--brand-deep) 100%)",
          }}
        >
          <div className="text-[15px] font-bold leading-tight">{line1}</div>
          <div className="text-[10px] uppercase tracking-wider text-white/80 mt-0.5">{small}</div>
          <div className="text-xl font-extrabold tracking-tight mt-0.5">{line2}</div>
        </div>
      </div>
    </div>
  );
}

function BrandMark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <rect x="2" y="3" width="9" height="9" rx="2" fill="currentColor" />
      <rect x="13" y="3" width="9" height="9" rx="2" fill="currentColor" opacity="0.55" />
      <rect x="2" y="14" width="9" height="7" rx="2" fill="currentColor" opacity="0.75" />
      <rect x="13" y="14" width="9" height="7" rx="2" fill="currentColor" />
    </svg>
  );
}

function DoctorAvatar({ className = "" }: { className?: string }) {
  return (
    <div
      className={`overflow-hidden rounded-full ring-2 ring-white shadow-sm shrink-0 select-none bg-sky-50 ${className}`}
    >
      <img
        src={healthtechChatAvatar}
        alt="HealthTech AI"
        className="h-full w-full object-cover object-center"
        draggable={false}
      />
    </div>
  );
}

function MarkdownText({ text }: { text: string }) {
  if (!text) return null;

  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];

  let currentTableLines: string[] = [];

  const parseInlineElements = (txt: string) => {
    if (!txt) return [];
    // Split by markdown images and links
    const parts = txt.split(/(!?\[[^\]]*\]\([^)]*\))/g);
    return parts.map((part, idx) => {
      // 1. Check if it's an image
      if (part.startsWith("![") && part.endsWith(")")) {
        const match = part.match(/^!\[(.*?)\]\((.*?)\)$/);
        if (match) {
          const alt = match[1];
          const src = match[2];
          return (
            <div key={idx} className="relative group overflow-hidden rounded-2xl border border-slate-100 shadow-md my-2 max-w-[280px] bg-slate-50">
              <img
                src={src}
                alt={alt}
                className="w-full h-auto object-cover max-h-[160px] transition-transform duration-300 group-hover:scale-105"
                onError={(e) => {
                  const parent = (e.target as HTMLElement).parentElement;
                  if (parent) parent.style.display = "none";
                }}
              />
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2 text-white text-[10px] font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-200 truncate">
                {alt}
              </div>
            </div>
          );
        }
      }
      // 2. Check if it's a link
      if (part.startsWith("[") && part.endsWith(")")) {
        const match = part.match(/^\[(.*?)\]\((.*?)\)$/);
        if (match) {
          const linkText = match[1];
          const url = match[2];
          return (
            <a
              key={idx}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 my-1 rounded-full bg-blue-50/80 hover:bg-blue-100/90 text-[var(--brand)] font-bold text-[12px] transition duration-200 border border-blue-100/60 shadow-sm cursor-pointer"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--brand-pink)] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--brand-pink)]"></span>
              </span>
              {linkText === "Link" ? "Xem chi tiết sản phẩm" : linkText}
              <span className="text-[10px] ml-0.5 opacity-80">↗</span>
            </a>
          );
        }
      }
      // 3. Parse bold text
      const boldParts = part.split(/(\*\*.*?\*\*)/g);
      return boldParts.map((bPart, bIdx) => {
        if (bPart.startsWith("**") && bPart.endsWith("**")) {
          return (
            <strong key={`${idx}-${bIdx}`} className="font-black text-slate-900">
              {bPart.slice(2, -2)}
            </strong>
          );
        }
        return bPart;
      });
    });
  };

  const renderBufferedTable = (tableLines: string[], index: number) => {
    if (tableLines.length < 2) return null; // Needs at least header + separator

    const parseCells = (lineStr: string) => {
      const cells = lineStr.split("|").map((s) => s.trim());
      if (lineStr.trim().startsWith("|")) {
        cells.shift();
      }
      if (lineStr.trim().endsWith("|")) {
        cells.pop();
      }
      return cells;
    };

    // Parse header
    const rawHeaders = parseCells(tableLines[0]);

    // Parse rows (skip index 1 which is the separator |---|)
    const rawRows = tableLines.slice(2).map((line) => parseCells(line));

    return (
      <div
        key={`table-${index}`}
        className="overflow-x-auto my-3 rounded-xl border border-slate-100 shadow-sm bg-white"
      >
        <table className="min-w-full divide-y divide-slate-100 text-[12px] leading-relaxed">
          <thead className="bg-slate-50 font-extrabold text-slate-700">
            <tr>
              {rawHeaders.map((headerText, i) => (
                <th
                  key={i}
                  className="px-3 py-2 text-left font-bold border-r border-slate-100 last:border-r-0"
                >
                  {parseInlineElements(headerText)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white text-slate-600">
            {rawRows.map((rowCells, rIdx) => (
              <tr
                key={rIdx}
                className="hover:bg-slate-50/50 transition duration-150 odd:bg-slate-50/30"
              >
                {rowCells.map((cellText, cIdx) => (
                  <td key={cIdx} className="px-3 py-2 border-r border-slate-50 last:border-r-0">
                    {parseInlineElements(cellText)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Check if it's a table row
    const pipeCount = (trimmed.match(/\|/g) || []).length;
    const isTableRow = pipeCount >= 2;

    if (isTableRow) {
      currentTableLines.push(line);
      continue;
    }

    // If we were parsing a table and now hit a non-table line, render the table
    if (currentTableLines.length > 0) {
      elements.push(renderBufferedTable(currentTableLines, i));
      currentTableLines = [];
    }

    if (!trimmed) {
      elements.push(<div key={`empty-${i}`} className="h-1.5" />);
      continue;
    }

    // Horizontal Rule (--- or -- or similar dividers)
    if (/^(\-\-\-+|\-\-+)$/.test(trimmed)) {
      elements.push(<hr key={`hr-${i}`} className="my-3 border-t border-slate-200/60" />);
      continue;
    }

    // Headers: ###, ##, #
    const headerMatch = line.match(/^(#{1,6})\s+(.*)/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const content = headerMatch[2];
      const headerClasses =
        level === 1
          ? "text-lg font-black text-slate-900 mt-3 mb-1.5"
          : level === 2
          ? "text-base font-extrabold text-slate-900 mt-2.5 mb-1"
          : "text-[13.5px] font-black text-slate-800 mt-2 mb-1 flex items-center gap-1";

      elements.push(
        <div key={`header-${i}`} className={headerClasses}>
          {parseInlineElements(content)}
        </div>
      );
      continue;
    }

    // Bullet points
    const matchBullet = line.match(/^(\s*)([*•-]\s+)(.*)/);
    if (matchBullet) {
      const content = matchBullet[3];
      if (/^(\-\-\-+|\-\-+)$/.test(content.trim())) {
        elements.push(<hr key={`hr-${i}`} className="my-3 border-t border-slate-200/60" />);
        continue;
      }
      elements.push(
        <div key={`bullet-${i}`} className="flex items-start gap-1.5 pl-3.5 relative py-0.5">
          <span className="absolute left-1 text-[var(--brand)] font-extrabold select-none">•</span>
          <span className="flex-1 text-[13.5px] leading-relaxed text-slate-700">
            {parseInlineElements(content)}
          </span>
        </div>
      );
      continue;
    }

    // Standard paragraph line
    elements.push(
      <div key={`p-${i}`} className="text-[13.5px] leading-relaxed text-slate-700 py-0.5">
        {parseInlineElements(line)}
      </div>
    );
  }

  // Render any trailing table at the end of the text
  if (currentTableLines.length > 0) {
    elements.push(renderBufferedTable(currentTableLines, lines.length));
  }

  return <div className="space-y-0.5">{elements}</div>;
}
