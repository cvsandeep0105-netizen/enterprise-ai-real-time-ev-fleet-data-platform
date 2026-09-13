import { Paper, Typography } from "@mui/material";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";

import useStatusAnalytics from "../../hooks/useStatusAnalytics";

const COLORS = [
  "#4caf50",
  "#ff9800",
  "#f44336",
  "#2196f3",
];

export default function VehicleStatusChart() {
  const { statusData, fetchStatusData } = useStatusAnalytics();
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Vehicle Status
      </Typography>

      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            data={statusData}
            dataKey="count"
            nameKey="status"
            outerRadius={120}
            label
          >
            {statusData.map((entry, index) => (
              <Cell
                key={index}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>

          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Paper>
  );
}