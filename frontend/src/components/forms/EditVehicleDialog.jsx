import { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Snackbar,
  Alert,
} from "@mui/material";

import api from "../../services/api";
import { useVehicle } from "../../context/VehicleContext";

export default function EditVehicleDialog({
  open,
  handleClose,
  vehicle,
}) {
  const { fetchVehicles } = useVehicle();

  const [formData, setFormData] = useState({
    battery: "",
    speed: "",
    status: "",
  });

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  useEffect(() => {
    if (vehicle) {
      setFormData({
        battery: vehicle.battery,
        speed: vehicle.speed,
        status: vehicle.status,
      });
    }
  }, [vehicle]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSave = async () => {
    try {
      await api.put(`/vehicles/${vehicle.id}`, {
        battery: Number(formData.battery),
        speed: Number(formData.speed),
        status: formData.status,
      });

      fetchVehicles();

      setSnackbar({
        open: true,
        message: "Vehicle updated successfully!",
        severity: "success",
      });

      handleClose();
    } catch (err) {
      console.error(err);

      setSnackbar({
        open: true,
        message: "Failed to update vehicle.",
        severity: "error",
      });
    }
  };

  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth>
        <DialogTitle>Edit Vehicle</DialogTitle>

        <DialogContent>
          <TextField
            fullWidth
            margin="normal"
            label="Battery"
            name="battery"
            type="number"
            value={formData.battery}
            onChange={handleChange}
          />

          <TextField
            fullWidth
            margin="normal"
            label="Speed"
            name="speed"
            type="number"
            value={formData.speed}
            onChange={handleChange}
          />

          <TextField
            select
            fullWidth
            margin="normal"
            label="Status"
            name="status"
            value={formData.status}
            onChange={handleChange}
          >
            <MenuItem value="Running">Running</MenuItem>
            <MenuItem value="Charging">Charging</MenuItem>
            <MenuItem value="Low Battery">Low Battery</MenuItem>
          </TextField>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose}>
            Cancel
          </Button>

          <Button
            variant="contained"
            onClick={handleSave}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

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
    </>
  );
}