import { alpha, createTheme } from "@mui/material/styles";

import {
  breakpointTokens,
  colorTokens,
  cssCustomPropertyTokens,
  elevationTokens,
  shapeTokens,
  spacingTokens,
  typographyTokens,
} from "./tokens";

const focusRing = {
  outline: `3px solid ${alpha(colorTokens.brand.accent, 0.45)}`,
  outlineOffset: 2,
} as const;

const focusRingShadow = `0 0 0 3px ${alpha(colorTokens.brand.accent, 0.35)}`;

const rootCssVariables: Record<string, string> = {
  "--ds-font-sans": cssCustomPropertyTokens.typography.fontSans,
  "--ds-font-size-100": cssCustomPropertyTokens.typography.fontSize100,
  "--ds-font-size-200": cssCustomPropertyTokens.typography.fontSize200,
  "--ds-font-size-300": cssCustomPropertyTokens.typography.fontSize300,
  "--ds-font-size-400": cssCustomPropertyTokens.typography.fontSize400,
  "--ds-font-size-500": cssCustomPropertyTokens.typography.fontSize500,
  "--ds-font-size-600": cssCustomPropertyTokens.typography.fontSize600,
  "--ds-line-height-normal": cssCustomPropertyTokens.typography.lineHeightNormal,
  "--ds-letter-spacing-wide": cssCustomPropertyTokens.typography.letterSpacingWide,
  "--ds-letter-spacing-caps": cssCustomPropertyTokens.typography.letterSpacingCaps,
  "--ds-font-weight-regular": cssCustomPropertyTokens.typography.fontWeightRegular,
  "--ds-font-weight-medium": cssCustomPropertyTokens.typography.fontWeightMedium,
  "--ds-font-weight-semibold": cssCustomPropertyTokens.typography.fontWeightSemibold,
  "--ds-font-weight-bold": cssCustomPropertyTokens.typography.fontWeightBold,
  "--ds-space-1": cssCustomPropertyTokens.spacing.xxs,
  "--ds-space-2": cssCustomPropertyTokens.spacing.xs,
  "--ds-space-3": cssCustomPropertyTokens.spacing.sm,
  "--ds-space-4": cssCustomPropertyTokens.spacing.md,
  "--ds-space-5": cssCustomPropertyTokens.spacing.lg,
  "--ds-space-6": cssCustomPropertyTokens.spacing.xl,
  "--ds-space-7": cssCustomPropertyTokens.spacing["2xl"],
  "--ds-radius-sm": cssCustomPropertyTokens.radius.sm,
  "--ds-radius-md": cssCustomPropertyTokens.radius.md,
  "--ds-radius-lg": cssCustomPropertyTokens.radius.lg,
  "--ds-radius-pill": cssCustomPropertyTokens.radius.pill,
  "--ds-surface-canvas": cssCustomPropertyTokens.color.surfaceCanvas,
  "--ds-surface-elevated": cssCustomPropertyTokens.color.surfaceElevated,
  "--ds-surface-muted": cssCustomPropertyTokens.color.surfaceMuted,
  "--ds-text-primary": cssCustomPropertyTokens.color.textPrimary,
  "--ds-text-secondary": cssCustomPropertyTokens.color.textSecondary,
  "--ds-text-muted": cssCustomPropertyTokens.color.textMuted,
  "--ds-border-subtle": cssCustomPropertyTokens.color.borderSubtle,
  "--ds-accent": cssCustomPropertyTokens.color.accent,
  "--ds-accent-strong": cssCustomPropertyTokens.color.accentStrong,
  "--ds-accent-soft": cssCustomPropertyTokens.color.accentSoft,
  "--ds-info-bg": cssCustomPropertyTokens.color.infoBg,
  "--ds-info": cssCustomPropertyTokens.color.infoFg,
  "--ds-info-border": cssCustomPropertyTokens.color.infoBorder,
  "--ds-success-bg": colorTokens.status.success.background,
  "--ds-success": colorTokens.status.success.foreground,
  "--ds-success-border": colorTokens.status.success.border,
  "--ds-warning-bg": colorTokens.status.warning.background,
  "--ds-warning": colorTokens.status.warning.foreground,
  "--ds-warning-border": colorTokens.status.warning.border,
  "--ds-warn-bg": colorTokens.status.warning.background,
  "--ds-warn": colorTokens.status.warning.foreground,
  "--ds-warn-border": colorTokens.status.warning.border,
  "--ds-error-bg": colorTokens.status.error.background,
  "--ds-error": colorTokens.status.error.foreground,
  "--ds-error-border": colorTokens.status.error.border,
  "--ds-focus-ring": focusRingShadow,
  "--ds-accent-overlay-10": alpha(colorTokens.brand.accent, 0.1),
  "--ds-accent-overlay-13": alpha(colorTokens.brand.accent, 0.13),
  "--ds-accent-overlay-15": alpha(colorTokens.brand.accent, 0.15),
  "--ds-accent-overlay-22": alpha(colorTokens.brand.accent, 0.22),
  "--ds-shadow-1": cssCustomPropertyTokens.elevation.sm,
};

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
      main: colorTokens.status.success.foreground,
      light: colorTokens.status.success.background,
      dark: colorTokens.status.success.border,
      contrastText: colorTokens.text.inverse,
    },
    warning: {
      main: colorTokens.status.warning.foreground,
      light: colorTokens.status.warning.background,
      dark: colorTokens.status.warning.border,
      contrastText: colorTokens.text.primary,
    },
    error: {
      main: colorTokens.status.error.foreground,
      light: colorTokens.status.error.background,
      dark: colorTokens.status.error.border,
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
        ":root": rootCssVariables,
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
