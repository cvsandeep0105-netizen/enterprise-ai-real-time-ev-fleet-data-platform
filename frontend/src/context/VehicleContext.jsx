import { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api";

const VehicleContext = createContext();

export function VehicleProvider({ children }) {
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchVehicles = async () => {
    try {
      const response = await api.get("/vehicles");
      setVehicles(response.data);
    } catch (err) {
      console.error("Vehicle fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial load
    fetchVehicles();

    // Refresh every 5 seconds
    const interval = setInterval(() => {
      fetchVehicles();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <VehicleContext.Provider
      value={{
        vehicles,
        loading,
        fetchVehicles,
      }}
    >
      {children}
    </VehicleContext.Provider>
  );
}

export function useVehicle() {
  return useContext(VehicleContext);
}