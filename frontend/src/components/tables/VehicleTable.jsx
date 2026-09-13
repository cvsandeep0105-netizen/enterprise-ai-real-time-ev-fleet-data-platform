import {
  Paper,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TextField,
  MenuItem,
  CircularProgress,
  Box,
  Chip,
} from "@mui/material";

import { useState } from "react";
import { useVehicle } from "../../context/VehicleContext";

export default function VehicleTable() {
  const { vehicles, loading } = useVehicle();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  const filteredVehicles = vehicles.filter((vehicle) => {
    const matchesSearch = vehicle.vehicle_id
      ?.toLowerCase()
      .includes(search.toLowerCase());

    const status = vehicle.vehicle_status || "";

    const matchesStatus =
      statusFilter === "All" ||
      status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="300px"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 3, overflowX: "auto" }}>
      <Typography variant="h6" gutterBottom>
        Live Vehicle Telemetry
      </Typography>

      <TextField
        fullWidth
        label="Search Vehicle ID"
        variant="outlined"
        margin="normal"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <TextField
        select
        fullWidth
        label="Filter by Status"
        margin="normal"
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value)}
      >
        <MenuItem value="All">All</MenuItem>
        <MenuItem value="MOVING">Moving</MenuItem>
        <MenuItem value="STOPPED">Stopped</MenuItem>
      </TextField>

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell><b>Vehicle</b></TableCell>
            <TableCell><b>Battery</b></TableCell>
            <TableCell><b>Speed</b></TableCell>
            <TableCell><b>Status</b></TableCell>
            <TableCell><b>Charging</b></TableCell>
            <TableCell><b>Temperature</b></TableCell>
            <TableCell><b>Location</b></TableCell>
            <TableCell><b>Last Update</b></TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {filteredVehicles.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} align="center">
                No vehicles available.
              </TableCell>
            </TableRow>
          ) : (
            filteredVehicles.map((vehicle) => (
              <TableRow key={vehicle.vehicle_id}>
                <TableCell>
                  <b>{vehicle.vehicle_id}</b>
                </TableCell>

                <TableCell>
                  {vehicle.battery}%
                </TableCell>

                <TableCell>
                  {vehicle.speed} km/h
                </TableCell>

                <TableCell>
                  <Chip
                    label={vehicle.vehicle_status || "UNKNOWN"}
                    size="small"
                  />
                </TableCell>

                <TableCell>
                  <Chip
                    label={vehicle.charging_status || "UNKNOWN"}
                    size="small"
                  />
                </TableCell>

                <TableCell>
                  {vehicle.temperature_status || "UNKNOWN"}
                </TableCell>

                <TableCell>
                  {vehicle.location || "N/A"}
                </TableCell>

                <TableCell>
                  {vehicle.timestamp
                    ? new Date(vehicle.timestamp).toLocaleString()
                    : "N/A"}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Paper>
  );
}