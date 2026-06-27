import axios from "axios";

const API_BASE = "/api";

const api = axios.create({ baseURL: API_BASE, headers: { "Content-Type": "application/json" } });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const register = (u, p, e) => api.post("/auth/register/", { username: u, password: p, email: e });
export const login = (u, p) => api.post("/auth/login/", { username: u, password: p });
export const getMe = () => api.get("/auth/me/");

export const listKBs = () => api.get("/knowledge-bases/");
export const createKB = (data) => api.post("/knowledge-bases/", data);
export const getKB = (id) => api.get(`/knowledge-bases/${id}/`);
export const deleteKB = (id) => api.delete(`/knowledge-bases/${id}/`);

export const listDocs = (kbId) => api.get(`/knowledge-bases/${kbId}/documents/`);
export const uploadDoc = (kbId, file) => {
  const form = new FormData(); form.append("file", file);
  return api.post(`/knowledge-bases/${kbId}/documents/`, form, { headers: { "Content-Type": "multipart/form-data" } });
};
export const deleteDoc = (docId) => api.delete(`/documents/${docId}/`);

export const listConvs = (kbId) => api.get(`/knowledge-bases/${kbId}/conversations/`);
export const getConv = (convId) => api.get(`/conversations/${convId}/`);
export const deleteConv = (convId) => api.delete(`/conversations/${convId}/`);
export const getMessages = (convId) => api.get(`/conversations/${convId}/messages/`);
export const saveAssistantMessage = (convId, content, sources) =>
  api.post(`/conversations/${convId}/save-message/`, { role: "assistant", content, sources });

const sse = (path, message) =>
  fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("access_token")}` },
    body: JSON.stringify({ message }),
  });
export const newChat = (kbId, msg) => sse(`/knowledge-bases/${kbId}/chat/`, msg);
export const continueChat = (convId, msg) => sse(`/conversations/${convId}/chat/`, msg);

export default api;
