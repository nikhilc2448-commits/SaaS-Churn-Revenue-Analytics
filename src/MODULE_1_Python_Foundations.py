from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


# Project paths
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


# Expected columns for each file
EXPECTED_COLUMNS = {
    "saas_customers.csv": [
        "CustomerID",
        "CompanyName",
        "Industry",
        "Country",
        "City",
        "EmployeeCount",
        "SignupDate",
        "AcquisitionChannel"
    ],

    "saas_subscriptions.csv": [
        "SubscriptionID",
        "CustomerID",
        "PlanName",
        "BillingTerm",
        "Seats",
        "MRR",
        "StartDate",
        "EndDate",
        "Status"
    ],

    "saas_usage.csv": [
        "CustomerID",
        "SubscriptionID",
        "Month",
        "Logins",
        "ActiveUsers",
        "FeatureUsed",
        "APICalls",
        "SessionMinutes"
    ],

    "saas_tickets.csv": [
        "TicketID",
        "CustomerID",
        "OpenedDate",
        "Category",
        "Priority",
        "ResolutionHours",
        "SatisfactionScore"
    ]
}


def load_csv(file_name):
    """
    Load one CSV file with basic exception handling.
    """

    file_path = DATA_DIR / file_name

    try:
        df = pd.read_csv(file_path)

    except FileNotFoundError:
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    except EmptyDataError:
        raise ValueError(
            f"File is empty: {file_path}"
        )

    except ParserError as error:
        raise ValueError(
            f"CSV file is malformed: {file_path}\n{error}"
        )

    except UnicodeDecodeError:
        raise ValueError(
            f"Could not read the encoding of: {file_path}"
        )

    if df.empty:
        raise ValueError(
            f"No records found in: {file_path}"
        )

    return df


def validate_dataframe(df, file_name):
    """
    Check that the loaded file contains the expected columns.
    """

    expected_columns = EXPECTED_COLUMNS[file_name]
    actual_columns = df.columns.tolist()

    missing_columns = [
        column
        for column in expected_columns
        if column not in actual_columns
    ]

    extra_columns = [
        column
        for column in actual_columns
        if column not in expected_columns
    ]

    if missing_columns:
        raise ValueError(
            f"{file_name} is missing columns: {missing_columns}"
        )

    print("\n" + "=" * 60)
    print(f"VALIDATION - {file_name}")
    print("=" * 60)

    print(f"Shape: {df.shape}")
    print("Status: Valid")

    if extra_columns:
        print(f"Warning - Extra columns found: {extra_columns}")

    return True


def audit_dataframe(df, name):
    """
    Create a complete audit dictionary without printing values.
    """

    text_unique = {}

    text_columns = df.select_dtypes(include=["str"]).columns

    for col in text_columns:
        text_unique[col] = (
            df[col]
            .astype("string")
            .unique()
            .tolist()
        )

    return {
        "dataset": name,
        "rows": len(df),
        "columns": len(df.columns),
        "shape": df.shape,
        "dtypes": {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        },
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "unique_text_values": text_unique,
    }


def load_all_data():
    """
    Load and validate all four SaaS datasets.
    """

    data = {}

    for file_name in EXPECTED_COLUMNS:

        df = load_csv(file_name)

        validate_dataframe(
            df,
            file_name
        )

        table_name = file_name.replace(".csv", "")

        data[table_name] = df

    return data


if __name__ == "__main__":

    tables = load_all_data()

    for table_name, df in tables.items():
        audit_dataframe(
            df,
            table_name
        )