import axios from "axios";

// Dynamically match localhost or 127.0.0.1 based on current browser URL
// to prevent cross-origin cookie loss
const hostname =
  typeof window !== "undefined" && window.location.hostname
    ? window.location.hostname
    : "localhost";

const api = axios.create({
  baseURL: `http://${hostname}:8000`,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

export default api;