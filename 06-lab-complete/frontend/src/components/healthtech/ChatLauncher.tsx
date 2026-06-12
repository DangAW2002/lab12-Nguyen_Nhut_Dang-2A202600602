import { useCallback, useEffect, useRef, useState } from "react";
import { JokeBubble } from "./JokeBubble";
import { pickRandomJoke } from "./jokes";
import { Mascot } from "./Mascot";
import { WelcomeBubble } from "./WelcomeBubble";
import "./healthtech-mascot.css";

const JOKE_AUTO_HIDE_MS = 5500;

const WELCOME_DELAY_MS = 3000;
const IDLE_TIMEOUT_MS = 20000;

export interface ChatLauncherProps {
  chatOpen: boolean;
  /** Khung chat đang phóng to (modal full) */
  chatExpanded?: boolean;
  onOpenChat: () => void;
  /** Show numeric badge (1) or text (NEW) */
  badgeVariant?: "count" | "new";
}

export function ChatLauncher({
  chatOpen,
  chatExpanded = false,
  onOpenChat,
  badgeVariant = "count",
}: ChatLauncherProps) {
  const [welcomeVisible, setWelcomeVisible] = useState(false);
  const [welcomeDismissed, setWelcomeDismissed] = useState(false);
  const [idleInviteVisible, setIdleInviteVisible] = useState(false);
  const [idleDismissed, setIdleDismissed] = useState(false);
  const [shake, setShake] = useState(false);
  const [pulseBoost, setPulseBoost] = useState(false);
  const [jokeVisible, setJokeVisible] = useState(false);
  const [jokeText, setJokeText] = useState("");

  const lastActivityRef = useRef(Date.now());
  const idleTriggeredRef = useRef(false);
  const jokeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const registerActivity = useCallback(() => {
    lastActivityRef.current = Date.now();
    idleTriggeredRef.current = false;
    setIdleInviteVisible(false);
    setShake(false);
    setPulseBoost(false);
  }, []);

  useEffect(() => {
    if (welcomeDismissed || chatOpen) return;

    const timer = window.setTimeout(() => {
      setWelcomeVisible(true);
    }, WELCOME_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [welcomeDismissed, chatOpen]);

  useEffect(() => {
    if (chatOpen) {
      setWelcomeVisible(false);
      setIdleInviteVisible(false);
      return;
    }

    const onActivity = () => registerActivity();

    window.addEventListener("pointerdown", onActivity);
    window.addEventListener("keydown", onActivity);
    window.addEventListener("scroll", onActivity, { passive: true });

    const idleCheck = window.setInterval(() => {
      if (chatOpen || idleTriggeredRef.current) return;

      const elapsed = Date.now() - lastActivityRef.current;
      if (elapsed >= IDLE_TIMEOUT_MS && !idleDismissed) {
        idleTriggeredRef.current = true;
        setWelcomeVisible(false);
        setIdleInviteVisible(true);
        setPulseBoost(true);
        setShake(true);
        window.setTimeout(() => setShake(false), 700);
      }
    }, 1000);

    return () => {
      window.removeEventListener("pointerdown", onActivity);
      window.removeEventListener("keydown", onActivity);
      window.removeEventListener("scroll", onActivity);
      window.clearInterval(idleCheck);
    };
  }, [chatOpen, idleDismissed, registerActivity]);

  const hideJoke = useCallback(() => {
    if (jokeTimerRef.current) {
      clearTimeout(jokeTimerRef.current);
      jokeTimerRef.current = null;
    }
    setJokeVisible(false);
  }, []);

  useEffect(() => () => hideJoke(), [hideJoke]);

  const showJoke = useCallback(() => {
    hideJoke();
    setJokeText(pickRandomJoke());
    setJokeVisible(true);
    jokeTimerRef.current = setTimeout(() => {
      setJokeVisible(false);
      jokeTimerRef.current = null;
    }, JOKE_AUTO_HIDE_MS);
  }, [hideJoke]);

  const handleOpenChat = () => {
    registerActivity();
    setWelcomeVisible(false);
    setIdleInviteVisible(false);
    onOpenChat();
  };

  const handleMascotClick = () => {
    registerActivity();
    setWelcomeVisible(false);
    setIdleInviteVisible(false);
    showJoke();
    if (!chatOpen) {
      onOpenChat();
    }
  };

  const handleDismissWelcome = () => {
    registerActivity();
    setWelcomeVisible(false);
    setWelcomeDismissed(true);
  };

  const handleDismissIdle = () => {
    registerActivity();
    setIdleInviteVisible(false);
    setIdleDismissed(true);
  };

  const showWelcome = !chatOpen && welcomeVisible && !welcomeDismissed && !idleInviteVisible;
  const showIdleInvite = !chatOpen && idleInviteVisible && !idleDismissed;

  const launcherClass = [
    "healthtech-launcher",
    chatOpen && "healthtech-launcher--chat-open",
    chatOpen && chatExpanded && "healthtech-launcher--chat-expanded",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={launcherClass} aria-live="polite">
      <div className="healthtech-launcher__cluster">
        {showWelcome && (
          <WelcomeBubble
            variant="welcome"
            onClose={handleDismissWelcome}
            onChat={handleOpenChat}
          />
        )}
        {showIdleInvite && (
          <WelcomeBubble
            variant="idle"
            onClose={handleDismissIdle}
            onChat={handleOpenChat}
          />
        )}

        <div className="healthtech-launcher__stage">
          {jokeVisible && <JokeBubble text={jokeText} onClose={hideJoke} />}
          <span
            className={`healthtech-launcher__pulse healthtech-launcher__pulse--active${
              pulseBoost ? " healthtech-launcher__pulse--boost" : ""
            }`}
            aria-hidden
          />
          {!chatOpen && (
            <span
              className={`healthtech-launcher__badge${
                badgeVariant === "new" ? " healthtech-launcher__badge--new" : ""
              }`}
              aria-hidden
            >
              {badgeVariant === "new" ? "NEW" : "1"}
            </span>
          )}
          <Mascot onClick={handleMascotClick} shake={shake} />
        </div>
      </div>
    </div>
  );
}
