import React, { useState } from "react";
import { MessageSquare, Send, Bot, User, Sparkles, BookOpen, X } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { sendChatMessage } from "@/services/api";
import { toast } from "sonner";

interface Message {
  sender: "user" | "bot";
  text: string;
  citations?: any[];
}

export function KnowledgeAssistantModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "Hello! I am PolicyGuard's **Regulatory Knowledge Assistant** powered by local RBI/PMLA RAG intelligence. Ask me any regulatory question regarding KYC thresholds, AML reporting, or PMLA compliance rules.",
    },
  ]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { sender: "user", text: userMsg }]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(userMsg);
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: response.reply || "I retrieved the regulatory context.",
          citations: response.citations || [],
        },
      ]);
    } catch (err: any) {
      toast.error("Failed to query Knowledge Assistant.");
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "I encountered an issue processing your regulatory query. Please verify your query or try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Assistant Trigger Button */}
      <Button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 rounded-full h-14 px-5 bg-gradient-to-r from-primary to-secondary text-primary-foreground shadow-2xl hover:scale-105 transition-transform flex items-center gap-2 border border-white/20"
      >
        <Bot className="h-6 w-6 animate-pulse" />
        <span className="font-semibold text-sm hidden md:inline">Regulatory Knowledge Assistant</span>
      </Button>

      {/* Modal Dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[650px] h-[650px] flex flex-col bg-background/95 backdrop-blur-xl border border-primary/20 p-0 overflow-hidden">
          <DialogHeader className="p-4 border-b border-border/40 bg-muted/30 flex flex-row items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center border border-primary/40">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <div>
                <DialogTitle className="text-lg font-bold flex items-center gap-2">
                  Regulatory Knowledge Assistant
                </DialogTitle>
                <p className="text-xs text-muted-foreground">
                  Grounded in RBI Master Circulars, AML & PMLA Frameworks
                </p>
              </div>
            </div>
          </DialogHeader>

          {/* Chat Messages */}
          <ScrollArea className="flex-1 p-4 space-y-4">
            <div className="space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${
                    msg.sender === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {msg.sender === "bot" && (
                    <div className="h-8 w-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center shrink-0 mt-1">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}

                  <div
                    className={`max-w-[80%] rounded-2xl p-4 text-sm leading-relaxed ${
                      msg.sender === "user"
                        ? "bg-primary text-primary-foreground rounded-tr-none"
                        : "bg-muted/40 border border-border/50 rounded-tl-none whitespace-pre-wrap"
                    }`}
                  >
                    {msg.text}

                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border/30 text-xs text-muted-foreground space-y-1">
                        <p className="font-semibold flex items-center gap-1 text-primary">
                          <BookOpen className="h-3 w-3" /> Cited Regulatory Evidence:
                        </p>
                        {msg.citations.map((c: any, idx: number) => (
                          <div key={idx} className="bg-black/30 p-2 rounded border border-white/5 font-mono text-[11px]">
                            • [{c.id}] {c.source}: {c.text?.slice(0, 100)}...
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {msg.sender === "user" && (
                    <div className="h-8 w-8 rounded-full bg-secondary/20 border border-secondary/40 flex items-center justify-center shrink-0 mt-1">
                      <User className="h-4 w-4 text-secondary" />
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3 justify-start">
                  <div className="h-8 w-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center shrink-0 animate-spin">
                    <Sparkles className="h-4 w-4 text-primary" />
                  </div>
                  <div className="bg-muted/40 p-4 rounded-2xl text-xs text-muted-foreground animate-pulse">
                    Searching RBI Knowledge Base & analyzing regulatory evidence...
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Input Bar */}
          <div className="p-4 border-t border-border/40 bg-muted/20 flex gap-2">
            <Input
              placeholder="Ask about KYC rules, AML limits, or PMLA guidelines..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={isLoading}
              className="bg-background/80"
            />
            <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
