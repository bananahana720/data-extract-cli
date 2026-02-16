import { AppBar, Box, Button, Container, Toolbar, Typography } from "@mui/material";
import { NavLink, Route, Routes } from "react-router-dom";

import { ConfigPage } from "./pages/ConfigPage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { JobsPage } from "./pages/JobsPage";
import { NewRunPage } from "./pages/NewRunPage";
import { SessionsPage } from "./pages/SessionsPage";

export default function App() {
  const navLinkSx = {
    borderRadius: 999,
    border: 1,
    borderColor: "divider",
    px: 2,
    py: 0.75,
    textTransform: "none",
    color: "text.primary",
    backgroundColor: "background.paper",
    fontWeight: 600,
    "&.active": {
      borderColor: "text.primary",
      backgroundColor: "text.primary",
      color: "common.white",
    },
  };

  return (
    <Box sx={{ minHeight: "100vh" }}>
      <AppBar
        position="static"
        color="transparent"
        elevation={0}
        sx={{ backgroundColor: "transparent", pt: { xs: 2, md: 2.5 } }}
      >
        <Container maxWidth="lg">
          <Toolbar
            disableGutters
            sx={{
              alignItems: { xs: "flex-start", md: "flex-end" },
              justifyContent: "space-between",
              gap: 2,
              flexWrap: "wrap",
            }}
          >
            <Box>
              <Typography
                component="p"
                variant="overline"
                sx={{ color: "text.secondary", letterSpacing: "0.14em", lineHeight: 1.2 }}
              >
                Local Analyst Workspace
              </Typography>
              <Typography component="h1" variant="h4" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
                Data Extract Control Room
              </Typography>
            </Box>
            <Box component="nav" aria-label="Primary navigation" sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              <Button component={NavLink} to="/" end sx={navLinkSx}>
                New Run
              </Button>
              <Button component={NavLink} to="/config" sx={navLinkSx}>
                Config
              </Button>
              <Button component={NavLink} to="/jobs" sx={navLinkSx}>
                Jobs
              </Button>
              <Button component={NavLink} to="/sessions" sx={navLinkSx}>
                Sessions
              </Button>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      <Box component="main">
        <Container maxWidth="lg" sx={{ pb: 5 }}>
          <Routes>
            <Route path="/" element={<NewRunPage />} />
            <Route path="/config" element={<ConfigPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/jobs/:jobId" element={<JobDetailPage />} />
            <Route path="/sessions" element={<SessionsPage />} />
          </Routes>
        </Container>
      </Box>
    </Box>
  );
}
