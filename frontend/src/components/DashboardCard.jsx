import { Typography } from "@mui/material";
import MainLayout from "../../layouts/MainLayout";

export default function Dashboard() {
  return (
    <MainLayout>
      <Typography variant="h4" fontWeight="bold">
        Dashboard
      </Typography>

      <Typography sx={{ mt: 2 }}>
        Welcome to the Enterprise EV Fleet Data Platform 
      </Typography>
    </MainLayout>
  );
}