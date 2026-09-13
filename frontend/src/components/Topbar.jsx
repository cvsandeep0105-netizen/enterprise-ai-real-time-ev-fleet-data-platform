import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Avatar,
  Box,
} from "@mui/material";

import NotificationsIcon from "@mui/icons-material/Notifications";
import DarkModeIcon from "@mui/icons-material/DarkMode";

export default function Topbar() {
  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        <Typography
          variant="h6"
          sx={{
            flexGrow: 1,
            fontWeight: "bold",
          }}
        >
          ⚡ EV Fleet Data Platform
        </Typography>

        <IconButton color="inherit">
          <NotificationsIcon />
        </IconButton>

        <IconButton color="inherit">
          <DarkModeIcon />
        </IconButton>

        <Box sx={{ ml: 2 }}>
          <Avatar>S</Avatar>
        </Box>
      </Toolbar>
    </AppBar>
  );
}