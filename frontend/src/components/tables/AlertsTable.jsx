import { useEffect, useState } from "react";
import {
  Paper,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
} from "@mui/material";

import api from "../../services/api";

export default function AlertsTable() {
  const [alerts, setAlerts] = useState([]);

  const fetchAlerts = () => {
    api
      .get("/alerts/")
      .then((res) => setAlerts(res.data))
      .catch((err) => console.error(err));
  };

  useEffect(() => {
    fetchAlerts();

    const interval = setInterval(fetchAlerts, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        🚨 Live Alerts
      </Typography>

      <Table>
        <TableHead>
          <TableRow>
            <TableCell><b>Vehicle</b></TableCell>
            <TableCell><b>Alert</b></TableCell>
            <TableCell><b>Severity</b></TableCell>
            <TableCell><b>Message</b></TableCell>
            <TableCell><b>Time</b></TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {alerts.map((alert) => (
            <TableRow key={alert.id}>
              <TableCell>{alert.vehicle_id}</TableCell>

              <TableCell>{alert.alert_type}</TableCell>

              <TableCell>
                <Chip
                  label={alert.severity}
                  color={
                    alert.severity === "Critical"
                      ? "error"
                      : alert.severity === "High"
                      ? "warning"
                      : "info"
                  }
                />
              </TableCell>

              <TableCell>{alert.message}</TableCell>

              <TableCell>
                {new Date(alert.timestamp).toLocaleString()}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
}