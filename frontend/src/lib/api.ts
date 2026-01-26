import axios from "axios";

const API_URL = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      const errorData = error.response.data;
      // FastAPI returns errors in 'detail' field, but our endpoints use 'error' field
      const message = errorData?.error || errorData?.detail || error.response.statusText || "An error occurred";
      throw new Error(message);
    } else if (error.request) {
      // Request made but no response
      throw new Error("Network error. Please check your connection.");
    } else {
      // Something else happened
      throw new Error(error.message || "An unexpected error occurred");
    }
  }
);

export default api;
