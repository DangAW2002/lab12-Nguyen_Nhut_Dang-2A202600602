import { X } from "lucide-react";

export interface JokeBubbleProps {
  text: string;
  onClose: () => void;
}

export function JokeBubble({ text, onClose }: JokeBubbleProps) {
  return (
    <div className="healthtech-joke" role="status" aria-live="polite">
      <div className="healthtech-joke__card">
        <button
          type="button"
          className="healthtech-joke__close"
          onClick={onClose}
          aria-label="Đóng"
        >
          <X className="h-3.5 w-3.5" strokeWidth={2.5} />
        </button>
        <p className="healthtech-joke__label">HealthTech AI kể chuyện cười</p>
        <p className="healthtech-joke__text">{text}</p>
      </div>
    </div>
  );
}
