import { Grid, Typography } from "@mui/material";

import MainLayout from "../../layouts/MainLayout";
import StatsCard from "../../components/cards/StatsCard";
import FleetPerformanceChart from "../../components/charts/FleetPerformanceChart";
import BatteryHealthChart from "../../components/charts/BatteryHealthChart";
import VehicleStatusChart from "../../components/charts/VehicleStatusChart";
import VehicleTable from "../../components/tables/VehicleTable";
import AlertsTable from "../../components/tables/AlertsTable";
import AddVehicleForm from "../../components/forms/AddVehicleForm";

import useDashboardSummary from "../../hooks/useDashboardSummary";

export default function Dashboard() {
  const { summary, fetchSummary } = useDashboardSummary();

  return (
    <MainLayout>
      <Typography variant="h4" fontWeight="bold" mb={3}>
        EV Fleet Dashboard
      </Typography>

      {/* KPI Cards */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard
            title="Total Vehicles"
            value={summary.total_vehicles}
            color="#1976d2"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard
            title="Active Vehicles"
            value={summary.running}
            color="#4caf50"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard
            title="Charging"
            value={summary.charging}
            color="#ff9800"
          />
        </Grid>

        <Grid size={{ xs: 12, md: 3 }}>
          <StatsCard
            title="Active Alerts"
            value={summary.active_alerts}
            color="#f44336"
          />
        </Grid>
      </Grid>

      {/* Fleet Performance */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12 }}>
          <FleetPerformanceChart />
        </Grid>
      </Grid>

      {/* Battery Health & Vehicle Status */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <BatteryHealthChart />
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <VehicleStatusChart />
        </Grid>
      </Grid>

      {/* Vehicle Table */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12 }}>
          <VehicleTable />
        </Grid>
      </Grid>

      {/* Add Vehicle Form */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12 }}>
          <AddVehicleForm />
        </Grid>
      </Grid>

      {/* Live Alerts */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12 }}>
          <AlertsTable />
        </Grid>
      </Grid>
    </MainLayout>
  );
}