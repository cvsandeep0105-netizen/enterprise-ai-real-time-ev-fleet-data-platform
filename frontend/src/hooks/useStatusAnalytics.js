import { useEffect, useState } from "react";
import api from "../services/api";

export default function useStatusAnalytics() {
  const [statusData, setStatusData] = useState([]);

  const fetchStatusData = async () => {
    try {
      const response = await api.get("/analytics/status");
      setStatusData(response.data);
    } catch (err) {
      console.error("Status analytics error:", err);
    }
  };

  useEffect(() => {
    fetchStatusData();

    const interval = setInterval(() => {
      fetchStatusData();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return {
    statusData,
    fetchStatusData,
  };
}