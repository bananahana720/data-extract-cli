export const statusTokens = {
  neutral: {
    background: "#E7EFF5",
    foreground: "#1D3A4D",
    border: "#C4D6E4",
  },
  info: {
    background: "#E5F5FE",
    foreground: "#0D4B70",
    border: "#9BD8FA",
  },
  success: {
    background: "#E9F9F1",
    foreground: "#0F5132",
    border: "#9EDDBB",
  },
  warning: {
    background: "#FFF6E5",
    foreground: "#7A4A05",
    border: "#F0CF8D",
  },
  error: {
    background: "#FEEDEE",
    foreground: "#7A1820",
    border: "#F3B5BC",
  },
} as const;

export const colorTokens = {
  brand: {
    deepNavy: "#0B1F2B",
    accent: "#1DA1F2",
    accentStrong: "#0A7BC0",
    accentSoft: "#DFF2FE",
    onBrand: "#FFFFFF",
  },
  surface: {
    canvas: "#F3F7FB",
    elevated: "#FFFFFF",
    muted: "#E8EFF5",
  },
  text: {
    primary: "#0B1F2B",
    secondary: "#2E4A5E",
    muted: "#5B7488",
    inverse: "#FFFFFF",
  },
  border: {
    subtle: "#CFDEE9",
    strong: "#ABC1D0",
  },
  status: statusTokens,
} as const;

export const typographyTokens = {
  fontFamily: {
    sans: '"Space Grotesk", "Avenir Next", "Segoe UI", sans-serif',
    mono: '"IBM Plex Mono", "SFMono-Regular", Menlo, Consolas, monospace',
  },
  fontSize: {
    xs: "0.75rem",
    sm: "0.875rem",
    md: "1rem",
    lg: "1.125rem",
    xl: "1.375rem",
    "2xl": "1.75rem",
  },
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.65,
  },
  fontWeight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  letterSpacing: {
    normal: "0em",
    wide: "0.01em",
    caps: "0.08em",
  },
} as const;

export const spacingTokens = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  "2xl": 40,
} as const;

export const breakpointTokens = {
  xs: 320,
  sm: 480,
  md: 768,
  lg: 1024,
  xl: 1440,
} as const;

export const shapeTokens = {
  radius: {
    sm: 8,
    md: 12,
    lg: 16,
    pill: 999,
  },
} as const;

export const elevationTokens = {
  sm: "0 8px 20px rgba(11, 31, 43, 0.08)",
  md: "0 14px 30px rgba(11, 31, 43, 0.12)",
} as const;

const px = (value: number): string => `${value}px`;

export const cssCustomPropertyTokens = {
  typography: {
    fontSans: typographyTokens.fontFamily.sans,
    fontSize100: typographyTokens.fontSize.xs,
    fontSize200: typographyTokens.fontSize.sm,
    fontSize300: typographyTokens.fontSize.md,
    fontSize400: typographyTokens.fontSize.lg,
    fontSize500: typographyTokens.fontSize.xl,
    fontSize600: `clamp(${typographyTokens.fontSize.xl}, 2.4vw, ${typographyTokens.fontSize["2xl"]})`,
    lineHeightNormal: `${typographyTokens.lineHeight.normal}`,
    letterSpacingWide: typographyTokens.letterSpacing.wide,
    letterSpacingCaps: typographyTokens.letterSpacing.caps,
    fontWeightRegular: `${typographyTokens.fontWeight.regular}`,
    fontWeightMedium: `${typographyTokens.fontWeight.medium}`,
    fontWeightSemibold: `${typographyTokens.fontWeight.semibold}`,
    fontWeightBold: `${typographyTokens.fontWeight.bold}`,
  },
  spacing: {
    xxs: px(spacingTokens.xxs),
    xs: px(spacingTokens.xs),
    sm: px(spacingTokens.sm),
    md: px(spacingTokens.md),
    lg: px(spacingTokens.lg),
    xl: px(spacingTokens.xl),
    "2xl": px(spacingTokens["2xl"]),
  },
  radius: {
    sm: px(shapeTokens.radius.sm),
    md: px(shapeTokens.radius.md),
    lg: px(shapeTokens.radius.lg),
    pill: px(shapeTokens.radius.pill),
  },
  color: {
    surfaceCanvas: colorTokens.surface.canvas,
    surfaceElevated: colorTokens.surface.elevated,
    surfaceMuted: colorTokens.surface.muted,
    textPrimary: colorTokens.text.primary,
    textSecondary: colorTokens.text.secondary,
    textMuted: colorTokens.text.muted,
    borderSubtle: colorTokens.border.subtle,
    accent: colorTokens.brand.accent,
    accentStrong: colorTokens.brand.accentStrong,
    accentSoft: colorTokens.brand.accentSoft,
    infoBg: colorTokens.status.info.background,
    infoFg: colorTokens.status.info.foreground,
    infoBorder: colorTokens.status.info.border,
    successBg: colorTokens.status.success.background,
    successFg: colorTokens.status.success.foreground,
    successBorder: colorTokens.status.success.border,
    warnBg: colorTokens.status.warning.background,
    warnFg: colorTokens.status.warning.foreground,
    warnBorder: colorTokens.status.warning.border,
    errorBg: colorTokens.status.error.background,
    errorFg: colorTokens.status.error.foreground,
    errorBorder: colorTokens.status.error.border,
  },
  elevation: {
    sm: elevationTokens.sm,
    md: elevationTokens.md,
  },
} as const;

export type SemanticStatus = keyof typeof statusTokens;
export type ColorTokens = typeof colorTokens;
export type TypographyTokens = typeof typographyTokens;
export type SpacingTokens = typeof spacingTokens;
export type BreakpointTokens = typeof breakpointTokens;
