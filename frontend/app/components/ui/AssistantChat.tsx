"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { MessageCircle, X, CornerDownLeft, Sparkles } from "lucide-react";
import { buildSystemPrompt, PromptContext } from "@/app/lib/agent_prompt";
import { useModeStore } from "@/components/ModeToggle";

type Message = { role: "user" | "assistant"; content: string };

export function AssistantChat() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const { isEasyMode } = useModeStore();
  const mode = isEasyMode ? "easy" : "advanced";
  
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hi! I'm your ProtEngine Labs assistant. Ask me anything about the pipeline, the science, or the UI." }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sessionId = pathname?.includes("/analysis/") ? pathname.split("/analysis/")[1] : null;
  const page = pathname === "/" ? "home" : pathname?.split("/")[1] || "home";

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendWithPrompt = async (
    userMsg: Message,
    history: Message[],
    ctxParams: Partial<PromptContext> = {}
  ) => {
    setIsLoading(true);
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    const ctx: PromptContext = {
      mode,
      page,
      sessionId,
      pipelineStatus: "IDLE", // To hook up realistically we'd need global state
      ...ctxParams
    };

    const systemPrompt = buildSystemPrompt(ctx);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...history, userMsg],
          system: systemPrompt
        })
      });

      if (!res.ok) {
        throw new Error("Chat failed");
      }

      const data = await res.json();
      const text = data.content?.[0]?.text || "No response";

      setMessages((prev) => [...prev, { role: "assistant", content: text }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I ran into an error connecting to the AI." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendWithPrompt({ role: "user", content: input }, messages);
  };

  return (
    <>
      {/* Floating Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-primary text-primary-foreground rounded-full shadow-2xl flex items-center justify-center hover:scale-105 transition-transform z-50 border-2 border-primary/20"
        aria-label="Toggle AI Assistant"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={28} />}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[600px] max-h-[80vh] bg-card border shadow-[0_12px_40px_rgba(0,0,0,0.12)] rounded-2xl flex flex-col z-50 overflow-hidden text-sm">
          {/* Header */}
          <div className="p-4 border-b bg-muted/30 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              <span className="font-semibold text-base tracking-tight">AI Assistant</span>
              <span className="ml-2 text-xs text-muted-foreground uppercase tracking-wider font-bold">
                {mode}
              </span>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div 
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 leading-relaxed ${
                    m.role === "user" 
                      ? "bg-primary text-primary-foreground rounded-br-sm" 
                      : "bg-muted text-foreground rounded-bl-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap whitespace-break-spaces">{m.content}</p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl rounded-bl-sm bg-muted text-muted-foreground px-4 py-3 flex gap-1 items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce delay-75" />
                  <span className="w-1.5 h-1.5 rounded-full bg-current animate-bounce delay-150" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-3 border-t bg-background">
            <div className="relative flex items-center">
              <input
                type="text"
                placeholder="Ask me anything..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="w-full bg-muted/50 border-0 rounded-full pl-4 pr-10 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <button 
                type="submit" 
                disabled={!input.trim() || isLoading}
                className="absolute right-2 text-primary p-1.5 rounded-full hover:bg-primary/10 transition-colors disabled:opacity-50"
              >
                <CornerDownLeft className="w-4 h-4" />
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
