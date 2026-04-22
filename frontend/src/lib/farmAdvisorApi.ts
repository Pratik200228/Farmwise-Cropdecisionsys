import type { ChatMessage, FarmContext } from "../types/farm";
import { buildApiUrl, isMockAiEnabled } from "./runtimeConfig";

const ADVISOR_PATH = "/api/v1/farm-advisor/chat";

export type AdvisorRequestBody = {
  messages: { role: "user" | "assistant" | "system"; content: string }[];
  context: FarmContext;
};

export type AdvisorResponseBody = {
  reply?: string;
  message?: string;
};

function lastUserText(messages: ChatMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === "user") return messages[i].content;
  }
  return "";
}

export function mockAdvisorReply(messages: ChatMessage[], context: FarmContext): string {
  const q = lastUserText(messages).toLowerCase();
  const region = context.region.trim() || "your area";
  const goal =
    context.primaryGoal === "profit"
      ? "margin and market timing"
      : context.primaryGoal === "yield"
        ? "maximizing yield"
        : context.primaryGoal === "sustainability"
          ? "soil health and lower inputs"
          : "balanced yield and resilience";

  if (/price|market|sell|commodity/.test(q)) {
    return `For **${region}**, market-linked decisions work best when you combine USDA/commodity trend data with your harvest window.\n\n- Track basis and local elevator bids vs. futures.\n- If your goal is ${goal}, stress-test a “sell-by” date against storage cost.\n- Ask your backend agent to pull the latest USDA series for your crop once the API is wired.`;
  }
  if (/disease|pest|leaf|spot|yellow|health|plantix|plant village/.test(q)) {
    return `Crop health checks should pair **clear photos** (canopy + affected leaves) with **growth stage** and recent weather.\n\n- Rule out nutrition issues before assuming disease.\n- For ${region}, align scouting with humid/warm periods when fungal pressure rises.\n- When PlantVillage/Plantix is connected, send images through your FastAPI route—not the browser key.`;
  }
  if (/soil|moisture|irrigation|water|nasa/.test(q)) {
    return `With **${context.soilType}** soil on ~**${context.farmSizeAcres}** acres, water management should follow soil moisture trends and rooting depth.\n\n- Use NASA SMAP/IMERG-style signals as a regional guide, then ground-truth with field probes.\n- Match irrigation to crop stage; peak need often tracks flowering/grain fill.\n- Goal focus: ${goal}.`;
  }
  if (/what.+grow|crop|rotate|suitability|plant/.test(q)) {
    return `Here is a **structured starting point** for ${region} (${context.season}, ${context.soilType}).\n\n1. **Shortlist** 3–5 crops that match season length and water budget.\n2. **Score** them on heat/cold risk, soil fit, and market outlet.\n3. **Validate** with your Crop Suitability agent once weather + soil APIs are live.\n\nYour stated goal centers on **${goal}**. ${context.notes.trim() ? `Notes you added: _${context.notes.trim()}_` : "Add notes in Farm context for more specific rotation ideas."}`;
  }

  return `I am your **FarmWise advisor** (demo mode). I see you farm in **${region}** with **${context.soilType}** soil, ~**${context.farmSizeAcres}** acres, **${context.season}** season, optimizing for **${goal}**.\n\nTry asking about:\n- **Crop suitability** and rotation\n- **Market timing** and selling windows\n- **Crop health** scouting\n- **Soil moisture** and irrigation\n\nWhen the FastAPI route \`${ADVISOR_PATH}\` is implemented, answers will come from your team’s LLM agent with live data.`;
}

export async function sendFarmAdvisorMessage(
  messages: ChatMessage[],
  context: FarmContext,
): Promise<string> {
  if (isMockAiEnabled()) {
    await new Promise((r) => setTimeout(r, 600));
    return mockAdvisorReply(messages, context);
  }

  const body: AdvisorRequestBody = {
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
    context,
  };

  const res = await fetch(buildApiUrl(ADVISOR_PATH), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Advisor request failed (${res.status})`);
  }

  const data = (await res.json()) as AdvisorResponseBody;
  const reply = data.reply ?? data.message;
  if (!reply) throw new Error("Advisor response missing reply");
  return reply;
}
