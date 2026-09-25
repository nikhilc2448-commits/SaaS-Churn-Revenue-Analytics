import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLEANED_DIR = os.path.join(BASE_DIR, "data", "cleaned")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)


def load_data():
    customers = pd.read_csv(
        os.path.join(CLEANED_DIR, "saas_customers_cleaned.csv")
    )

    subscriptions = pd.read_csv(
        os.path.join(CLEANED_DIR, "saas_subscriptions_cleaned.csv")
    )

    usage = pd.read_csv(
        os.path.join(CLEANED_DIR, "saas_usage_cleaned.csv")
    )

    tickets = pd.read_csv(
        os.path.join(CLEANED_DIR, "saas_tickets_cleaned.csv")
    )

    customers["SignupDate"] = pd.to_datetime(
        customers["SignupDate"], errors="coerce"
    )

    subscriptions["StartDate"] = pd.to_datetime(
        subscriptions["StartDate"], errors="coerce"
    )

    subscriptions["EndDate"] = pd.to_datetime(
        subscriptions["EndDate"], errors="coerce"
    )

    subscriptions["MRR"] = pd.to_numeric(
        subscriptions["MRR"], errors="coerce"
    ).fillna(0)

    usage["Month"] = pd.to_datetime(
        usage["Month"], errors="coerce"
    )

    tickets["OpenedDate"] = pd.to_datetime(
        tickets["OpenedDate"], errors="coerce"
    )

    return customers, subscriptions, usage, tickets


def create_customer_summary(customers, subscriptions):
    subscriptions = subscriptions.sort_values(
        ["CustomerID", "StartDate"]
    )

    latest_subscription = (
        subscriptions
        .drop_duplicates("CustomerID", keep="last")
        [["CustomerID", "Status"]]
    )

    revenue = (
        subscriptions.groupby("CustomerID")["MRR"]
        .sum()
        .rename("TotalMRR")
    )

    summary = customers[
        ["CustomerID", "CompanyName", "Industry", "SignupDate"]
    ].copy()

    summary = summary.merge(
        latest_subscription,
        on="CustomerID",
        how="left"
    )

    summary = summary.merge(
        revenue,
        on="CustomerID",
        how="left"
    )

    summary["TotalMRR"] = summary["TotalMRR"].fillna(0)

    analysis_date = max(
        customers["SignupDate"].max(),
        subscriptions["StartDate"].max(),
        subscriptions["EndDate"].max()
    )

    summary["TenureMonths"] = (
        (analysis_date - summary["SignupDate"]).dt.days / 30.44
    ).clip(lower=0).round(1)

    return summary, analysis_date


def create_pivot_summaries(customers, subscriptions):
    subscription_customer = subscriptions.merge(
        customers[["CustomerID", "Industry", "AcquisitionChannel"]],
        on="CustomerID",
        how="left"
    )

    plan_pivot = pd.pivot_table(
        subscriptions,
        index="PlanName",
        values="MRR",
        aggfunc=["count", "sum", "mean"]
    )

    plan_pivot.columns = [
        "SubscriptionCount",
        "TotalMRR",
        "AverageMRR"
    ]

    plan_pivot = plan_pivot.reset_index()

    industry_pivot = pd.pivot_table(
        subscription_customer,
        index="Industry",
        values="MRR",
        aggfunc=["count", "sum", "mean"]
    )

    industry_pivot.columns = [
        "SubscriptionCount",
        "TotalMRR",
        "AverageMRR"
    ]

    industry_pivot = industry_pivot.reset_index()

    channel_pivot = pd.pivot_table(
        subscription_customer,
        index="AcquisitionChannel",
        values="MRR",
        aggfunc=["count", "sum", "mean"]
    )

    channel_pivot.columns = [
        "SubscriptionCount",
        "TotalMRR",
        "AverageMRR"
    ]

    channel_pivot = channel_pivot.reset_index()

    return plan_pivot, industry_pivot, channel_pivot


