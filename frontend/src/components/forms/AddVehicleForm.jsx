import { useState } from "react";
import {
  Box,
  Button,
  MenuItem,
  TextField,
  Typography,
  Snackbar,
  Alert,
} from "@mui/material";

import api from "../../services/api";
import { useVehicle } from "../../context/VehicleContext";

export default function AddVehicleForm() {
  const { fetchVehicles } = useVehicle();

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  const [vehicle, setVehicle] = useState({
    vehicle_id: "",
    battery: "",
    speed: "",
    status: "Running",
  });

  const handleChange = (e) => {
    setVehicle({
      ...vehicle,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async () => {
    try {
      await api.post("/vehicles", {
        vehicle_id: vehicle.vehicle_id,
        battery: Number(vehicle.battery),
        speed: Number(vehicle.speed),
        status: vehicle.status,
      });

      setSnackbar({
        open: true,
        message: "Vehicle added successfully!",
        severity: "success",
      });

      fetchVehicles();

      setVehicle({
        vehicle_id: "",
        battery: "",
        speed: "",
        status: "Running",
      });

    } catch (err) {
      console.error(err);

      setSnackbar({
        open: true,
        message: "Failed to add vehicle.",
        severity: "error",
      });
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" mb={2}>
        Add Vehicle
      </Typography>

      <TextField
        fullWidth
        margin="normal"
        label="Vehicle ID"
        name="vehicle_id"
        value={vehicle.vehicle_id}
        onChange={handleChange}
      />

      <TextField
        fullWidth
        margin="normal"
        label="Battery"
        name="battery"
        type="number"
        value={vehicle.battery}
        onChange={handleChange}
      />

      <TextField
        fullWidth
        margin="normal"
        label="Speed"
        name="speed"
        type="number"
        value={vehicle.speed}
        onChange={handleChange}
      />

      <TextField
        select
        fullWidth
        margin="normal"
        label="Status"
        name="status"
        value={vehicle.status}
        onChange={handleChange}
      >
        <MenuItem value="Running">Running</MenuItem>
        <MenuItem value="Charging">Charging</MenuItem>
        <MenuItem value="Low Battery">Low Battery</MenuItem>
      </TextField>

      <Button
        variant="contained"
        sx={{ mt: 2 }}
        onClick={handleSubmit}
      >
        Add Vehicle
      </Button>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() =>
          setSnackbar({ ...snackbar, open: false })
        }
      >
        <Alert
          severity={snackbar.severity}
          onClose={() =>
            setSnackbar({ ...snackbar, open: false })
          }
          sx={{ width: "100%" }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}