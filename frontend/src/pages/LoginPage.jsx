import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { login, register } from "../api/client";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { loginUser } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isRegister) {
        await register(username, password, email);
        const res = await login(username, password);
        await loginUser(res.data.access, res.data.refresh);
      } else {
        const res = await login(username, password);
        await loginUser(res.data.access, res.data.refresh);
      }
      navigate("/");
    } catch (err) {
      const msg = err.response?.data;
      if (msg && typeof msg === "object") {
        setError(Object.values(msg).flat().join("；"));
      } else {
        setError(msg?.detail || "操作失败");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-gradient-to-b from-white to-gray-50">
      {/* Logo */}
      <div className="w-12 h-12 rounded-xl bg-gray-900 text-white flex items-center justify-center text-xl font-bold mb-6 shadow-lg shadow-gray-900/10">
        A
      </div>
      <h1 className="text-2xl font-bold text-gray-900 tracking-tight mb-8">
        {isRegister ? "创建账号" : "欢迎回来"}
      </h1>

      {/* 卡片 */}
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        {error && (
          <div className="mb-6 px-4 py-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm outline-none focus:bg-white focus:border-gray-400 focus:ring-2 focus:ring-gray-100 transition-all"
              placeholder="你的用户名"
              required
            />
          </div>

          {isRegister && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">邮箱</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm outline-none focus:bg-white focus:border-gray-400 focus:ring-2 focus:ring-gray-100 transition-all"
                placeholder="you@example.com"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm outline-none focus:bg-white focus:border-gray-400 focus:ring-2 focus:ring-gray-100 transition-all"
              placeholder="至少 6 位"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 text-white text-sm font-semibold rounded-xl transition-all shadow-sm"
          >
            {loading ? "请稍候..." : isRegister ? "注册" : "登录"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <span className="text-sm text-gray-400">
            {isRegister ? "已有账号？" : "没有账号？"}
          </span>
          <button
            onClick={() => { setIsRegister(!isRegister); setError(""); }}
            className="ml-1 text-sm font-semibold text-gray-900 hover:underline"
          >
            {isRegister ? "去登录" : "免费注册"}
          </button>
        </div>
      </div>

      <p className="mt-8 text-xs text-gray-400">
        🔒 数据隔离 · 安全可靠
      </p>
    </div>
  );
}
