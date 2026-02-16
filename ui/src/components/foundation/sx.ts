import type { SxProps, SystemStyleObject } from "@mui/system";
import type { Theme } from "@mui/material/styles";

type SxEntry = SystemStyleObject<Theme> | ((theme: Theme) => SystemStyleObject<Theme>);

export function mergeSx(base: SxEntry, sx?: SxProps<Theme>): SxProps<Theme> {
  if (sx == null) {
    return base;
  }

  const extension = Array.isArray(sx) ? sx : [sx];
  return [base, ...extension] as SxProps<Theme>;
}
