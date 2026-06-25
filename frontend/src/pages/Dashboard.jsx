import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { listKBs, createKB, deleteKB, listDocs, uploadDoc, deleteDoc } from "../api/client";

// ── 小组件 ──────────────────────────────

function KBModal({ show, onClose, onCreated }) {
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [loading, setLoading] = useState(false);

  if (!show) return null;

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim() || loading) return;
    setLoading(true);
    try { await createKB({ name, description: desc }); onCreated(); onClose(); } catch {}
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl p-6" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-bold text-gray-900 mb-5">新建知识库</h2>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">名称</label>
            <input
              value={name} onChange={e => setName(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm outline-none focus:bg-white focus:border-gray-400 transition-all"
              placeholder="给知识库起个名字"
              autoFocus required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">描述 <span className="text-gray-300 font-normal">可选</span></label>
            <textarea
              value={desc} onChange={e => setDesc(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm outline-none focus:bg-white focus:border-gray-400 transition-all"
              rows={2} placeholder="简要描述知识库用途"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">取消</button>
            <button type="submit" disabled={loading}
              className="px-5 py-2 bg-gray-900 text-white text-sm font-semibold rounded-xl hover:bg-gray-800 disabled:opacity-50 transition-all">
              {loading ? "创建中..." : "创建"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function DocRow({ doc, onDelete }) {
  const emoji = { pdf: "📄", docx: "📝", doc: "📝", txt: "📃", md: "📃" }[doc.file_type] || "📎";
  const badge = doc.status === "ready"
    ? "bg-emerald-50 text-emerald-600"
    : doc.status === "processing"
    ? "bg-amber-50 text-amber-600"
    : doc.status === "error"
    ? "bg-red-50 text-red-500"
    : "bg-gray-100 text-gray-400";
  const label = { ready: "就绪", processing: "处理中", error: "失败", pending: "排队" }[doc.status] || doc.status;

  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 group transition-colors">
      <span className="text-xl">{emoji}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 truncate">{doc.filename}</p>
        <p className="text-xs text-gray-400 mt-0.5">
          {(doc.file_size / 1024).toFixed(0)} KB · {doc.chunk_count} 个分块
        </p>
      </div>
      <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${badge}`}>{label}</span>
      <button onClick={() => onDelete(doc.id)}
        className="text-gray-300 hover:text-red-500 text-xs font-medium opacity-0 group-hover:opacity-100 transition-all">
        删除
      </button>
    </div>
  );
}

// ── 页面 ─────────────────────────────────

export default function Dashboard() {
  const [kbs, setKBs] = useState([]);
  const [selectedKB, setSelectedKB] = useState(null);
  const [docs, setDocs] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [uploading, setUploading] = useState(false);
  const navigate = useNavigate();

  const loadKBs = useCallback(async () => {
    try { const r = await listKBs(); setKBs(r.data); } catch {}
  }, []);

  const loadDocs = useCallback(async (kbId) => {
    if (!kbId) return;
    try { const r = await listDocs(kbId); setDocs(r.data); } catch {}
  }, []);

  useEffect(() => { loadKBs(); }, [loadKBs]);

  // 自动选中第一个
  useEffect(() => {
    if (kbs.length > 0 && !selectedKB) {
      setSelectedKB(kbs[0]);
    }
  }, [kbs, selectedKB]);

  useEffect(() => {
    if (selectedKB) { loadDocs(selectedKB.id); }
    else { setDocs([]); }
  }, [selectedKB, loadDocs]);

  // 轮询
  useEffect(() => {
    if (!selectedKB) return;
    const t = setInterval(() => loadDocs(selectedKB.id), 4000);
    return () => clearInterval(t);
  }, [selectedKB, loadDocs]);

  const handleSelectKB = (kb) => { setSelectedKB(kb); };

  const handleDeleteKB = async (e, id) => {
    e.stopPropagation();
    if (!confirm("删除知识库将同时删除所有文档，确定吗？")) return;
    await deleteKB(id);
    if (selectedKB?.id === id) setSelectedKB(null);
    loadKBs();
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedKB) return;
    setUploading(true);
    try { await uploadDoc(selectedKB.id, file); await loadDocs(selectedKB.id); } catch {}
    setUploading(false);
  };

  const handleDeleteDoc = async (id) => {
    if (!confirm("删除后无法恢复")) return;
    await deleteDoc(id);
    if (selectedKB) loadDocs(selectedKB.id);
  };

  const readyCount = docs.filter(d => d.status === "ready").length;

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* 顶栏 */}
      <header className="sticky top-0 bg-white/80 backdrop-blur-md border-b border-gray-100 z-40">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gray-900 text-white flex items-center justify-center text-sm font-bold">A</div>
            <span className="font-bold text-gray-900 text-lg tracking-tight">AI 知识库</span>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setShowCreate(true)}
              className="px-4 py-2 bg-gray-900 text-white text-sm font-semibold rounded-xl hover:bg-gray-800 transition-all shadow-sm">
              新建知识库
            </button>
            <button onClick={() => { localStorage.clear(); window.location.reload(); }}
              className="text-sm text-gray-400 hover:text-gray-600 transition-colors px-2">
              退出
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* KB 网格 */}
        {kbs.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-10">
            {kbs.map(kb => (
              <div key={kb.id}
                onClick={() => handleSelectKB(kb)}
                className={`bg-white rounded-2xl border-2 p-5 cursor-pointer transition-all ${
                  selectedKB?.id === kb.id
                    ? "border-gray-900 shadow-md"
                    : "border-gray-100 hover:border-gray-300 hover:shadow-sm"
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <span className="text-2xl">📚</span>
                  <button onClick={(e) => handleDeleteKB(e, kb.id)}
                    className="text-gray-300 hover:text-red-500 text-xs font-medium transition-colors">
                    删除
                  </button>
                </div>
                <h3 className="font-bold text-gray-900 text-sm">{kb.name}</h3>
                {kb.description && <p className="text-xs text-gray-400 mt-1 line-clamp-2">{kb.description}</p>}
                <p className="text-xs text-gray-400 mt-3">{kb.document_count} 个文档</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <p className="text-5xl mb-5">📚</p>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">创建你的第一个知识库</h2>
            <p className="text-gray-400 mb-8">上传文档，用 AI 进行智能问答</p>
            <button onClick={() => setShowCreate(true)}
              className="px-6 py-3 bg-gray-900 text-white rounded-xl text-sm font-semibold hover:bg-gray-800 transition-all shadow-sm">
              创建知识库
            </button>
          </div>
        )}

        {/* 选中知识库的详情 */}
        {selectedKB && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            {/* 头部 */}
            <div className="px-6 py-5 border-b border-gray-50 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-gray-900">{selectedKB.name}</h3>
                <p className="text-sm text-gray-400 mt-0.5">
                  {docs.length} 个文档 · {readyCount} 个就绪
                </p>
              </div>
              <div className="flex items-center gap-3">
                <label className={`inline-flex items-center gap-1.5 px-4 py-2 border-2 border-dashed rounded-xl cursor-pointer transition-all text-sm font-medium ${
                  uploading ? "border-gray-200 text-gray-300" : "border-gray-200 text-gray-600 hover:border-gray-400 hover:bg-gray-50"
                }`}>
                  {uploading ? "⏳ 上传中..." : "📤 上传文档"}
                  <input type="file" accept=".pdf,.docx,.doc,.txt,.md" onChange={handleUpload} disabled={uploading} className="hidden" />
                </label>
                <button onClick={() => navigate(`/kb/${selectedKB.id}/chat`)}
                  disabled={readyCount === 0}
                  className={`px-5 py-2 rounded-xl text-sm font-bold transition-all shadow-sm ${
                    readyCount > 0
                      ? "bg-gray-900 text-white hover:bg-gray-800"
                      : "bg-gray-100 text-gray-400 cursor-not-allowed"
                  }`}>
                  💬 开始对话
                </button>
              </div>
            </div>

            {/* 文档列表 */}
            <div className="p-4">
              {docs.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-3xl mb-2">📂</p>
                  <p className="text-gray-500 text-sm">还没有文档</p>
                  <p className="text-gray-400 text-xs mt-1">上传 PDF、Word、TXT 或 Markdown 文件</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-50">
                  {docs.map(doc => (
                    <DocRow key={doc.id} doc={doc} onDelete={handleDeleteDoc} />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <KBModal show={showCreate} onClose={() => setShowCreate(false)} onCreated={loadKBs} />
    </div>
  );
}
