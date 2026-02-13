"""
Export module for scraper data.
Supports JSON, CSV, and Excel export formats.
"""

import json
import pandas as pd
from rich.console import Console

console = Console()


def export_data(data, filename, format="json"):
    """
    Export scraped data to a file.

    Args:
        data: List of dicts to export
        filename: Output filename (extension will be added if missing)
        format: 'json', 'csv', or 'excel'
    """
    if not data:
        console.print("[yellow]⚠ Dışa aktarılacak veri yok.[/yellow]")
        return

    # Ensure proper extension
    ext_map = {"json": ".json", "csv": ".csv", "excel": ".xlsx"}
    expected_ext = ext_map.get(format, ".json")
    if not filename.endswith(expected_ext):
        filename = filename.rsplit(".", 1)[0] + expected_ext if "." in filename else filename + expected_ext

    if format == "json":
        _export_json(data, filename)
    elif format == "csv":
        _export_csv(data, filename)
    elif format == "excel":
        _export_excel(data, filename)
    else:
        console.print(f"[red]✗ Bilinmeyen format: {format}[/red]")
        return

    console.print(f"[bold green]✓ {len(data)} kayıt → {filename}[/bold green]")


def _export_json(data, filename):
    """Export data as JSON."""
    # Flatten nested dicts for cleaner output
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _export_csv(data, filename):
    """Export data as CSV."""
    df = _to_dataframe(data)
    df.to_csv(filename, index=False, encoding="utf-8-sig")


def _export_excel(data, filename):
    """Export data as Excel."""
    df = _to_dataframe(data)
    df.to_excel(filename, index=False, engine="openpyxl")


def _to_dataframe(data):
    """
    Convert list of dicts to a pandas DataFrame.
    Handles nested structures by flattening them.
    """
    flat_data = []
    for item in data:
        flat_item = {}
        for key, value in item.items():
            if isinstance(value, list):
                # Convert lists to semicolon-separated strings
                if value and isinstance(value[0], dict):
                    # List of dicts — serialize each
                    parts = []
                    for v in value:
                        if isinstance(v, dict):
                            parts.append(" | ".join(f"{k}: {val}" for k, val in v.items()))
                        else:
                            parts.append(str(v))
                    flat_item[key] = " ;; ".join(parts)
                else:
                    flat_item[key] = "; ".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Flatten dict into separate columns
                for sub_key, sub_val in value.items():
                    flat_item[f"{key}_{sub_key}"] = sub_val
            else:
                flat_item[key] = value
        flat_data.append(flat_item)

    return pd.DataFrame(flat_data)


def print_summary(data, title="Sonuçlar"):
    """Print a quick summary table of the data to the terminal."""
    if not data:
        console.print("[yellow]Veri bulunamadı.[/yellow]")
        return

    from rich.table import Table

    table = Table(title=title, show_lines=True)

    # Use first item's keys as columns, skip very long fields
    skip_keys = {"career", "roster", "standings", "matches", "teams", "trophies"}
    keys = [k for k in data[0].keys() if k not in skip_keys]

    for key in keys:
        table.add_column(key, style="cyan", no_wrap=False, max_width=40)

    # Show first 20 rows
    for item in data[:20]:
        row = []
        for key in keys:
            val = item.get(key, "")
            if isinstance(val, (list, dict)):
                val = f"[{len(val)} items]" if isinstance(val, list) else str(val)
            row.append(str(val)[:80])
        table.add_row(*row)

    if len(data) > 20:
        table.add_row(*[f"... +{len(data) - 20} more" if i == 0 else "" for i in range(len(keys))])

    console.print(table)
