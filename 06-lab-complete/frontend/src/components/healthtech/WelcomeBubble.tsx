import { X } from "lucide-react";

export type WelcomeBubbleVariant = "welcome" | "idle";

export interface WelcomeBubbleProps {
  variant?: WelcomeBubbleVariant;
  onClose: () => void;
  onChat: () => void;
}

export function WelcomeBubble({
  variant = "welcome",
  onClose,
  onChat,
}: WelcomeBubbleProps) {
  const isIdle = variant === "idle";

  return (
    <div
      className={`healthtech-bubble${isIdle ? " healthtech-bubble--idle" : ""}`}
      role="dialog"
      aria-label={isIdle ? "Lời mời hỗ trợ HealthTech AI" : "Chào mừng HealthTech AI"}
    >
      <div className="healthtech-bubble__card">
        <button
          type="button"
          className="healthtech-bubble__close"
          onClick={onClose}
          aria-label="Đóng"
        >
          <X className="h-3.5 w-3.5" strokeWidth={2.5} />
        </button>

        {isIdle ? (
          <>
            <p className="healthtech-bubble__idle-text">
              Cần hỗ trợ sức khỏe?
              <br />
              <span style={{ color: "#0369a1" }}>HealthTech AI luôn sẵn sàng.</span>
            </p>
            <button type="button" className="healthtech-bubble__cta" onClick={onChat}>
              Chat ngay
            </button>
          </>
        ) : (
          <>
            <p className="healthtech-bubble__title">👋 Xin chào!</p>
            <p className="healthtech-bubble__subtitle">Tôi là HealthTech AI.</p>
            <p className="healthtech-bubble__subtitle" style={{ marginBottom: "0.5rem" }}>
              Tôi có thể hỗ trợ:
            </p>
            <ul className="healthtech-bubble__list">
              <li>
                <span className="healthtech-bubble__check">✓</span>
                Tư vấn vaccine
              </li>
              <li>
                <span className="healthtech-bubble__check">✓</span>
                Giải đáp kiến thức sức khỏe
              </li>
              <li>
                <span className="healthtech-bubble__check">✓</span>
                Hỗ trợ lịch tiêm chủng
              </li>
            </ul>
            <button type="button" className="healthtech-bubble__cta" onClick={onChat}>
              Chat ngay
            </button>
          </>
        )}
      </div>
    </div>
  );
}
