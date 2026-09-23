import axios from "axios";

const api = axios.create({
  baseURL: "http://12.0.0.1:8000",
  withCredentials: true,
});

export default api;