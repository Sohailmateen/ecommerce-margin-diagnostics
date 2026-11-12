import os
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_financial_simulator():
    os.makedirs("models", exist_ok=True)
    wb = openpyxl.Workbook()

    # Load processed statistical tables
    tier_df = pd.read_csv("data/processed/unit_economics_by_tier.csv")
    delay_df = pd.read_csv("data/processed/sla_delay_impact.csv")

    # Styling definitions (Corporate Finance Palette)
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    sub_header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    input_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    output_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    bold_font = Font(name="Calibri", size=11, bold=True)
    input_font = Font(name="Calibri", size=11, bold=True, color="0000FF")
    title_font = Font(name="Calibri", size=15, bold=True, color="1F4E78")

    thin_border = Border(
        left=Side(style="thin", color="BFBFBF"),
        right=Side(style="thin", color="BFBFBF"),
        top=Side(style="thin", color="BFBFBF"),
        bottom=Side(style="thin", color="BFBFBF"),
    )

    # =========================================================================
    # TAB 1: EXECUTIVE SIMULATOR
    # =========================================================================
    ws_sim = wb.active
    ws_sim.title = "Executive_Simulator"

    ws_sim["B2"] = "OLIST E-COMMERCE MARGIN EROSION & PROFIT RECOVERY SIMULATOR"
    ws_sim["B2"].font = title_font
    ws_sim["B3"] = "Note: Yellow cells with blue text are editable business assumptions. Green cells compute live financial impact."
    ws_sim["B3"].font = Font(italic=True, size=10, color="595959")

    # Section 1: Current Baseline (Linked to Data Tabs)
    ws_sim["B5"] = "1. CURRENT BASELINE PERFORMANCE (HISTORICAL)"
    ws_sim["B5"].font = header_font
    ws_sim["B5"].fill = header_fill
    ws_sim["C5"].fill = header_fill

    baselines = [
        ("Total Delivered Orders", "=SUM(Unit_Economics_Data!B2:B6)", "#,##0"),
        ("Total Order Items Sold", 112650, "#,##0"),
        ("Total Gross Revenue ($)", "=SUMPRODUCT(Unit_Economics_Data!B2:B6, Unit_Economics_Data!C2:C6)", "$#,##0.00"),
        ("Total Net Contribution Margin ($)", "=SUM(Unit_Economics_Data!F2:F6)", "$#,##0.00"),
        ("Baseline Net Margin (%)", "=C9/C8", "0.00%"),
        ("Sub-$25 Orders Volume", "=Unit_Economics_Data!B2", "#,##0"),
        ("Avg Net Margin: Sub-$25 vs $25-$50 Lift ($)", "=Unit_Economics_Data!G3 - Unit_Economics_Data!G2", "$#,##0.00"),
        ("Total Delayed Orders (>0 SLA Days)", "=SUM(SLA_Delay_Data!B3:B5)", "#,##0"),
        ("Avg Net Margin per Order ($)", "=C9/C6", "$#,##0.00"),
    ]

    for idx, (label, formula, num_fmt) in enumerate(baselines, start=6):
        ws_sim[f"B{idx}"] = label
        ws_sim[f"B{idx}"].font = bold_font
        ws_sim[f"B{idx}"].border = thin_border
        ws_sim[f"C{idx}"] = formula
        ws_sim[f"C{idx}"].number_format = num_fmt
        ws_sim[f"C{idx}"].border = thin_border

    # Section 2: Strategic Policy Levers (Editable Assumptions)
    ws_sim["B16"] = "2. STRATEGIC POLICY LEVERS (EDITABLE INPUTS)"
    ws_sim["B16"].font = header_font
    ws_sim["B16"].fill = header_fill
    ws_sim["C16"].fill = header_fill

    levers = [
        ("Lever 1: % of Sub-$25 Orders Converted to $25-$50 Bundles", 0.25, "0.0%"),
        ("Lever 2: % Reduction in Carrier SLA Delivery Delays", 0.30, "0.0%"),
        ("Empirical Repeat Lift from On-Time Delivery (Logistic Reg)", 0.1251, "0.00%"),
        ("Lever 3: Warehouse Handling Cost Savings per Item ($)", 0.50, "$#,##0.00"),
    ]

    for idx, (label, val, num_fmt) in enumerate(levers, start=17):
        ws_sim[f"B{idx}"] = label
        ws_sim[f"B{idx}"].font = bold_font
        ws_sim[f"B{idx}"].border = thin_border
        ws_sim[f"C{idx}"] = val
        ws_sim[f"C{idx}"].font = input_font
        ws_sim[f"C{idx}"].fill = input_fill
        ws_sim[f"C{idx}"].number_format = num_fmt
        ws_sim[f"C{idx}"].border = thin_border

    # Section 3: Projected Bottom-Line Financial Impact
    ws_sim["B22"] = "3. PROJECTED ANNUALIZED PROFIT RECOVERY ($)"
    ws_sim["B22"].font = header_font
    ws_sim["B22"].fill = header_fill
    ws_sim["C22"].fill = header_fill

    impacts = [
        ("Gain from Basket Bundling (Sub-$25 -> $25-$50)", "=C11 * C17 * C12", "$#,##0.00"),
        ("Gain from Retained Repeat Orders (SLA Delay Fix)", "=(C13 * C18) * C19 * C14", "$#,##0.00"),
        ("Gain from Warehouse Handling Optimization", "=C7 * C20", "$#,##0.00"),
        ("TOTAL INCREMENTAL NET MARGIN GAIN ($)", "=SUM(C23:C25)", "$#,##0.00"),
        ("NEW PROJECTED NET MARGIN ($)", "=C9 + C26", "$#,##0.00"),
        ("NEW PROJECTED MARGIN (%)", "=C27 / C8", "0.00%"),
    ]

    for idx, (label, formula, num_fmt) in enumerate(impacts, start=23):
        ws_sim[f"B{idx}"] = label
        ws_sim[f"B{idx}"].font = bold_font
        ws_sim[f"B{idx}"].border = thin_border
        ws_sim[f"C{idx}"] = formula
        ws_sim[f"C{idx}"].font = bold_font
        ws_sim[f"C{idx}"].fill = output_fill
        ws_sim[f"C{idx}"].number_format = num_fmt
        ws_sim[f"C{idx}"].border = thin_border

    # Section 4: Multi-Scenario Sensitivity Matrix (Conservative / Base / Aggressive)
    ws_sim["E5"] = "4. EXECUTIVE SCENARIO COMPARISON MATRIX"
    ws_sim["E5"].font = header_font
    for col_let in ["E", "F", "G", "H"]:
        ws_sim[f"{col_let}5"].fill = header_fill

    headers = ["Scenario Metric", "Conservative (Low)", "Base Case (Target)", "Aggressive (High)"]
    for col_idx, h in enumerate(headers, start=5):
        cell = ws_sim.cell(row=6, column=col_idx, value=h)
        cell.font = bold_font
        cell.fill = sub_header_fill
        cell.border = thin_border

    scenarios = [
        ("Sub-$25 Bundle Conversion %", 0.15, "=C17", 0.40, "0.0%"),
        ("SLA Delay Reduction %", 0.15, "=C18", 0.50, "0.0%"),
        ("Handling Cost Savings / Item ($)", 0.25, "=C20", 0.75, "$#,##0.00"),
        ("Incremental Profit Gain ($)",
         "=($C$11*F7*$C$12) + (($C$13*F8)*$C$19*$C$14) + ($C$7*F9)",
         "=C26",
         "=($C$11*H7*$C$12) + (($C$13*H8)*$C$19*$C$14) + ($C$7*H9)",
         "$#,##0.00"),
        ("New Total Net Margin ($)", "=$C$9+F10", "=$C$9+G10", "=$C$9+H10", "$#,##0.00"),
        ("Margin Lift (Basis Points)", "=(F11/$C$8 - $C$10)*10000", "=(G11/$C$8 - $C$10)*10000", "=(H11/$C$8 - $C$10)*10000", "0\" bps\""),
    ]

    for row_idx, (metric, cons, base, aggr, num_fmt) in enumerate(scenarios, start=7):
        ws_sim.cell(row=row_idx, column=5, value=metric).font = bold_font
        ws_sim.cell(row=row_idx, column=5).border = thin_border
        for col_offset, val in enumerate([cons, base, aggr], start=6):
            c = ws_sim.cell(row=row_idx, column=col_offset, value=val)
            c.number_format = num_fmt
            c.border = thin_border
            if row_idx >= 10:
                c.fill = output_fill
                c.font = bold_font

    # =========================================================================
    # TAB 2 & TAB 3: PROCESSED DATA TABS
    # =========================================================================
    def populate_df_sheet(sheet_name, df):
        ws = wb.create_sheet(title=sheet_name)
        for col_idx, col_name in enumerate(df.columns, start=1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
        for r_idx, row in enumerate(df.itertuples(index=False), start=2):
            for c_idx, val in enumerate(row, start=1):
                ws.cell(row=r_idx, column=c_idx, value=val)
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) + 4
            ws.column_dimensions[get_column_letter(col[0].column)].width = max_len

    populate_df_sheet("Unit_Economics_Data", tier_df)
    populate_df_sheet("SLA_Delay_Data", delay_df)

    # Auto-fit columns on Executive_Simulator
    ws_sim.column_dimensions["A"].width = 3
    ws_sim.column_dimensions["B"].width = 52
    ws_sim.column_dimensions["C"].width = 20
    ws_sim.column_dimensions["D"].width = 4
    ws_sim.column_dimensions["E"].width = 34
    for col_let in ["F", "G", "H"]:
        ws_sim.column_dimensions[col_let].width = 22

    output_path = "models/financial_scenario_model.xlsx"
    wb.save(output_path)
    print(f"Successfully generated {output_path} with live Excel formulas!")

if __name__ == "__main__":
    build_financial_simulator()