def write_dataframe(ws, df, table_name):
    for column_index, column in enumerate(df.columns, start=1):
        cell = ws.cell(row=1, column=column_index, value=column)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for row_index, row in enumerate(
        df.itertuples(index=False),
        start=2
    ):
        for column_index, value in enumerate(row, start=1):
            cell = ws.cell(
                row=row_index,
                column=column_index,
                value=value
            )

            if isinstance(value, pd.Timestamp):
                cell.value = value.to_pydatetime()
                cell.number_format = "yyyy-mm-dd"

    if len(df.columns) > 0 and len(df) > 0:
        end_column = get_column_letter(len(df.columns))
        end_row = len(df) + 1

        table = Table(
            displayName=table_name,
            ref=f"A1:{end_column}{end_row}"
        )

        style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )

        table.tableStyleInfo = style
        ws.add_table(table)

    for column_cells in ws.columns:
        max_length = 0

        for cell in column_cells:
            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        ws.column_dimensions[
            get_column_letter(column_cells[0].column)
        ].width = min(max_length + 2, 30)


def create_kpi_sheet(wb, customer_summary):
    ws = wb.create_sheet("KPI")

    ws["A1"] = "SaaS Churn & Revenue KPIs"
    ws["A1"].font = Font(bold=True, size=14)

    ws["A3"] = "KPI"
    ws["B3"] = "Value"

    ws["A3"].font = Font(bold=True)
    ws["B3"].font = Font(bold=True)

    last_row = len(customer_summary) + 1

    ws["A4"] = "Total MRR"
    ws["B4"] = f"=SUM('Customer Summary'!E2:E{last_row})"

    ws["A5"] = "Churn Rate"
    ws["B5"] = (
        f'=COUNTIF(\'Customer Summary\'!E2:E{last_row},"Churned")'
        f'/COUNTA(\'Customer Summary\'!A2:A{last_row})'
    )

    # Status is actually column E and MRR is column F
    ws["B5"] = (
        f'=COUNTIF(\'Customer Summary\'!E2:E{last_row},"Churned")'
        f'/COUNTA(\'Customer Summary\'!A2:A{last_row})'
    )

    ws["A6"] = "Average Revenue per Account"
    ws["B6"] = (
        f"=AVERAGE('Customer Summary'!F2:F{last_row})"
    )

    ws["A7"] = "Average Tenure"
    ws["B7"] = (
        f"=AVERAGE('Customer Summary'!G2:G{last_row})"
    )

    ws["A9"] = "Analysis Date"
    ws["B9"] = self_analysis_date

    ws["B4"].number_format = '#,##0.00'
    ws["B5"].number_format = '0.00%'
    ws["B6"].number_format = '#,##0.00'
    ws["B7"].number_format = '0.0'

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 20

    return ws


