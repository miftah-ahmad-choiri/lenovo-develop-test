"""
Pure transformation functions for the WO Onsite pipeline.

Every function here is stateless — it takes DataFrames and returns DataFrames.
No file I/O happens here; that lives in pipeline.py.
"""
import pandas as pd
import numpy as np


# ── 1. New-WO detection ───────────────────────────────────────────────────────

def new_wo_filter_detection(
    df_devi3_input: pd.DataFrame,
    df_devi2_input: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return WO IDs from df_devi3 (last 60 days) that do NOT exist in df_devi2.

    Returns a DataFrame with columns:
        'Work Order ID (df_devi3)', 'Exists in df_devi2' (always 0)
    """
    df3 = df_devi3_input.copy()
    df3["Release Date"] = pd.to_datetime(df3["Release Date"], errors="coerce")
    cutoff = pd.to_datetime("today") - pd.Timedelta(days=60)
    df3 = df3[df3["Release Date"] >= cutoff]

    flags = df3["Work Order ID"].isin(df_devi2_input["WO#"]).astype(int)
    df_verification = pd.DataFrame({
        "Work Order ID (df_devi3)": df3["Work Order ID"],
        "Exists in df_devi2":       flags,
    })
    return df_verification[df_verification["Exists in df_devi2"] == 0]


# ── 2. Process new WOs ────────────────────────────────────────────────────────

def process_new_work_orders(
    df_devi3_raw: pd.DataFrame,
    df_new_wo_filtered_ids: pd.DataFrame,
) -> pd.DataFrame:
    """
    Filter df_devi3 to new WOs (last 60 days, not in devi2), select and rename
    columns, returning df_new_wo_process1.
    """
    if df_new_wo_filtered_ids.empty:
        print("df_new_wo_filtered_ids is empty — no new WOs to process.")
        return pd.DataFrame()

    df3 = df_devi3_raw.copy()
    df3["Release Date"] = pd.to_datetime(df3["Release Date"], errors="coerce")
    cutoff = pd.to_datetime("today") - pd.Timedelta(days=60)
    df3_60 = df3[df3["Release Date"] >= cutoff]

    new_ids = df_new_wo_filtered_ids["Work Order ID (df_devi3)"].unique()
    df_temp = df3_60[df3_60["Work Order ID"].isin(new_ids)].copy()

    column_mapping = {
        "Release Date":                  "Creation Date",
        "Work Order ID":                 "WO#",
        "Serial Number":                 "SN",
        "Product Description":           "Product",
        "Case":                          "Service Order Description",
        "Owner":                         "Actual ASP",
        "Labor Vendor Related":          "Origin Vendor ID",
        "Service Delivery Instructions": "Information",
    }
    selected = {k: v for k, v in column_mapping.items() if k in df_temp.columns}
    if not selected:
        print("Warning: no matching columns found. Returning empty DataFrame.")
        return pd.DataFrame()

    df_out = df_temp[list(selected.keys())].rename(columns=selected)
    if "Creation Date" in df_out.columns:
        df_out["Creation Date"] = pd.to_datetime(df_out["Creation Date"], errors="coerce")
    return df_out


# ── 3. Process customer info ──────────────────────────────────────────────────

def process_customer_info(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'Customer Address', 'Customer Name', and 'Customer Phone No ' columns
    by combining contact fields from df_devi1.
    """
    df = df_input.copy()

    df["Customer Address"] = pd.Series(np.where(
        df["Company Name (Contact) (Contact)"].isna(),
        df["Address 1 (Contact) (Contact)"].fillna(""),
        df["Company Name (Contact) (Contact)"].fillna("") + ", " +
        df["Address 1 (Contact) (Contact)"].fillna(""),
    )).str.strip()

    df["Customer Name"] = pd.Series(np.where(
        df[" Contact Name (Contact) (Contact)"].isna(),
        df["Primary Email (Contact) (Contact)"].fillna(""),
        df[" Contact Name (Contact) (Contact)"].fillna("") + " (" +
        df["Primary Email (Contact) (Contact)"].fillna("") + ")",
    )).str.strip()

    def _fmt_phone(value):
        if pd.isna(value) or str(value).strip() == "":
            return np.nan
        try:
            fv = float(value)
            return str(int(fv)) if fv == int(fv) else str(fv)
        except (ValueError, TypeError):
            return str(value)

    df["Customer Phone No "] = (
        df["Mobile Phone (Contact) (Contact)"]
        .astype(str)
        .str.replace(r"[+-]", "", regex=True)
        .apply(_fmt_phone)
    )
    return df


# ── 4. Update Actual ASP from devi1 ──────────────────────────────────────────

def update_actual_asp_from_devi1(
    df_new_wo_proc1: pd.DataFrame,
    df_devi1_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Update the 'Actual ASP' column in df_new_wo_proc1 using matching WO# from
    df_devi1 and its 'Owner' / 'Customer (Labor Vendor Related)' columns.
    """
    if df_new_wo_proc1.empty or "WO#" not in df_new_wo_proc1.columns:
        return df_new_wo_proc1.copy()
    df = df_new_wo_proc1.copy()
    merged = pd.merge(
        df,
        df_devi1_data[["Work Order ID", "Owner",
                        "Customer (Labor Vendor Related) (Partner Function)"]],
        left_on="WO#", right_on="Work Order ID",
        how="left", suffixes=("_proc1", "_devi1"),
    )
    conditions = [
        merged["Actual ASP"].fillna("") == merged["Owner"].fillna(""),
        merged["Actual ASP"].fillna("") ==
        merged["Customer (Labor Vendor Related) (Partner Function)"].fillna(""),
    ]
    choices = [
        merged["Actual ASP"],
        merged["Customer (Labor Vendor Related) (Partner Function)"],
    ]
    df["Actual ASP"] = np.select(conditions, choices,
                                  default=merged["Actual ASP"])
    return df


# ── 5. Combine WO + customer info ─────────────────────────────────────────────

def combine_wo_and_customer_info(
    df_updated_wo: pd.DataFrame,
    df_processed_customer: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge customer address/name/phone from df_processed_customer into
    df_updated_wo on WO#.
    """
    if df_updated_wo.empty or "WO#" not in df_updated_wo.columns:
        return pd.DataFrame()
    wo_ids = df_updated_wo["WO#"].unique()
    df_cust = df_processed_customer[
        df_processed_customer["Work Order ID"].isin(wo_ids)
    ].copy()

    df_combined = pd.merge(
        df_updated_wo,
        df_cust[["Work Order ID", "Customer Address",
                 "Customer Name", "Customer Phone No "]],
        left_on="WO#", right_on="Work Order ID",
        how="left",
    )
    return df_combined.drop(columns=["Work Order ID"])


# ── 6. Process devi4 data ─────────────────────────────────────────────────────

def process_devi4_data(
    df_devi4_input: pd.DataFrame,
    df_devi2_input: pd.DataFrame,
    df_final_combined_input: pd.DataFrame,
) -> pd.DataFrame:
    """
    Filter and reshape devi4 (work-order products), aggregate part descriptions
    per WO, and return a merged DataFrame.
    """
    df4 = df_devi4_input[[
        "Work Order", "Work Order Product Status",
        "Original Committed Delivery Date", "Product", "Description", "Shipment Date",
    ]].copy()
    df4.rename(columns={
        "Work Order Product Status": "Status",
        "Shipment Date":             "WH Ship      (LAPS)",
    }, inplace=True)

    df4["process"] = df4["Status"].isin(["Delivered", "Shipped", "parts in transit"]).astype(int)
    df4["Status Part"] = None

    shipped = df4["Status"].str.lower() == "shipped"
    df4.loc[shipped, "Status Part"] = "waiting part"
    df4.loc[shipped, "process"]     = 2

    product_ok = ~df4["Product"].isin(["OUBHAN2", "INBHAN1"])
    df4["Part Description"] = np.where(
        product_ok,
        df4["Product"].astype(str) + " " + df4["Description"].astype(str),
        np.nan,
    )
    df4.dropna(subset=["Part Description"], inplace=True)

    df2_open = df_devi2_input[
        ~df_devi2_input["Status"].isin(["completed", "cancelled", "Completed", "Cancelled"])
    ]
    # df_new_wo_only may be empty when all devi3 WOs already exist in devi2
    if not df_final_combined_input.empty and "WO#" in df_final_combined_input.columns:
        wo_from_combined = df_final_combined_input["WO#"].unique()
    else:
        wo_from_combined = pd.array([], dtype=object)

    df4_filtered = df4[
        df4["Work Order"].isin(df2_open["WO#"]) |
        df4["Work Order"].isin(wo_from_combined)
    ].copy()

    df4_merged = df4_filtered.groupby("Work Order").agg(
        Product_Description=("Part Description", lambda x: ", ".join(x.dropna().unique())),
        **{col: (col, "first") for col in df4_filtered.columns
           if col not in ["Work Order", "Part Description"]},
    ).reset_index()

    return df4_merged.rename(columns={
        "Work Order":          "WO#",
        "Product_Description": "Part Description",
    })


# ── 7. Consolidate merged columns ─────────────────────────────────────────────

def consolidate_merged_columns(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse '_devi2' / '_new_wo' suffix pairs into a single column,
    prioritising _new_wo values.
    """
    df = df_raw.copy()
    suffixed = [c for c in df.columns if "_devi2" in c or "_new_wo" in c]
    originals = sorted(set(
        c.replace("_devi2", "").replace("_new_wo", "") for c in suffixed
    ))
    for col in originals:
        c2, cn = f"{col}_devi2", f"{col}_new_wo"
        if c2 in df.columns and cn in df.columns:
            df[col] = df[cn].fillna(df[c2])
            df.drop(columns=[c2, cn], inplace=True)
        elif c2 in df.columns and col not in df.columns:
            df.rename(columns={c2: col}, inplace=True)
        elif cn in df.columns and col not in df.columns:
            df.rename(columns={cn: col}, inplace=True)
    return df


# ── 8. Combine devi2 + new-WO with consolidation ──────────────────────────────

def combine_devi2_new_wo_with_consolidation(
    df_devi2_full: pd.DataFrame,
    df_new_wo_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Outer-merge open devi2 rows with new-WO rows, then consolidate duplicate
    columns.
    """
    df2_open = df_devi2_full[
        ~df_devi2_full["Status"].isin(["completed", "cancelled", "Completed", "Cancelled"])
    ].copy()

    common_cols = [
        "Creation Date", "WO#", "SN", "Product", "Service Order Description",
        "Actual ASP", "Origin Vendor ID", "Information",
        "Customer Address", "Customer Name", "Customer Phone No ",
    ]

    df2_sel = df2_open[common_cols].copy()
    df2_sel.rename(columns={c: f"{c}_devi2" for c in common_cols if c != "WO#"}, inplace=True)

    # If there are no new WOs (empty or missing columns), return devi2-only data
    if df_new_wo_data.empty or not all(c in df_new_wo_data.columns for c in common_cols):
        return consolidate_merged_columns(df2_sel)

    df_nw_sel = df_new_wo_data[common_cols].copy()
    df_nw_sel.rename(columns={c: f"{c}_new_wo" for c in common_cols if c != "WO#"}, inplace=True)

    merged = pd.merge(df2_sel, df_nw_sel, on="WO#", how="outer")
    return consolidate_merged_columns(merged)


# ── 9a. Filter devi2 rows not in devi4 ────────────────────────────────────────

def filter_devi2_not_in_devi4(
    df_devi2_input: pd.DataFrame,
    df_devi4_merged_input: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return open devi2 rows whose WO# does not appear in devi4.
    """
    df2 = df_devi2_input[
        ~df_devi2_input["Status"].isin(["completed", "cancelled", "Completed", "Cancelled"])
    ].copy()
    return df2[~df2["WO#"].isin(df_devi4_merged_input["WO#"])].copy()


# ── 9b. Merge and reorder ─────────────────────────────────────────────────────

def merge_and_reorder_dfs(
    df_devi4_merged: pd.DataFrame,
    df_combined_open: pd.DataFrame,
    final_cols_order: list,
) -> pd.DataFrame:
    """
    Left-merge devi4 data with combined open WOs, consolidate suffix columns,
    and reorder to final_cols_order.
    """
    def _fmt_vendor_id(value):
        if pd.isna(value):
            return np.nan
        try:
            fv = float(value)
            return str(int(fv)) if fv == int(fv) else str(fv)
        except (ValueError, TypeError):
            return str(value)

    df4 = df_devi4_merged.copy()
    if "Product" in df4.columns:
        df4.drop(columns=["Product"], inplace=True)

    cols_from_combined = [
        c for c in final_cols_order
        if c in df_combined_open.columns and c not in df4.columns
    ]
    cols_from_combined = list(dict.fromkeys(["WO#"] + cols_from_combined))
    df_combined_subset = df_combined_open[cols_from_combined]

    df_merged = pd.merge(
        df4, df_combined_subset,
        on="WO#", how="left",
        suffixes=("_devi4", "_combined"),
    )

    for col in final_cols_order:
        if col == "Product":
            continue
        c4, cc = f"{col}_devi4", f"{col}_combined"
        if c4 in df_merged.columns and cc in df_merged.columns:
            df_merged[col] = df_merged[c4].fillna(df_merged[cc])
            df_merged.drop(columns=[c4, cc], inplace=True)
        elif c4 in df_merged.columns:
            df_merged.rename(columns={c4: col}, inplace=True)
        elif cc in df_merged.columns:
            df_merged.rename(columns={cc: col}, inplace=True)

    final_df = df_merged[final_cols_order].copy()
    if "Origin Vendor ID" in final_df.columns:
        final_df["Origin Vendor ID"] = final_df["Origin Vendor ID"].apply(_fmt_vendor_id)
    return final_df


# ── 10. Update Actual Vendor ID ───────────────────────────────────────────────

def update_actual_vendor_id(
    df_final_report: pd.DataFrame,
    df_devi2_source: pd.DataFrame,
) -> pd.DataFrame:
    """
    Fill / update 'Actual Vendor ID' and 'Origin ASP' from devi2.
    """
    df = df_final_report.copy()
    df2 = df_devi2_source[["WO#", "Actual Vendor ID", "Origin ASP"]].copy()
    df2.rename(columns={
        "Actual Vendor ID": "Actual Vendor ID_from_devi2",
        "Origin ASP":       "Origin ASP_from_devi2",
    }, inplace=True)

    merged = pd.merge(df, df2, on="WO#", how="left")
    df["Actual Vendor ID"] = merged["Actual Vendor ID"].fillna(
        merged["Actual Vendor ID_from_devi2"]
    )
    df["Origin ASP"] = merged["Origin ASP_from_devi2"]
    return df


# ── 11. Update ASP information (vendor-mapping lookup) ───────────────────────

def update_asp_information(
    df_final_report: pd.DataFrame,
    df_devi12: pd.DataFrame,
) -> pd.DataFrame:
    """
    Resolve Official ASP Name and Vendor ID using the vendor-mapping table
    (devi12 sheet 1).

    Case 1: Origin Vendor ID present  → look up name via Vendor ID → Name 1
    Case 2: Origin Vendor ID blank    → look up Vendor ID via Actual ASP alias
                                         → then resolve name
    Then set Origin ASP = Actual ASP = official name, Actual Vendor ID = Vendor ID.
    """
    df = df_final_report.copy()
    asp = df_devi12.copy()

    for col in ["Vendor ID", "Name 1"]:
        asp[col] = asp[col].fillna("").astype(str).str.strip()

    alias_cols = []
    for col in ["Name 2", "Name 3"]:
        if col in asp.columns:
            asp[col] = asp[col].fillna("").astype(str).str.strip()
            alias_cols.append(col)

    vendor_to_name = (
        asp.drop_duplicates("Vendor ID")
        .set_index("Vendor ID")["Name 1"]
        .to_dict()
    )
    name_to_vendor: dict = {}
    for _, row in asp.iterrows():
        if row["Name 1"]:
            name_to_vendor[row["Name 1"]] = row["Vendor ID"]
        for alias_col in alias_cols:
            if row[alias_col]:
                name_to_vendor[row[alias_col]] = row["Vendor ID"]

    for idx in df.index:
        origin_vid = str(df.at[idx, "Origin Vendor ID"]).strip()

        if (
            pd.notna(df.at[idx, "Origin Vendor ID"])
            and origin_vid not in ("", "nan")
        ):
            # Case 1
            asp_name = vendor_to_name.get(origin_vid)
            if asp_name:
                df.at[idx, "Origin ASP"]       = asp_name
                df.at[idx, "Actual ASP"]        = asp_name
                df.at[idx, "Actual Vendor ID"]  = origin_vid
        else:
            # Case 2
            actual_asp = str(df.at[idx, "Actual ASP"]).strip()
            if actual_asp and actual_asp.lower() != "nan":
                vid = name_to_vendor.get(actual_asp)
                if vid:
                    asp_name = vendor_to_name.get(vid)
                    if asp_name:
                        df.at[idx, "Origin Vendor ID"] = vid
                        df.at[idx, "Actual Vendor ID"] = vid
                        df.at[idx, "Origin ASP"]       = asp_name
                        df.at[idx, "Actual ASP"]       = asp_name
    return df


# ── 12. Format final columns ──────────────────────────────────────────────────

def format_columns_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cast date columns to datetime and string columns to str, ready for export.
    """
    df_out = df.copy()

    for col in ["Creation Date", "WH Ship      (LAPS)"]:
        if col in df_out.columns:
            df_out[col] = pd.to_datetime(df_out[col], errors="coerce")

    for col in ["WO#", "Customer Phone No ", "Origin Vendor ID", "Actual Vendor ID"]:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str).replace("nan", np.nan)

    return df_out
