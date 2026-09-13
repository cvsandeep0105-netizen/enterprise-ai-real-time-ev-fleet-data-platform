import { useEffect, useState } from "react";
import api from "../services/api";

export default function useDashboardSummary() {
  const [summary, setSummary] = useState({
    total_vehicles: 0,
    running: 0,
    charging: 0,
    low_battery: 0,
    average_battery: 0,
    average_speed: 0,
  });

  const fetchSummary = async () => {
    try {
      const response = await api.get("/dashboard/summary");
      setSummary(response.data);
    } catch (error) {
      console.error("Dashboard summary error:", error);
    }
  };

  useEffect(() => {
    fetchSummary();

    const interval = setInterval(() => {
      fetchSummary();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return {
    summary,
    fetchSummary,
  };
}