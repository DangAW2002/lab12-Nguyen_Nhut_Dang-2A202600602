import { useEffect, useRef } from "react";
import mascotVideo from "@/assets/healthtech-mascot-1.webm";

export interface MascotProps {
  onClick: () => void;
  shake?: boolean;
  ariaLabel?: string;
}

export function Mascot({
  onClick,
  shake = false,
  ariaLabel = "Mở HealthTech AI chatbot",
}: MascotProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    video.muted = true;
    const play = () => {
      void video.play().catch(() => {
        /* autoplay may be blocked until user gesture */
      });
    };
    play();
    video.addEventListener("loadeddata", play);
    return () => video.removeEventListener("loadeddata", play);
  }, []);

  return (
    <button
      type="button"
      className={`healthtech-mascot${shake ? " healthtech-mascot--shake" : ""}`}
      onClick={onClick}
      aria-label={ariaLabel}
    >
      <span className="healthtech-mascot__motion" aria-hidden>
        <span className="healthtech-mascot__sway">
          <span className="healthtech-mascot__body">
            <video
              ref={videoRef}
              src={mascotVideo}
              className="healthtech-mascot__media"
              autoPlay
              loop
              muted
              playsInline
              preload="auto"
              disablePictureInPicture
              disableRemotePlayback
            />
          </span>
        </span>
      </span>
    </button>
  );
}
