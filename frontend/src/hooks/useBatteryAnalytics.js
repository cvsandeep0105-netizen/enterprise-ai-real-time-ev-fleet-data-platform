import { useEffect, useState } from "react";
import api from "../services/api";

export default function useBatteryAnalytics() {
  const [batteryData, setBatteryData] = useState([]);

  const fetchBatteryData = async () => {
    try {
      const response = await api.get("/analytics/battery");
      setBatteryData(response.data);
    } catch (err) {
      console.error("Battery analytics error:", err);
    }
  };

  useEffect(() => {
    fetchBatteryData();

    const interval = setInterval(() => {
      fetchBatteryData();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return {
    batteryData,
    fetchBatteryData,
  };
}