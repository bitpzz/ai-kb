import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getKB, listConvs, getMessages, newChat, continueChat, saveAssistantMessage,
} from "../api/client";

export default function ChatPage() {
  const { kbId } = useParams();
  const [kb, setKb] = useState(null);
  const [convs, setConvs] = useState([]);
  const [conv, setConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [streamingSources, setStreamingSources] = useState([]);
  const endRef = useRef(null);

  useEffect(() => { getKB(kbId).then(r => setKb(r.data)); }, [kbId]);
  useEffect(() => { loadConvs(); }, [kbId]);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, streamingText]);

  const loadConvs = async () => {
    try { const r = await listConvs(kbId); setConvs(r.data); } catch {}
  };

  const openConv = async (c) => {
    setConv(c);
    try { const r = await getMessages(c.id); setMessages(r.data); } catch {}
  };

  const send = async () => {
    const msg = input.trim();
    if (!msg || streaming) return;
    setInput("");
    setMessages(p => [...p, { role: "user", content: msg, sources: [], id: Date.now() }]);
    setStreaming(true);
    setStreamingText("");
    setStreamingSources([]);

    try {
      const r = conv ? await continueChat(conv.id, msg) : await newChat(kbId, msg);
      const cid = r.headers.get("X-Conversation-Id");

      if (!conv && cid) {
        const nc = { id: cid, title: msg.slice(0, 30), message_count: 2 };
        setConv(nc); setConvs(p => [nc, ...p]);
      }

      const reader = r.body.getReader();
      const d = new TextDecoder();
      let text = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of d.decode(value, { stream: true }).split("\n")) {
          if (!line.startsWith("data: ")) continue;
          try {
            const j = JSON.parse(line.slice(6));
            if (j.type === "text") { text += j.content; setStreamingText(text); }
            else if (j.type === "sources") setStreamingSources(j.content);
          } catch {}
        }
      }

      setMessages(p => [...p, { role: "assistant", content: text, sources: streamingSources, id: Date.now() }]);
      const target = cid || conv?.id;
      if (target) try { await saveAssistantMessage(target, text, streamingSources); } catch {}
    } catch (e) {
      setMessages(p => [...p, { role: "assistant", content: "出错了：" + e.message, sources: [], id: Date.now() }]);
    } finally {
      setStreaming(false); setStreamingText("");
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div className="h-screen flex bg-white">
      {/* ── 侧栏 ── */}
      <aside className="w-64 flex flex-col bg-gray-50 border-r border-gray-100 shrink-0">
        <div className="p-4">
          <Link to="/" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
            ← 返回首页
          </Link>
          <h2 className="text-sm font-bold text-gray-900 mt-2 truncate">{kb?.name}</h2>
          <button
            onClick={() => { setConv(null); setMessages([]); }}
            className="mt-3 w-full py-2 rounded-xl bg-gray-900 text-white text-sm font-semibold hover:bg-gray-800 transition-all"
          >
            新对话
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-0.5">
          {convs.length === 0 && <p className="text-xs text-gray-400 text-center mt-8">暂无对话</p>}
          {convs.map(c => (
            <div key={c.id}
              onClick={() => openConv(c)}
              className={`px-3 py-2.5 rounded-xl cursor-pointer text-sm transition-all ${
                conv?.id === c.id ? "bg-white shadow-sm border border-gray-200" : "hover:bg-gray-100"
              }`}
            >
              <p className="font-medium text-gray-800 truncate">{c.title}</p>
              <p className="text-xs text-gray-400 mt-0.5">{c.message_count} 条消息</p>
            </div>
          ))}
        </div>
      </aside>

      {/* ── 聊天主区 ── */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* 消息区 */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 && !streaming ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-sm px-6">
                <div className="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center text-2xl mx-auto mb-4">💡</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">开始对话</h3>
                <p className="text-sm text-gray-400 mb-6">基于知识库文档内容进行智能问答</p>
                <div className="space-y-2">
                  {["总结一下文档的主要内容", "列出文档中的关键信息", "这些文档讲了什么？"].map(q => (
                    <button key={q} onClick={() => { setInput(q); send(); }}
                      className="block w-full text-left px-4 py-2.5 bg-gray-50 hover:bg-gray-100 rounded-xl text-sm text-gray-600 transition-colors">
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
              {messages.map(m => (
                <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-gray-900 text-white"
                      : "bg-gray-50 text-gray-800"
                  }`}>
                    <div className="whitespace-pre-wrap">{m.content}</div>

                    {m.sources?.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-gray-200/60">
                        <p className="text-xs text-gray-400 font-medium mb-2">📖 参考原文</p>
                        {m.sources.map((s, i) => (
                          <details key={i} className="mb-1.5">
                            <summary className="inline-flex items-center gap-1 px-2.5 py-1 bg-white/60 rounded-full text-xs text-gray-500 cursor-pointer hover:bg-white transition-colors border border-gray-100">
                              {s.filename} · 片段 {s.chunk_index + 1}
                            </summary>
                            <div className="mt-1.5 p-3 bg-white rounded-xl text-xs text-gray-500 leading-relaxed border border-gray-100">
                              {s.content}
                            </div>
                          </details>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* 流式输出 */}
              {streaming && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-2xl px-5 py-3.5 bg-gray-50 text-sm">
                    {streamingText ? (
                      <span className="text-gray-800 whitespace-pre-wrap">{streamingText}</span>
                    ) : (
                      <div className="flex gap-1.5 py-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce" />
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: "0.1s" }} />
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: "0.2s" }} />
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div ref={endRef} />
            </div>
          )}
        </div>

        {/* 输入栏 */}
        <div className="border-t border-gray-100 bg-white px-6 py-4">
          <div className="max-w-3xl mx-auto flex gap-2 items-end bg-gray-50 border border-gray-200 rounded-2xl p-2 focus-within:border-gray-300 focus-within:bg-white transition-all">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={kb ? `向 ${kb.name} 提问...` : "输入问题..."}
              rows={1}
              className="flex-1 px-3 py-2 bg-transparent outline-none resize-none text-sm text-gray-800 placeholder:text-gray-400"
              disabled={streaming}
            />
            <button
              onClick={send}
              disabled={streaming || !input.trim()}
              className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                streaming || !input.trim()
                  ? "bg-gray-200 text-gray-400 cursor-default"
                  : "bg-gray-900 text-white hover:bg-gray-800 shadow-sm"
              }`}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 19V5M5 12l7-7 7 7" />
              </svg>
            </button>
          </div>
          <p className="text-center text-xs text-gray-300 mt-2">
            {kb?.name} · {kb?.document_count ?? 0} 篇文档 · Enter 发送
          </p>
        </div>
      </main>
    </div>
  );
}
