import axios from "axios";

// Single axios instance so base URL + error handling live in one place.
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  timeout: 10_000,
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    // Centralized place to log/report API failures as the app grows.
    console.error("CareCompass API error:", error?.response?.data || error.message);
    return Promise.reject(error);
  }
);
