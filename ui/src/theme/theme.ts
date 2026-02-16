import { alpha, createTheme } from "@mui/material/styles";

import {
  breakpointTokens,
  colorTokens,
  elevationTokens,
  shapeTokens,
  spacingTokens,
  typographyTokens,
} from "./tokens";

const focusRing = {
  outline: `3px solid ${alpha(colorTokens.brand.accent, 0.45)}`,
  outlineOffset: 2,
} as const;

export const appTheme = createTheme({
  breakpoints: {
    values: breakpointTokens,
  },
  palette: {
    mode: "light",
    primary: {
      main: colorTokens.brand.deepNavy,
      dark: "#07151E",
      light: "#203644",
      contrastText: colorTokens.text.inverse,
    },
    secondary: {
      main: colorTokens.brand.accent,
      dark: colorTokens.brand.accentStrong,
      light: "#7ACCF8",
      contrastText: colorTokens.brand.deepNavy,
    },
    background: {
      default: colorTokens.surface.canvas,
      paper: colorTokens.surface.elevated,
    },
    text: {
      primary: colorTokens.text.primary,
      secondary: colorTokens.text.secondary,
    },
    divider: colorTokens.border.subtle,
    info: {
      main: colorTokens.brand.accent,
      light: colorTokens.status.info.background,
      dark: colorTokens.status.info.foreground,
      contrastText: colorTokens.text.inverse,
    },
    success: {
      main: "#1E8E5A",
      light: colorTokens.status.success.background,
      dark: colorTokens.status.success.foreground,
      contrastText: colorTokens.text.inverse,
    },
    warning: {
      main: "#B26A08",
      light: colorTokens.status.warning.background,
      dark: colorTokens.status.warning.foreground,
      contrastText: colorTokens.text.primary,
    },
    error: {
      main: "#CF3C4A",
      light: colorTokens.status.error.background,
      dark: colorTokens.status.error.foreground,
      contrastText: colorTokens.text.inverse,
    },
  },
  typography: {
    fontFamily: typographyTokens.fontFamily.sans,
    h1: {
      fontSize: typographyTokens.fontSize["2xl"],
      fontWeight: typographyTokens.fontWeight.bold,
      lineHeight: typographyTokens.lineHeight.tight,
      letterSpacing: typographyTokens.letterSpacing.wide,
    },
    h2: {
      fontSize: typographyTokens.fontSize.xl,
      fontWeight: typographyTokens.fontWeight.bold,
      lineHeight: typographyTokens.lineHeight.tight,
    },
    h3: {
      fontSize: typographyTokens.fontSize.lg,
      fontWeight: typographyTokens.fontWeight.semibold,
      lineHeight: typographyTokens.lineHeight.tight,
    },
    h4: {
      fontSize: typographyTokens.fontSize.md,
      fontWeight: typographyTokens.fontWeight.semibold,
      lineHeight: typographyTokens.lineHeight.normal,
    },
    body1: {
      fontSize: typographyTokens.fontSize.md,
      lineHeight: typographyTokens.lineHeight.normal,
    },
    body2: {
      fontSize: typographyTokens.fontSize.sm,
      lineHeight: typographyTokens.lineHeight.normal,
    },
    overline: {
      fontSize: typographyTokens.fontSize.xs,
      fontWeight: typographyTokens.fontWeight.semibold,
      letterSpacing: typographyTokens.letterSpacing.caps,
      textTransform: "uppercase",
      lineHeight: typographyTokens.lineHeight.normal,
    },
    button: {
      fontWeight: typographyTokens.fontWeight.semibold,
      letterSpacing: typographyTokens.letterSpacing.wide,
      textTransform: "none",
    },
  },
  shape: {
    borderRadius: shapeTokens.radius.md,
  },
  components: {
    MuiTypography: {
      defaultProps: {
        variantMapping: {
          h1: "h1",
          h2: "h2",
          h3: "h3",
          h4: "h4",
          h5: "h5",
          h6: "h6",
          subtitle1: "p",
          subtitle2: "p",
          body1: "p",
          body2: "p",
          inherit: "p",
        },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        "*, *::before, *::after": {
          boxSizing: "border-box",
        },
        body: {
          fontFamily: typographyTokens.fontFamily.sans,
          backgroundColor: colorTokens.surface.canvas,
          color: colorTokens.text.primary,
        },
        ":focus-visible": focusRing,
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          minHeight: 40,
          borderRadius: shapeTokens.radius.pill,
          paddingInline: spacingTokens.md,
          "&.Mui-focusVisible": focusRing,
        },
        containedPrimary: {
          backgroundColor: colorTokens.brand.deepNavy,
          "&:hover": {
            backgroundColor: alpha(colorTokens.brand.deepNavy, 0.9),
          },
        },
        outlined: {
          borderColor: colorTokens.border.strong,
          "&:hover": {
            borderColor: colorTokens.brand.deepNavy,
            backgroundColor: colorTokens.surface.muted,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: shapeTokens.radius.lg,
          border: `1px solid ${theme.palette.divider}`,
          boxShadow: "none",
          backgroundImage: "none",
        }),
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: ({ theme }) => ({
          backgroundImage: "none",
          borderColor: theme.palette.divider,
        }),
        rounded: {
          borderRadius: shapeTokens.radius.lg,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: ({ theme }) => ({
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: shapeTokens.radius.md,
          alignItems: "flex-start",
          "& .MuiAlert-message": {
            width: "100%",
          },
          "& .MuiAlert-icon": {
            marginTop: 2,
          },
        }),
        standardInfo: {
          backgroundColor: colorTokens.status.info.background,
          color: colorTokens.status.info.foreground,
          borderColor: colorTokens.status.info.border,
        },
        standardSuccess: {
          backgroundColor: colorTokens.status.success.background,
          color: colorTokens.status.success.foreground,
          borderColor: colorTokens.status.success.border,
        },
        standardWarning: {
          backgroundColor: colorTokens.status.warning.background,
          color: colorTokens.status.warning.foreground,
          borderColor: colorTokens.status.warning.border,
        },
        standardError: {
          backgroundColor: colorTokens.status.error.background,
          color: colorTokens.status.error.foreground,
          borderColor: colorTokens.status.error.border,
        },
      },
    },
    MuiTooltip: {
      defaultProps: {
        arrow: true,
      },
      styleOverrides: {
        tooltip: ({ theme }) => ({
          ...theme.typography.body2,
          backgroundColor: colorTokens.brand.deepNavy,
          color: colorTokens.text.inverse,
          border: `1px solid ${alpha(colorTokens.brand.accent, 0.3)}`,
          borderRadius: shapeTokens.radius.sm,
          boxShadow: elevationTokens.sm,
          padding: `${spacingTokens.xs}px ${spacingTokens.sm}px`,
          maxWidth: 340,
        }),
        arrow: {
          color: colorTokens.brand.deepNavy,
        },
      },
    },
  },
});
