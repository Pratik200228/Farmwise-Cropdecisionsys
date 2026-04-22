import { useCallback, useState } from "react";
import { mockAdvisorReply, sendFarmAdvisorMessage } from "../lib/farmAdvisorApi";
import type { ChatMessage, FarmContext } from "../types/farm";

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useFarmAdvisor(initialContext: FarmContext) {
  const [context, setContext] = useState<FarmContext>(initialContext);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: newId(),
      role: "assistant",
      content:
        "Welcome to **FarmWise AI**. Set your **Farm context** on the right, then ask about crops, markets, soil moisture, or crop health. I will use your context in every answer.",
      createdAt: Date.now(),
    },
  ]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      const userMsg: ChatMessage = {
        id: newId(),
        role: "user",
        content: trimmed,
        createdAt: Date.now(),
      };

      let threadForApi: ChatMessage[] = [];

      setError(null);
      setPending(true);
      setMessages((prev) => {
        threadForApi = [...prev, userMsg];
        return threadForApi;
      });

      try {
        const reply = await sendFarmAdvisorMessage(threadForApi, context);
        setMessages((prev) => [
          ...prev,
          {
            id: newId(),
            role: "assistant",
            content: reply,
            createdAt: Date.now(),
          },
        ]);
      } catch (e) {
        const explicitMock = import.meta.env.VITE_USE_MOCK_AI === "true";
        if (!explicitMock) {
          const fallback = mockAdvisorReply(threadForApi, context);
          setMessages((prev) => [
            ...prev,
            {
              id: newId(),
              role: "assistant",
              content:
                `_(API unreachable — showing offline guidance.)_\n\n${fallback}`,
              createdAt: Date.now(),
            },
          ]);
          setError(
            e instanceof Error ? e.message : "Could not reach the advisor API.",
          );
        } else {
          setError(e instanceof Error ? e.message : "Request failed");
        }
      } finally {
        setPending(false);
      }
    },
    [context],
  );

  const clearThread = useCallback(() => {
    setMessages([
      {
        id: newId(),
        role: "assistant",
        content:
          "Thread cleared. Ask a new question — I will still use your **Farm context**.",
        createdAt: Date.now(),
      },
    ]);
    setError(null);
  }, []);

  return {
    context,
    setContext,
    messages,
    send,
    pending,
    error,
    clearThread,
  };
}
