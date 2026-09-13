import { Paper, Typography } from "@mui/material";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import useBatteryAnalytics from "../../hooks/useBatteryAnalytics";

export default function BatteryHealthChart() {
  const { batteryData, fetchBatteryData } = useBatteryAnalytics();

  const chartData = batteryData.map((vehicle) => ({
    name: vehicle.vehicle_id,
    battery: vehicle.battery,
  }));

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Battery Health
      </Typography>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Bar dataKey="battery" fill="#4caf50" />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
}