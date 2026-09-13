import { useEffect, useState } from "react";
import api from "../services/api";

export default function useVehicles() {
  const [vehicles, setVehicles] = useState([]);

  const fetchVehicles = () => {
    api
      .get("/vehicles")
      .then((res) => setVehicles(res.data))
      .catch((err) => console.error(err));
  };

  useEffect(() => {
    fetchVehicles();
  }, []);

  return {
    vehicles,
    fetchVehicles,
  };
}