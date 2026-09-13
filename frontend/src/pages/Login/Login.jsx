import { useNavigate } from "react-router-dom";
import { Box, Paper, Typography, TextField, Button } from "@mui/material";

export default function Login() {
 
    const navigate = useNavigate();
   return ( 
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        bgcolor: "f5f7fb",
       
      }}
    >
      <Paper elevation={6} sx={{ p: 5, width: 400, borderRadius: 3 }}>
        <Typography variant="h4" align="center" gutterBottom>
          EV Fleet Platform
        </Typography>

        <Typography align="center" sx={{ mb: 3 }}>
          Login to continue
        </Typography>

        <TextField
          fullWidth
          label="Email"
          margin="normal"
        />

        <TextField
          fullWidth
          type="password"
          label="Password"
          margin="normal"
        />

        <Button
         fullWidth
         variant="contained"
         sx={{ mt: 3 }}
         onClick={() => navigate("/dashboard")}
         >
         LOGIN
        </Button>
      </Paper>
    </Box>
  );
}