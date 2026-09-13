import { Card, CardContent, Typography } from "@mui/material";

export default function StatsCard({
  title,
  value,
  color = "#1976d2",
}) {
  return (
    <Card
      sx={{
        borderLeft: `6px solid ${color}`,
        borderRadius: 3,
        boxShadow: 3,
      }}
    >
      <CardContent>
        <Typography
          variant="body2"
          color="text.secondary"
        >
          {title}
        </Typography>

        <Typography
          variant="h4"
          fontWeight="bold"
          sx={{ mt: 1 }}
        >
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}