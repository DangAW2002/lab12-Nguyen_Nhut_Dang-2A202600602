export const HEALTHTECH_JOKES = [
  "Virus hỏi: Cho tôi vào nhé? — Vaccine: Xin lỗi, hết vé rồi! 🎫",
  "Mũi kim tiêm ngắn hơn caption Instagram, nhưng hiệu quả dài hơn nhiều! 💉",
  "Stethoscope của tôi nghe được nhịp tim, chưa nghe được lý do trễ lịch tiêm 🤖",
  "Không sợ tiêm, chỉ sợ… quên lịch hẹn. Để tôi nhắc bạn nhé! 📅",
  "Uống đủ nước, ngủ đủ giấc — còn tiêm đủ mũi thì giao cho HealthTech AI!",
  "Bác sĩ robot không ngại ca đêm, chỉ ngại bạn không bấm 'Chat ngay'. 😄",
  "Vitamin C + vaccine = combo chống 'cúm' tin nhắn spam từ virus.",
  "Tôi là AI, không phải AI… kiệt sức vì bạn hỏi 'tiêm có đau không?' lần thứ 10.",
];

export function pickRandomJoke(): string {
  return HEALTHTECH_JOKES[Math.floor(Math.random() * HEALTHTECH_JOKES.length)]!;
}
