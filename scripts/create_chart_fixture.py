#!/usr/bin/env python3
"""Create Excel fixture with chart for testing chart detection."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference


def create_chart_fixture():
    """Create Excel workbook with embedded chart."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Data"

    # Add sample data
    data = [
        ["Month", "Sales", "Expenses"],
        ["January", 5000, 3000],
        ["February", 6000, 3500],
        ["March", 7000, 4000],
        ["April", 5500, 3200],
        ["May", 8000, 4500],
        ["June", 9000, 5000],
    ]

    for row in data:
        ws.append(row)

    # Create a bar chart
    chart = BarChart()
    chart.title = "Sales vs Expenses"
    chart.style = 10
    chart.x_axis.title = "Month"
    chart.y_axis.title = "Amount ($)"

    # Set data range for chart
    data_ref = Reference(ws, min_col=2, min_row=1, max_row=7, max_col=3)
    cats_ref = Reference(ws, min_col=1, min_row=2, max_row=7)

    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)

    # Add chart to worksheet
    ws.add_chart(chart, "E5")

    # Save fixture
    fixture_dir = Path(__file__).parent.parent / "tests" / "fixtures" / "excel"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    output_path = fixture_dir / "with_charts.xlsx"

    wb.save(output_path)
    print(f"Created chart fixture: {output_path}")
    print("Fixture contains: 1 worksheet with data and 1 embedded bar chart")

    return output_path


if __name__ == "__main__":
    create_chart_fixture()
