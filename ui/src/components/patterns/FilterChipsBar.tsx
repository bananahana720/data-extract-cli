import { useId, type HTMLAttributes, type ReactNode } from "react";

export interface FilterChipOption {
  id: string;
  label: ReactNode;
  count?: number;
  disabled?: boolean;
  ariaLabel?: string;
}

export interface FilterChipsBarProps extends Omit<HTMLAttributes<HTMLDivElement>, "onChange"> {
  chips: readonly FilterChipOption[];
  selectedChipIds: readonly string[];
  onSelectionChange?: (nextSelectedChipIds: string[]) => void;
  allowMultiple?: boolean;
  label?: string;
  clearLabel?: string;
  onClear?: () => void;
}

function cx(...values: Array<string | undefined | false>): string {
  return values.filter(Boolean).join(" ");
}

function nextSelection(
  selectedChipIds: readonly string[],
  chipId: string,
  allowMultiple: boolean
): string[] {
  const isSelected = selectedChipIds.includes(chipId);
  if (allowMultiple) {
    return isSelected
      ? selectedChipIds.filter((selectedChipId) => selectedChipId !== chipId)
      : [...selectedChipIds, chipId];
  }
  return isSelected ? [] : [chipId];
}

export function FilterChipsBar(props: FilterChipsBarProps) {
  const {
    chips,
    selectedChipIds,
    onSelectionChange,
    allowMultiple = true,
    label = "Filters",
    clearLabel = "Clear filters",
    onClear,
    className,
    role,
    ...divProps
  } = props;
  const labelId = useId();
  const selectedCount = selectedChipIds.length;
  const canUpdateSelection = Boolean(onSelectionChange);
  const canClearSelection = selectedCount > 0 && (Boolean(onClear) || canUpdateSelection);

  const handleToggle = (chipId: string) => {
    if (!onSelectionChange) {
      return;
    }
    onSelectionChange(nextSelection(selectedChipIds, chipId, allowMultiple));
  };

  const handleClear = () => {
    if (onClear) {
      onClear();
      return;
    }
    onSelectionChange?.([]);
  };

  return (
    <div
      {...divProps}
      className={cx("filter-chips-bar", className)}
      role={role ?? "group"}
      aria-labelledby={labelId}
    >
      <div className="filter-chips-bar__header">
        <p id={labelId} className="filter-chips-bar__label">
          {label}
        </p>
        <p className="filter-chips-bar__meta" aria-live="polite">
          {selectedCount === 0 ? "No filters selected" : `${selectedCount} selected`}
        </p>
      </div>
      <div className="filter-chips-bar__group" role="toolbar" aria-labelledby={labelId}>
        {chips.map((chip) => {
          const isSelected = selectedChipIds.includes(chip.id);
          return (
            <button
              key={chip.id}
              type="button"
              className={cx("filter-chip", isSelected && "is-selected")}
              disabled={chip.disabled || !canUpdateSelection}
              aria-disabled={chip.disabled || !canUpdateSelection}
              aria-pressed={isSelected}
              aria-label={chip.ariaLabel}
              onClick={() => handleToggle(chip.id)}
            >
              <span className="filter-chip__label">{chip.label}</span>
              {typeof chip.count === "number" ? (
                <span className="filter-chip__count" aria-hidden="true">
                  {chip.count}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
      {canClearSelection ? (
        <button
          type="button"
          className="action action-tertiary filter-chips-bar__clear"
          onClick={handleClear}
        >
          {clearLabel}
        </button>
      ) : null}
    </div>
  );
}
