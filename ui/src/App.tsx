import { AppBar, Box, Breadcrumbs, Button, Container, Link, Toolbar, Typography } from "@mui/material";
import { Link as RouterLink, NavLink, Route, Routes, matchPath, useLocation } from "react-router-dom";

import { ConfigPage } from "./pages/ConfigPage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { JobsPage } from "./pages/JobsPage";
import { NewRunPage } from "./pages/NewRunPage";
import { SessionsPage } from "./pages/SessionsPage";

interface BreadcrumbEntry {
  label: string;
  to?: string;
}

function buildBreadcrumbs(pathname: string): BreadcrumbEntry[] {
  const jobMatch = matchPath("/jobs/:jobId", pathname);
  if (jobMatch?.params.jobId) {
    return [
      { label: "Jobs", to: "/jobs" },
      { label: `Job ${jobMatch.params.jobId}` },
    ];
  }

  if (pathname === "/") {
    return [{ label: "New Run" }];
  }
  if (pathname === "/config") {
    return [{ label: "Configuration" }];
  }
  if (pathname === "/jobs") {
    return [{ label: "Jobs" }];
  }
  if (pathname === "/sessions") {
    return [{ label: "Sessions" }];
  }

  return [];
}

export default function App() {
  const location = useLocation();
  const breadcrumbs = buildBreadcrumbs(location.pathname);
  const currentContext = breadcrumbs.length > 0 ? breadcrumbs[breadcrumbs.length - 1].label : "Control Room";

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
    <Box sx={{ minHeight: "100vh", position: "relative" }}>
      <Link
        href="#main-content"
        underline="none"
        sx={{
          position: "absolute",
          left: 16,
          top: 8,
          zIndex: (theme) => theme.zIndex.tooltip + 1,
          px: 1.5,
          py: 0.75,
          borderRadius: 1.5,
          border: 1,
          borderColor: "divider",
          backgroundColor: "background.paper",
          color: "text.primary",
          fontWeight: 600,
          transform: "translateY(-180%)",
          transition: "transform 140ms ease",
          "&:focus, &:focus-visible": {
            transform: "translateY(0)",
            boxShadow: "var(--ds-focus-ring)",
          },
        }}
      >
        Skip to main content
      </Link>
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

      <Box component="main" id="main-content" tabIndex={-1}>
        <Container maxWidth="lg" sx={{ pb: 5 }}>
          <Box
            role="navigation"
            aria-label="Current view"
            sx={{ pt: 2, pb: 1.5, display: "grid", gap: 0.5 }}
          >
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: 0.8 }}>
              Current View
            </Typography>
            {breadcrumbs.length > 1 ? (
              <Breadcrumbs aria-label="Route breadcrumbs">
                {breadcrumbs.map((breadcrumb, index) =>
                  breadcrumb.to ? (
                    <Link
                      key={`${breadcrumb.label}-${index}`}
                      component={RouterLink}
                      to={breadcrumb.to}
                      underline="hover"
                      color="inherit"
                    >
                      {breadcrumb.label}
                    </Link>
                  ) : (
                    <Typography key={`${breadcrumb.label}-${index}`} color="text.primary" fontWeight={600}>
                      {breadcrumb.label}
                    </Typography>
                  )
                )}
              </Breadcrumbs>
            ) : (
              <Typography variant="body2" color="text.primary" fontWeight={600}>
                {currentContext}
              </Typography>
            )}
          </Box>
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
