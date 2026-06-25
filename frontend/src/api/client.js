import axios from "axios";

const API_BASE = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (username, password, email) =>
  api.post("/auth/register/", { username, password, email });

export const login = (username, password) =>
  api.post("/auth/login/", { username, password });

export const getMe = () => api.get("/auth/me/");

// Knowledge Bases
export const listKBs = () => api.get("/knowledge-bases/");
export const createKB = (data) => api.post("/knowledge-bases/", data);
export const getKB = (id) => api.get(`/knowledge-bases/${id}/`);
export const updateKB = (id, data) => api.put(`/knowledge-bases/${id}/`, data);
export const deleteKB = (id) => api.delete(`/knowledge-bases/${id}/`);

// Documents
export const listDocs = (kbId) =>
  api.get(`/knowledge-bases/${kbId}/documents/`);
export const uploadDoc = (kbId, file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post(`/knowledge-bases/${kbId}/documents/`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
export const deleteDoc = (docId) => api.delete(`/documents/${docId}/`);

// Conversations
export const listConvs = (kbId) =>
  api.get(`/knowledge-bases/${kbId}/conversations/`);
export const getConv = (convId) => api.get(`/conversations/${convId}/`);
export const deleteConv = (convId) => api.delete(`/conversations/${convId}/`);
export const getMessages = (convId) =>
  api.get(`/conversations/${convId}/messages/`);
export const saveAssistantMessage = (convId, content, sources) =>
  api.post(`/conversations/${convId}/save-message/`, {
    role: "assistant",
    content,
    sources,
  });

// Chat (SSE)
export const newChat = (kbId, message) => {
  const token = localStorage.getItem("access_token");
  return fetch(`${API_BASE}/knowledge-bases/${kbId}/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  });
};

export const continueChat = (convId, message) => {
  const token = localStorage.getItem("access_token");
  return fetch(`${API_BASE}/conversations/${convId}/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  });
};

export default api;
