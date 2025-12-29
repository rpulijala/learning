"use client";

import { useState, useRef, useEffect } from "react";
import { BACKEND_URL } from "@/config";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type PlanStep = {
  step: number;
  description: string;
  tool: string | null;
  tool_input: Record<string, unknown> | null;
};

type ContextLogEntry = {
  step: number;
  action: string;
  result: string;
};

type DebugInfo = {
  plan: PlanStep[];
  context_log: ContextLogEntry[];
};

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState<"openai" | "ollama">("openai");
  const [debugMode, setDebugMode] = useState(false);
  const [streaming, setStreaming] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [showDebugPanel, setShowDebugPanel] = useState(false);
  
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    setError(null);
    setDebugInfo(null);
    
    // Add user message
    const userMessage: ChatMessage = { role: "user", content: trimmedInput };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setIsLoading(true);

    try {
      if (debugMode || !streaming) {
        // Sync mode
        await handleSyncRequest(updatedMessages);
      } else {
        // Streaming mode
        await handleStreamingRequest(updatedMessages);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSyncRequest = async (msgs: ChatMessage[]) => {
    const response = await fetch(`${BACKEND_URL}/chat/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: msgs,
        provider,
        debug: debugMode,
      }),
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    
    // Add assistant message
    setMessages((prev) => [...prev, { role: "assistant", content: data.content }]);
    
    // Store debug info if available
    if (debugMode && data.plan && data.context_log) {
      setDebugInfo({ plan: data.plan, context_log: data.context_log });
      setShowDebugPanel(true);
    }
  };

  const handleStreamingRequest = async (msgs: ChatMessage[]) => {
    const response = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: msgs,
        provider,
      }),
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`);
    }

    // Add placeholder assistant message
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6).trim();
          if (data === "[DONE]") continue;
          
          try {
            const parsed = JSON.parse(data);
            
            if (parsed.type === "token" && parsed.content) {
              // Append token to last message
              setMessages((prev) => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
                  updated[lastIdx] = {
                    ...updated[lastIdx],
                    content: updated[lastIdx].content + parsed.content,
                  };
                }
                return updated;
              });
            } else if (parsed.type === "error") {
              throw new Error(parsed.message);
            }
          } catch (e) {
            // Ignore parse errors for non-JSON lines
            if (e instanceof SyntaxError) continue;
            throw e;
          }
        }
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const canSend = input.trim().length > 0 && !isLoading;

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
          LifeHub Agent
        </h1>
        <div className="flex items-center gap-4">
          {/* Provider selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 dark:text-gray-400">Provider:</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as "openai" | "ollama")}
              className="px-3 py-1.5 text-sm bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama</option>
            </select>
          </div>
          
          {/* Streaming toggle */}
          <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={streaming}
              onChange={(e) => setStreaming(e.target.checked)}
              disabled={debugMode}
              className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Streaming
          </label>
          
          {/* Debug toggle */}
          <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={debugMode}
              onChange={(e) => {
                setDebugMode(e.target.checked);
                if (!e.target.checked) setShowDebugPanel(false);
              }}
              className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Debug
          </label>
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto px-4 py-6"
        >
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 dark:text-gray-400 py-12">
                <p className="text-lg">Welcome to LifeHub Agent</p>
                <p className="text-sm mt-2">Ask me about weather, manage tasks, or search your notes.</p>
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700"
                  }`}
                >
                  <div className="text-xs font-medium mb-1 opacity-70">
                    {msg.role === "user" ? "You" : "Assistant"}
                  </div>
                  <div className="whitespace-pre-wrap">{msg.content || (isLoading && msg.role === "assistant" ? "..." : "")}</div>
                </div>
              </div>
            ))}
            
            {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 px-4 py-3 rounded-2xl">
                  <div className="text-xs font-medium mb-1 opacity-70">Assistant</div>
                  <div className="flex items-center gap-2">
                    <div className="animate-pulse">Thinking...</div>
                  </div>
                </div>
              </div>
            )}
            
            {error && (
              <div className="flex justify-center">
                <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg border border-red-300 dark:border-red-700">
                  <p className="font-medium">Error</p>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Debug panel */}
        {showDebugPanel && debugInfo && (
          <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 max-h-64 overflow-y-auto">
            <div className="max-w-3xl mx-auto p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 dark:text-white">Debug Info</h3>
                <button
                  onClick={() => setShowDebugPanel(false)}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
              
              <div className="grid md:grid-cols-2 gap-4">
                {/* Plan */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Plan</h4>
                  <div className="bg-white dark:bg-gray-900 rounded-lg p-3 text-sm space-y-2">
                    {debugInfo.plan.map((step, idx) => (
                      <div key={idx} className="text-gray-700 dark:text-gray-300">
                        <span className="font-medium">Step {step.step}:</span> {step.description}
                        {step.tool && (
                          <span className="ml-2 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                            {step.tool}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Context Log */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Context Log</h4>
                  <div className="bg-white dark:bg-gray-900 rounded-lg p-3 text-sm space-y-2 max-h-40 overflow-y-auto">
                    {debugInfo.context_log.map((entry, idx) => (
                      <div key={idx} className="text-gray-700 dark:text-gray-300 border-b border-gray-100 dark:border-gray-800 pb-2 last:border-0">
                        <div className="font-medium">Step {entry.step}: {entry.action}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate" title={entry.result}>
                          {entry.result.slice(0, 150)}{entry.result.length > 150 ? "..." : ""}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-4">
          <div className="max-w-3xl mx-auto flex gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
              rows={1}
              className="flex-1 px-4 py-3 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <button
              onClick={handleSend}
              disabled={!canSend}
              className={`px-6 py-3 rounded-xl font-medium transition-colors ${
                canSend
                  ? "bg-blue-600 hover:bg-blue-700 text-white"
                  : "bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
              }`}
            >
              {isLoading ? "..." : "Send"}
            </button>
          </div>
          <div className="max-w-3xl mx-auto mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
            Using: <span className="font-medium">{provider}</span>
            {debugMode && <span className="ml-2">(Debug mode - sync only)</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
