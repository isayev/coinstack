import axios from "axios";

const API_URL = (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";

const api = axios.create({
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
      let message = error.response.data?.detail || error.response.data?.error || "An error occurred";
      if (typeof message === 'object') {
        message = JSON.stringify(message);
      }
      const err = new Error(message);
      (err as any).response = error.response; // Attach response for debugging
      throw err;
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
