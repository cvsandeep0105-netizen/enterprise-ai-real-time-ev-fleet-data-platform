import { Paper, Typography, Box } from "@mui/material";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import { useVehicle } from "../../context/VehicleContext";

export default function FleetPerformanceChart() {
  const { vehicles, loading } = useVehicle();

  const chartData = vehicles.map((vehicle) => ({
    name: vehicle.vehicle_id,
    speed: Number(vehicle.speed) || 0,
  }));

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Fleet Performance
      </Typography>

      {loading ? (
        <Box
          sx={{
            height: 300,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          Loading fleet performance...
        </Box>
      ) : chartData.length === 0 ? (
        <Box
          sx={{
            height: 300,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          No vehicle data available.
        </Box>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={chartData}
            margin={{
              top: 10,
              right: 30,
              left: 10,
              bottom: 20,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis
              dataKey="name"
              tick={{ fontSize: 12 }}
            />

            <YAxis
              domain={[0, 120]}
              label={{
                value: "Speed (km/h)",
                angle: -90,
                position: "insideLeft",
              }}
            />

            <Tooltip
              formatter={(value) => [`${value} km/h`, "Speed"]}
            />

            <Line
              type="monotone"
              dataKey="speed"
              stroke="#1976d2"
              strokeWidth={3}
              dot={{ r: 5 }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Paper>
  );
}