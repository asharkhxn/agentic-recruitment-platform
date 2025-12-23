import { useState, useEffect } from "react";
import { agentApi } from "@/api/agent";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { Send, Bot, User } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  sql?: string;
}

export const ChatbotPage = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>();

  useEffect(() => {
    document.title = "AI Chatbot - Recruitment System";
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    await sendPrompt(input);
  };

  const sendPrompt = async (messageToSend: string) => {
    if (!messageToSend.trim()) return;

    // Get user from localStorage
    const userStr = localStorage.getItem("user");
    if (!userStr) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error: Please login to use the chatbot",
        },
      ]);
      return;
    }
    const user = JSON.parse(userStr);

    const userMessage: Message = { role: "user", content: messageToSend };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await agentApi.chat({
        message: messageToSend,
        user_id: user.id,
        conversation_id: conversationId,
      });

      setConversationId(response.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.response,
          sql: response.sql_generated,
        },
      ]);
    } catch (error: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${error.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts: { label: string; prompt: string }[] = [
    {
      label: "Create job (example)",
      prompt:
        "Create a job for Senior Backend Engineer in London, requirements: Python, FastAPI, PostgreSQL, salary: £80k-£100k",
    },
    {
      label: "Summarize a job",
      prompt: 'Summarize the job "Senior Backend Engineer" in 2-3 sentences',
    },
    { label: "Find jobs in London", prompt: "Find jobs in London" },
    { label: "Find jobs 100k+", prompt: "Find jobs with salary above 100k" },
    {
      label: "View applicants",
      prompt: "Show applicants for job_id: <paste-job-id-here>",
    },
    {
      label: "Rank applicants",
      prompt: "Rank applicants for job_id: <paste-job-id-here>",
    },
  ];

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-24">
      <div className="max-w-3xl space-y-5">
        <span className="accent-pill">AI Copilot</span>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight text-white sm:text-5xl">
          Bring instant intelligence to every hiring conversation.
        </h1>
        <p className="text-base text-white/70">
          Pull contextual insights, craft outreach, and understand applicants on
          the fly. The assistant is tuned to your pipeline so every decision
          feels obvious.
        </p>
      </div>

      <Card className="w-full">
        <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="flex items-center gap-3 text-white">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
              <Bot className="h-5 w-5" />
            </span>
            AI Recruitment Assistant
          </CardTitle>
          <p className="text-sm text-white/50">
            Ask about roles, talent pools, or pipeline momentum.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="h-[460px] space-y-4 overflow-y-auto rounded-[28px] border border-white/10 bg-white/5 px-6 py-6">
            {messages.length === 0 && (
              <p className="text-center text-sm text-white/60">
                Start a conversation to see the assistant shape your hiring
                workflow.
              </p>
            )}
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-3 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`flex max-w-[78%] gap-3 rounded-2xl px-5 py-4 text-sm leading-relaxed shadow-[0_18px_36px_rgba(8,10,24,0.35)] ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-[#6c63ff] via-[#8f69ff] to-[#f3a9ff] text-white"
                      : "bg-white/10 text-white/85"
                  }`}
                >
                  {message.role === "assistant" && (
                    <Bot className="mt-1 h-5 w-5 text-white/70" />
                  )}
                  <div className="flex-1 space-y-2">
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.sql && (
                      <pre className="max-h-32 overflow-x-auto overflow-y-auto rounded-lg bg-black/40 p-3 text-xs">
                        {message.sql}
                      </pre>
                    )}
                  </div>
                  {message.role === "user" && <User className="mt-1 h-5 w-5" />}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/65">
                  <Spinner size="sm" />
                  <span>Thinking…</span>
                </div>
              </div>
            )}
          </div>

          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-3 sm:flex-row"
          >
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a role, pipeline, or applicant insight"
              disabled={loading}
            />
            <Button
              type="submit"
              disabled={loading || !input.trim()}
              className="sm:w-auto"
            >
              <span className="flex items-center gap-2">
                <Send className="h-4 w-4" />
                <span>Send</span>
              </span>
            </Button>
          </form>

          {/* Quick prompts placed below send form for easy access */}
          <div className="mt-4 flex flex-wrap gap-3">
            {quickPrompts.map((p) => (
              <Button
                key={p.label}
                variant="ghost"
                size="sm"
                className="rounded-full border border-white/10 px-4"
                onClick={() => sendPrompt(p.prompt)}
              >
                {p.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
