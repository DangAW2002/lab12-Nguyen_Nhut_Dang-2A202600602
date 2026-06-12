import { createFileRoute } from "@tanstack/react-router";
import { LongChauChat } from "@/components/LongChauChat";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Chatbot Tư vấn Tiêm chủng Long Châu" },
      {
        name: "description",
        content: "Giả lập giao diện chatbot tư vấn đăng ký gói tiêm chủng Long Châu.",
      },
      { property: "og:title", content: "Chatbot Tư vấn Tiêm chủng Long Châu" },
      {
        property: "og:description",
        content: "Trải nghiệm chatbot tư vấn gói tiêm chủng Long Châu.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  return <LongChauChat />;
}