def main():
    print("Starting Module 11 - Excel Reporting...")

    customers, subscriptions, usage, tickets = load_data()

    customer_summary, analysis_date = create_customer_summary(
        customers,
        subscriptions
    )

    plan_pivot, industry_pivot, channel_pivot = create_pivot_summaries(
        customers,
        subscriptions
    )

    wb = Workbook()

    default_sheet = wb.active
    wb.remove(default_sheet)

    # Cleaned data sheets
    write_dataframe(
        wb.create_sheet("Customers"),
        customers,
        "CustomersTable"
    )

    write_dataframe(
        wb.create_sheet("Subscriptions"),
        subscriptions,
        "SubscriptionsTable"
    )

    write_dataframe(
        wb.create_sheet("Usage"),
        usage,
        "UsageTable"
    )

    write_dataframe(
        wb.create_sheet("Tickets"),
        tickets,
        "TicketsTable"
    )

    # Customer summary
    write_dataframe(
        wb.create_sheet("Customer Summary"),
        customer_summary,
        "CustomerSummaryTable"
    )

    # Pivot summaries
    ws = wb.create_sheet("Pivot Summary")

    ws["A1"] = "Revenue by Plan"
    ws["A1"].font = Font(bold=True, size=13)

    plan_start = 3

    for column_index, column in enumerate(
        plan_pivot.columns,
        start=1
    ):
        ws.cell(
            row=plan_start,
            column=column_index,
            value=column
        ).font = Font(bold=True)

    for row_index, row in enumerate(
        plan_pivot.itertuples(index=False),
        start=plan_start + 1
    ):
        for column_index, value in enumerate(row, start=1):
            ws.cell(
                row=row_index,
                column=column_index,
                value=value
            )

    industry_start = plan_start + len(plan_pivot) + 4

    ws.cell(
        row=industry_start,
        column=1,
        value="Revenue by Industry"
    ).font = Font(bold=True, size=13)

    for column_index, column in enumerate(
        industry_pivot.columns,
        start=1
    ):
        ws.cell(
            row=industry_start + 2,
            column=column_index,
            value=column
        ).font = Font(bold=True)

    for row_index, row in enumerate(
        industry_pivot.itertuples(index=False),
        start=industry_start + 3
    ):
        for column_index, value in enumerate(row, start=1):
            ws.cell(
                row=row_index,
                column=column_index,
                value=value
            )

    channel_start = industry_start + len(industry_pivot) + 5

    ws.cell(
        row=channel_start,
        column=1,
        value="Revenue by Acquisition Channel"
    ).font = Font(bold=True, size=13)

    for column_index, column in enumerate(
        channel_pivot.columns,
        start=1
    ):
        ws.cell(
            row=channel_start + 2,
            column=column_index,
            value=column
        ).font = Font(bold=True)

    for row_index, row in enumerate(
        channel_pivot.itertuples(index=False),
        start=channel_start + 3
    ):
        for column_index, value in enumerate(row, start=1):
            ws.cell(
                row=row_index,
                column=column_index,
                value=value
            )

    for column in range(1, 5):
        ws.column_dimensions[
            get_column_letter(column)
        ].width = 25

    # KPI sheet
    ws_kpi = wb.create_sheet("KPI")

    ws_kpi["A1"] = "SaaS Churn & Revenue KPIs"
    ws_kpi["A1"].font = Font(bold=True, size=14)

    ws_kpi["A3"] = "KPI"
    ws_kpi["B3"] = "Value"

    ws_kpi["A3"].font = Font(bold=True)
    ws_kpi["B3"].font = Font(bold=True)

    last_row = len(customer_summary) + 1

    # Customer Summary columns:
    # A CustomerID
    # B CompanyName
    # C Industry
    # D SignupDate
    # E Status
    # F TotalMRR
    # G TenureMonths

    ws_kpi["A4"] = "Total MRR"
    ws_kpi["B4"] = (
        f"=SUM('Customer Summary'!F2:F{last_row})"
    )

    ws_kpi["A5"] = "Churn Rate"
    ws_kpi["B5"] = (
        f'=COUNTIF(\'Customer Summary\'!E2:E{last_row},"Churned")'
        f'/COUNTA(\'Customer Summary\'!A2:A{last_row})'
    )

    ws_kpi["A6"] = "Average Revenue per Account"
    ws_kpi["B6"] = (
        f"=AVERAGE('Customer Summary'!F2:F{last_row})"
    )

    ws_kpi["A7"] = "Average Tenure"
    ws_kpi["B7"] = (
        f"=AVERAGE('Customer Summary'!G2:G{last_row})"
    )

    ws_kpi["A9"] = "Analysis Date"
    ws_kpi["B9"] = analysis_date.to_pydatetime()
    ws_kpi["B9"].number_format = "yyyy-mm-dd"

    ws_kpi["B4"].number_format = '#,##0.00'
    ws_kpi["B5"].number_format = '0.00%'
    ws_kpi["B6"].number_format = '#,##0.00'
    ws_kpi["B7"].number_format = '0.0'

    ws_kpi.column_dimensions["A"].width = 30
    ws_kpi.column_dimensions["B"].width = 20

    output_file = os.path.join(
        REPORTS_DIR,
        "saas_churn_excel_report.xlsx"
    )

    wb.save(output_file)

    print(f"Customers included: {len(customers)}")
    print(f"Subscriptions included: {len(subscriptions)}")
    print(f"Excel report saved: {output_file}")
    print("Module 11 completed successfully.")


if __name__ == "__main__":
    main()
