# @title
import os
import pandas as pd
import numpy as np

devi1 = r'E:\OneDrive-IBM\OneDrive - IBM\IBM💼\LEARNING👨‍💻\github\repository\public\learning\lenovo-apps\lenovo-develop-test\lenovo-develop-test\uploads\excel\new_WO_Header_Status_-_Labor_Vendor_Updated_Open_WO_ONLY_7-7-2026_4-47-39_PM.xlsx'
devi2 = r'E:\OneDrive-IBM\OneDrive - IBM\IBM💼\LEARNING👨‍💻\github\repository\public\learning\lenovo-apps\lenovo-develop-test\lenovo-develop-test\uploads\excel\Masterfile_-_Cut_Jan_2026_-_Copy.xlsx'
devi3 = r'E:\OneDrive-IBM\OneDrive - IBM\IBM💼\LEARNING👨‍💻\github\repository\public\learning\lenovo-apps\lenovo-develop-test\lenovo-develop-test\uploads\excel\Active_Work_Orders_7-7-2026_4-46-51_PM.xlsx'
devi4 = r'E:\OneDrive-IBM\OneDrive - IBM\IBM💼\LEARNING👨‍💻\github\repository\public\learning\lenovo-apps\lenovo-develop-test\lenovo-develop-test\uploads\excel\Work_Order_Product_Advanced_Find_View_7-7-2026_4-49-03_PM.xlsx'
devi12 = r'E:\OneDrive-IBM\OneDrive - IBM\IBM💼\LEARNING👨‍💻\github\repository\public\learning\lenovo-apps\lenovo-develop-test\lenovo-develop-test\uploads\excel\Vendor-mapping.xlsx'


df_devi1  = pd.read_excel(devi1, sheet_name=0)
df_devi2  = pd.read_excel(devi2, sheet_name=0)
df_devi3  = pd.read_excel(devi3, sheet_name=0)
df_devi4  = pd.read_excel(devi4, sheet_name=0)
df_devi12 = pd.read_excel(devi12, sheet_name=1)


def new_wo_filter_detection(df_devi3_input, df_devi2_input):
    """
    Filters Work Orders from df_devi3_input that are within the last 60 days
    and identifies those that do not exist in df_devi2_input.

    Args:
        df_devi3_input (pd.DataFrame): DataFrame containing 'Work Order ID' and 'Release Date'.
        df_devi2_input (pd.DataFrame): DataFrame containing 'WO#'.

    Returns:
        pd.DataFrame: A DataFrame containing only the new Work Orders from df_devi3_input
                      (last 60 days) that are not present in df_devi2_input, with a flag of 0.
    """
    df_devi3_copy = df_devi3_input.copy()
    df_devi2_copy = df_devi2_input.copy()

    df_devi3_copy['Release Date'] = pd.to_datetime(df_devi3_copy['Release Date'], errors='coerce')
    df_devi3_filtered = df_devi3_copy[df_devi3_copy['Release Date'] >= (pd.to_datetime('today') - pd.Timedelta(days=60))]

    wo_ids_devi3 = df_devi3_filtered['Work Order ID']
    wo_ids_devi2 = df_devi2_copy['WO#']

    # Check if each WO ID from df_devi3 exists in df_devi2
    existance_flags = wo_ids_devi3.isin(wo_ids_devi2).astype(int)

    # Create the new DataFrame
    df_wo_verification = pd.DataFrame({
        'Work Order ID (df_devi3)': wo_ids_devi3,
        'Exists in df_devi2': existance_flags
    })

    # Filter to keep only WOs with value 0 (new WOs)
    new_wo_detected_df = df_wo_verification[df_wo_verification['Exists in df_devi2'] == 0]

    return new_wo_detected_df


def process_new_work_orders(df_devi3_raw, df_new_wo_filtered_ids):
    """
    Consolidates the steps to filter df_devi3 for the last 60 days,
    then further filters it to include only new Work Orders identified in df_new_wo_filtered_ids,
    selects specific columns, and renames them to create df_new_wo_process1.

    Args:
        df_devi3_raw (pd.DataFrame): The original df_devi3 DataFrame containing 'Work Order ID' and 'Release Date'.
        df_new_wo_filtered_ids (pd.DataFrame): DataFrame containing 'Work Order ID (df_devi3)' of new Work Orders.

    Returns:
        pd.DataFrame: df_new_wo_process1 with selected and renamed columns, or an empty DataFrame
                      if df_new_wo_filtered_ids is empty or if no matching columns are found.
    """
    # 1. Ensure 'Release Date' is in datetime format and filter df_devi3_raw for the last 60 days
    df_devi3_copy = df_devi3_raw.copy()
    df_devi3_copy['Release Date'] = pd.to_datetime(df_devi3_copy['Release Date'], errors='coerce')
    df_devi3_filtered_60days = df_devi3_copy[df_devi3_copy['Release Date'] >= (pd.to_datetime('today') - pd.Timedelta(days=60))]

    # 2. Filter df_devi3_filtered_60days using the new Work Order IDs from df_new_wo_filtered_ids
    if not df_new_wo_filtered_ids.empty:
        new_wo_ids = df_new_wo_filtered_ids['Work Order ID (df_devi3)'].unique()
        df_new_wo_process1_temp = df_devi3_filtered_60days[df_devi3_filtered_60days['Work Order ID'].isin(new_wo_ids)].copy()

        # Define the column mapping
        column_mapping = {
            'Release Date': 'Creation Date',
            'Work Order ID': 'WO#',
            'Serial Number': 'SN',
            'Product Description': 'Product',
            'Case': 'Service Order Description',
            'Owner': 'Actual ASP',
            'Labor Vendor Related': 'Origin Vendor ID',
            'Service Delivery Instructions': 'Information'
        }

        # Select and rename the columns to create df_new_wo_process1
        selected_columns = {old_col: new_col for old_col, new_col in column_mapping.items() if old_col in df_new_wo_process1_temp.columns}

        # Check if any columns are left after filtering for existence
        if not selected_columns:
            print("Warning: No matching columns found in df_devi3_filtered_60days for the specified mapping. Returning empty DataFrame.")
            return pd.DataFrame() # Return empty if no columns match

        df_new_wo_process1 = df_new_wo_process1_temp[list(selected_columns.keys())].rename(columns=selected_columns)

        # Format 'Creation Date' column to MM/DD/YYYY as string within the function
        if 'Creation Date' in df_new_wo_process1.columns:
            df_new_wo_process1['Creation Date'] = pd.to_datetime(df_new_wo_process1['Creation Date'], errors='coerce')
            df_new_wo_process1['Creation Date'] = df_new_wo_process1['Creation Date']

        return df_new_wo_process1
    else:
        print("df_new_wo_filtered_ids is empty, so no new Work Orders to process. Returning empty DataFrame.")
        return pd.DataFrame() # Return empty DataFrame if df_new_wo_filtered_ids is empty


# @title
def process_customer_info(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Processes customer information in a DataFrame by combining address and name/email fields,
    and cleaning phone numbers.

    Args:
        df_input (pd.DataFrame): The input DataFrame (e.g., df_devi1) containing raw customer data.

    Returns:
        pd.DataFrame: A new DataFrame with 'Customer Address', 'Customer Name',
                      and 'Customer Phone No ' columns added.
    """
    df_processed = df_input.copy()

    # 1. Combine 'Company Name (Contact) (Contact)' and 'Address 1 (Contact) (Contact)'
    df_processed['Customer Address'] = pd.Series(np.where(
        df_processed['Company Name (Contact) (Contact)'].isna(),
        df_processed['Address 1 (Contact) (Contact)'].fillna(''),
        df_processed['Company Name (Contact) (Contact)'].fillna('') + ', ' + df_processed['Address 1 (Contact) (Contact)'].fillna('')
    )).str.strip()

    # 2. Combine 'Contact Name (Contact) (Contact)' and 'Primary Email (Contact) (Contact)'
    df_processed['Customer Name'] = pd.Series(np.where(
        df_processed[' Contact Name (Contact) (Contact)'].isna(),
        df_processed['Primary Email (Contact) (Contact)'].fillna(''),
        df_processed[' Contact Name (Contact) (Contact)'].fillna('') + ' (' + df_processed['Primary Email (Contact) (Contact)'].fillna('') + ')'
    )).str.strip()

    # 3. Create 'Customer Phone No ' from 'Mobile Phone (Contact) (Contact)'
    df_processed['Customer Phone No '] = df_processed['Mobile Phone (Contact) (Contact)'] \
                                        .astype(str) \
                                        .str.replace(r'[+-]', '', regex=True)

    def format_phone_number(value):
        if pd.isna(value) or str(value).strip() == '':
            return np.nan
        try:
            # Attempt to convert to float to handle both int and float representations
            float_val = float(value)
            # If it's an integer-like float (e.g., 6285158337396.0)
            if float_val == int(float_val):
                return str(int(float_val))
            else:
                # It's a float with a decimal part, keep as string
                return str(float_val)
        except (ValueError, TypeError):
            # If conversion to float fails, it's a non-numeric string, return as is
            return str(value)

    df_processed['Customer Phone No '] = df_processed['Customer Phone No '].apply(format_phone_number)

    return df_processed


def update_actual_asp_from_devi1(df_new_wo_proc1: pd.DataFrame, df_devi1_data: pd.DataFrame) -> pd.DataFrame:
    """
    Updates the 'Actual ASP' column in df_new_wo_proc1 based on matching 'WO#'
    with df_devi1_data's 'Work Order ID' and specific conditions.

    Args:
        df_new_wo_proc1 (pd.DataFrame): The DataFrame to be updated (df_new_wo_process1_final).
        df_devi1_data (pd.DataFrame): The reference DataFrame (df_devi1).

    Returns:
        pd.DataFrame: The DataFrame with the 'Actual ASP' column potentially updated.
    """
    df_result = df_new_wo_proc1.copy()

    # Merge the two dataframes on their respective WO columns
    # using a left merge to keep all rows from df_new_wo_proc1
    merged_df = pd.merge(
        df_result,
        df_devi1_data[['Work Order ID', 'Owner', 'Customer (Labor Vendor Related) (Partner Function)']],
        left_on='WO#',
        right_on='Work Order ID',
        how='left',
        suffixes=('_proc1', '_devi1')
    )

    # Define conditions and choices for updating 'Actual ASP'
    conditions = [
        merged_df['Actual ASP'].fillna('') == merged_df['Owner'].fillna(''), # Condition 1: Actual ASP matches Owner
        merged_df['Actual ASP'].fillna('') == merged_df['Customer (Labor Vendor Related) (Partner Function)'].fillna('') # Condition 2: Actual ASP matches Customer (Labor Vendor Related)
    ]

    choices = [
        merged_df['Actual ASP'], # If condition 1 is true, keep current Actual ASP
        merged_df['Customer (Labor Vendor Related) (Partner Function)'] # If condition 2 is true, use Customer (Labor Vendor Related)
    ]

    # Apply np.select to update 'Actual ASP'
    # The order of conditions matters here for priority.
    df_result['Actual ASP'] = np.select(
        conditions,
        choices,
        default=merged_df['Actual ASP'] # Default to original Actual ASP if no conditions are met
    )

    return df_result

def combine_wo_and_customer_info(
    df_updated_wo: pd.DataFrame,
    df_processed_customer: pd.DataFrame
) -> pd.DataFrame:
    """
    Filters customer information based on Work Orders present in the updated WO DataFrame
    and then merges this information into the updated WO DataFrame.

    Args:
        df_updated_wo (pd.DataFrame): The DataFrame with updated Work Orders (e.g., df_new_wo_process1_updated).
        df_processed_customer (pd.DataFrame): The DataFrame containing processed customer information (e.g., df_devi1_processed).

    Returns:
        pd.DataFrame: A combined DataFrame with WO details and customer information.
    """
    # Extract unique Work Order IDs from the updated WO DataFrame
    wo_ids_to_filter = df_updated_wo['WO#'].unique()

    # Filter the processed customer DataFrame to include only relevant Work Orders
    df_devi1_filtered_for_merge = df_processed_customer[
        df_processed_customer['Work Order ID'].isin(wo_ids_to_filter)
    ].copy()

    # Merge the updated WO DataFrame with the filtered customer information
    df_combined = pd.merge(
        df_updated_wo,
        df_devi1_filtered_for_merge[['Work Order ID', 'Customer Address', 'Customer Name', 'Customer Phone No ']],
        left_on='WO#',
        right_on='Work Order ID',
        how='left'
    )

    # Drop the redundant 'Work Order ID' column from the merge
    df_combined = df_combined.drop(columns=['Work Order ID'])

    return df_combined


# @title
def process_devi4_data(df_devi4_input, df_devi2_input, df_final_combined_input):
    df_devi4_processed = df_devi4_input[['Work Order', 'Work Order Product Status', 'Original Committed Delivery Date', 'Product', 'Description', 'Shipment Date']].copy()
    df_devi4_processed.rename(columns={'Work Order Product Status': 'Status'}, inplace=True)
    df_devi4_processed.rename(columns={'Shipment Date': 'WH Ship      (LAPS)'}, inplace=True)

    # Initialize 'process' column based on the first set of statuses
    status_for_process_1 = ['Delivered', 'Shipped', 'parts in transit']
    df_devi4_processed['process'] = df_devi4_processed['Status'].isin(status_for_process_1).astype(int)

    # Initialize 'Status Part' column
    df_devi4_processed['Status Part'] = None

    # Apply the new condition for 'Shipped' status (case-insensitive)
    shipped_condition = df_devi4_processed['Status'].str.lower() == 'shipped'

    # Update 'Status Part' and 'process' where the condition is true
    df_devi4_processed.loc[shipped_condition, 'Status Part'] = 'waiting part'
    df_devi4_processed.loc[shipped_condition, 'process'] = 2

    # Create 'Product Description' column based on the condition
    product_condition = ~df_devi4_processed['Product'].isin(['OUBHAN2', 'INBHAN1'])
    df_devi4_processed['Part Description'] = np.where(
        product_condition,
        df_devi4_processed['Product'].astype(str) + ' ' + df_devi4_processed['Description'].astype(str),
        np.nan
    )

    # Remove rows with NaN in 'Product Description'
    df_devi4_processed.dropna(subset=['Part Description'], inplace=True)

    df_devi2_filtered_status = df_devi2_input[~df_devi2_input['Status'].isin(['completed', 'cancelled', 'Completed', 'Cancelled'])].copy()

    # Get unique Work Orders from df_final_combined_input
    wo_from_final_combined = df_final_combined_input['WO#'].unique()

    df_devi4_in_devi2 = df_devi4_processed[
        (df_devi4_processed['Work Order'].isin(df_devi2_filtered_status['WO#'])) |
        (df_devi4_processed['Work Order'].isin(wo_from_final_combined))
    ].copy()

    # Group by 'Work Order' and aggregate 'Product Description' by joining unique values
    df_devi4_in_devi2_merged = df_devi4_in_devi2.groupby('Work Order').agg(
        Product_Description=('Part Description', lambda x: ', '.join(x.dropna().unique())),
        # For other columns, take the first non-null value, ensuring all are in (column, aggfunc) tuple format
        **{col: (col, 'first') for col in df_devi4_in_devi2.columns if col not in ['Work Order', 'Part Description']}
    ).reset_index()

    df_devi4_in_devi2_merged = df_devi4_in_devi2_merged.rename(columns={
        'Work Order': 'WO#',
        'Product_Description': 'Part Description'
    })

    return df_devi4_in_devi2_merged


# @title
def consolidate_merged_columns(df_raw):
    """
    Consolidates columns in a DataFrame that resulted from a merge with suffixes
    (e.g., '_devi2', '_new_wo'). It prioritizes non-null values from '_new_wo'
    and fills missing values from '_devi2', then drops the original suffixed columns.

    Args:
        df_raw (pd.DataFrame): The DataFrame with merged columns, potentially containing
                               columns with suffixes like '_devi2' and '_new_wo'.

    Returns:
        pd.DataFrame: A new DataFrame with consolidated columns.
    """
    df_consolidated = df_raw.copy()

    # Identify columns that have been duplicated and suffixed during the merge
    # We're looking for pairs like 'ColumnName_devi2' and 'ColumnName_new_wo'
    suffixed_cols = [col for col in df_consolidated.columns if '_devi2' in col or '_new_wo' in col]

    # Group them by their original column name
    original_cols = sorted(list(set([col.replace('_devi2', '').replace('_new_wo', '') for col in suffixed_cols])))

    for col in original_cols:
        col_devi2 = f'{col}_devi2'
        col_new_wo = f'{col}_new_wo'

        # Check if both suffixed versions of the column exist
        if col_devi2 in df_consolidated.columns and col_new_wo in df_consolidated.columns:
            # Prioritize _new_wo values, fill nulls with _devi2 values
            # If both are null, it will remain null
            df_consolidated[col] = df_consolidated[col_new_wo].fillna(df_consolidated[col_devi2])
            # Drop the suffixed columns now that they are consolidated
            df_consolidated = df_consolidated.drop(columns=[col_devi2, col_new_wo])
        elif col_devi2 in df_consolidated.columns and col not in df_consolidated.columns:
            # If only _devi2 exists, and the consolidated column doesn't, just rename it
            df_consolidated.rename(columns={col_devi2: col}, inplace=True)
        elif col_new_wo in df_consolidated.columns and col not in df_consolidated.columns:
            # If only _new_wo exists, and the consolidated column doesn't, just rename it
            df_consolidated.rename(columns={col_new_wo: col}, inplace=True)

    # For any columns that were not suffixed but appear in common_cols, they would already be fine.
    # We also need to handle the 'WO#' column, which was explicitly excluded from renaming.
    # If 'WO#' was handled in the loop, ensure it's not created as 'WO#_devi2' or 'WO#_new_wo'
    # The current logic correctly excludes 'WO#' from suffixing, so it remains 'WO#' naturally.

    return df_consolidated

def combine_devi2_new_wo_with_consolidation(df_devi2_full, df_new_wo_data):
    """
    Combines specified columns from df_devi2_full (filtered for open WOs)
    and df_new_wo_data, renames them with suffixes, performs an outer merge,
    and consolidates columns using `consolidate_merged_columns`.

    Args:
        df_devi2_full (pd.DataFrame): The full df_devi2 DataFrame.
        df_new_wo_data (pd.DataFrame): The df_new_wo_only DataFrame.

    Returns:
        pd.DataFrame: A new DataFrame with combined and consolidated columns.
    """
    df_devi2_open_only = df_devi2_full[~df_devi2_full['Status'].isin(['completed', 'cancelled', 'Completed', 'Cancelled'])].copy()

    # Define the list of columns to extract from both dataframes
    common_cols = [
        'Creation Date', 'WO#', 'SN', 'Product', 'Service Order Description',
        'Actual ASP', 'Origin Vendor ID', 'Information', 'Customer Address',
        'Customer Name', 'Customer Phone No '
    ]

    # Select and rename columns from df_devi2_open_only
    df_devi2_selected = df_devi2_open_only[common_cols].copy()
    df_devi2_selected.rename(columns={
        col: f'{col}_devi2' for col in common_cols if col != 'WO#'
    }, inplace=True)

    # Select and rename columns from df_new_wo_only
    df_new_wo_only_selected = df_new_wo_data[common_cols].copy()
    df_new_wo_only_selected.rename(columns={
        col: f'{col}_new_wo' for col in common_cols if col != 'WO#'
    }, inplace=True)

    # Perform an outer merge on 'WO#'
    df_combined_devi2_new_wo_raw = pd.merge(
        df_devi2_selected,
        df_new_wo_only_selected,
        on='WO#',
        how='outer'
    )

    # Consolidate the merged columns using the defined function
    df_combined_devi2_new_wo_open = consolidate_merged_columns(df_combined_devi2_new_wo_raw)

    return df_combined_devi2_new_wo_open

def filter_devi2_not_in_devi4(df_devi2_input, df_devi4_merged_input):
    """
    Filters df_devi2 to exclude 'Completed' or 'Cancelled' statuses,
    then further filters to keep rows where 'WO#' is not in df_devi4_merged_input['WO#'].

    Args:
        df_devi2_input (pd.DataFrame): The original df_devi2 DataFrame.
        df_devi4_merged_input (pd.DataFrame): The df_devi4_processed_and_merged DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing WO# from df_devi2_input that are
                      not in df_devi4_merged_input and are not 'Completed'/'Cancelled'.
    """
    df_devi2_filtered_status = df_devi2_input[~df_devi2_input['Status'].isin(['completed', 'cancelled', 'Completed', 'Cancelled'])].copy()

    df_devi2_not_in_devi4 = df_devi2_filtered_status[
        ~df_devi2_filtered_status['WO#'].isin(df_devi4_merged_input['WO#'])
    ].copy()
    return df_devi2_not_in_devi4


def merge_and_reorder_dfs(df_devi4_merged, df_combined_open, final_cols_order):
    """
    Merges df_devi4_merged with df_combined_open and reorders columns.

    Args:
        df_devi4_merged (pd.DataFrame): The dataframe to add columns to (df_devi4_processed_and_merged).
        df_combined_open (pd.DataFrame): The dataframe to take columns from (df_combined_devi2_new_wo_open).
        final_cols_order (list): A list of column names in the desired final order.

    Returns:
        pd.DataFrame: The merged and reordered DataFrame.
    """
    # Create a copy of df_devi4_merged and remove its 'Product' column
    # as the user specified that 'Product' should come from df_combined_open.
    df_devi4_for_merge = df_devi4_merged.copy()
    if 'Product' in df_devi4_for_merge.columns:
        df_devi4_for_merge = df_devi4_for_merge.drop(columns=['Product'])

    # Identify columns from df_combined_open that are in final_cols_order and not already in df_devi4_for_merge
    cols_to_merge_from_combined = [col for col in final_cols_order if col in df_combined_open.columns and col not in df_devi4_for_merge.columns]

    # Include 'WO#' for merging key
    cols_to_merge_from_combined.insert(0, 'WO#')
    cols_to_merge_from_combined = list(dict.fromkeys(cols_to_merge_from_combined)) # Remove duplicates while preserving order

    # Select only the necessary columns from df_combined_open for the merge
    df_combined_open_subset = df_combined_open[cols_to_merge_from_combined]

    # Perform a left merge to add columns from df_combined_open to df_devi4_for_merge
    # 'Product' from df_combined_open_subset will merge directly without suffix as it was removed from df_devi4_for_merge
    df_final_merged = pd.merge(
        df_devi4_for_merge,
        df_combined_open_subset,
        on='WO#',
        how='left',
        suffixes=('_devi4', '_combined') # Suffixes are important to handle potential column name conflicts for other columns
    )

    # Define column consolidation logic for columns that might have suffixes
    # Prioritize values from the '_devi4' (df_devi4_merged) if they exist, otherwise use '_combined'
    for col in final_cols_order:
        # Skip 'Product' as it's already handled by being sourced solely from df_combined_open_subset
        if col == 'Product':
            continue

        if f'{col}_devi4' in df_final_merged.columns and f'{col}_combined' in df_final_merged.columns:
            df_final_merged[col] = df_final_merged[f'{col}_devi4'].fillna(df_final_merged[f'{col}_combined'])
            df_final_merged = df_final_merged.drop(columns=[f'{col}_devi4', f'{col}_combined'])
        elif f'{col}_devi4' in df_final_merged.columns:
            df_final_merged.rename(columns={f'{col}_devi4': col}, inplace=True)
        elif f'{col}_combined' in df_final_merged.columns:
            df_final_merged.rename(columns={f'{col}_combined': col}, inplace=True)


    # Reorder columns to the specified final order, dropping any columns not in final_cols_order
    # and ensuring all final_cols_order columns are present (with NaNs if not found)
    final_df = df_final_merged[final_cols_order].copy()

    # Convert 'Origin Vendor ID' to string type to handle mixed integer/text and NaNs gracefully
    if 'Origin Vendor ID' in final_df.columns:
        def format_vendor_id(value):
            if pd.isna(value):
                return np.nan
            try:
                # Attempt to convert to float to handle both int and float representations
                float_val = float(value)
                # If it's an integer-like float (e.g., 6002321698.0)
                if float_val == int(float_val):
                    return str(int(float_val))
                else:
                    # It's a float with a decimal part
                    return str(float_val)
            except (ValueError, TypeError):
                # If conversion to float fails, it's a non-numeric string
                return str(value)

        final_df['Origin Vendor ID'] = final_df['Origin Vendor ID'].apply(format_vendor_id)

    return final_df


def update_actual_vendor_id(df_final_report, df_devi2_source):
    """
    Updates the 'Actual Vendor ID' and populates 'Origin ASP' in df_final_report
    using matching 'WO#' from df_devi2_source.

    Args:
        df_final_report (pd.DataFrame): The DataFrame to be updated (df_combined_final_report).
        df_devi2_source (pd.DataFrame): The source DataFrame (df_devi2) containing the
                                         correct 'Actual Vendor ID' and 'Origin ASP'.

    Returns:
        pd.DataFrame: The df_final_report DataFrame with 'Actual Vendor ID' and 'Origin ASP' updated.
    """
    df_result = df_final_report.copy()

    # Select necessary columns from df_devi2_source and rename them for merging
    df_devi2_subset = df_devi2_source[['WO#', 'Actual Vendor ID', 'Origin ASP']].copy()
    df_devi2_subset.rename(columns={
        'Actual Vendor ID': 'Actual Vendor ID_from_devi2',
        'Origin ASP': 'Origin ASP_from_devi2'
    }, inplace=True)

    # Merge to bring in the updated information from df_devi2
    merged_df = pd.merge(
        df_result,
        df_devi2_subset,
        on='WO#',
        how='left' # Use left merge to keep all rows from df_result
    )

    # Update the 'Actual Vendor ID' in df_result.
    # Prioritize non-null values from df_result's existing 'Actual Vendor ID' if they exist,
    # otherwise use 'Actual Vendor ID_from_devi2' from merged_df.
    df_result['Actual Vendor ID'] = merged_df['Actual Vendor ID'].fillna(merged_df['Actual Vendor ID_from_devi2'])

    # Add/Update the 'Origin ASP' in df_result.
    # Since df_result might not initially have an 'Origin ASP' column (based on observation),
    # we directly assign the values from 'Origin ASP_from_devi2' which came from df_devi2.
    # This will create the column if it doesn't exist, and populate it. If it exists,
    # it would fill NaNs or overwrite based on the exact merge behavior and existing data.
    df_result['Origin ASP'] = merged_df['Origin ASP_from_devi2']

    # The temporary merged columns ('Actual Vendor ID_from_devi2', 'Origin ASP_from_devi2')
    # are only in 'merged_df' and are used for updating 'df_result'.
    # They are not added to 'df_result' itself, so no need to drop them from 'df_result'.

    return df_result



# @title
def update_asp_information(
    df_final_report,
    df_devi12
):
    """
    VBA equivalent logic:

    Case 1:
        If Origin Vendor ID exists:
            Vendor ID -> Official ASP Name

    Case 2:
        If Origin Vendor ID is blank:
            Actual ASP -> Alias lookup -> Vendor ID
            Vendor ID -> Official ASP Name

    Then:
        Origin ASP = Official ASP Name
        Actual ASP = Official ASP Name
        Actual Vendor ID = Origin Vendor ID
    """

    df_result = df_final_report.copy()
    df_asp = df_devi12.copy()

    # ---------------------------------
    # Standardize lookup fields
    # ---------------------------------

    for col in [
        'Vendor ID',
        'Name 1'
    ]:
        df_asp[col] = (
            df_asp[col]
            .fillna('')
            .astype(str)
            .str.strip()
        )

    # Alias columns (if present)
    alias_cols = []

    for col in ['Name 2', 'Name 3']:
        if col in df_asp.columns:
            df_asp[col] = (
                df_asp[col]
                .fillna('')
                .astype(str)
                .str.strip()
            )
            alias_cols.append(col)

    # ---------------------------------
    # Vendor ID -> ASP Name lookup
    # (equivalent to VLOOKUP(AE,A:B,2,FALSE))
    # ---------------------------------

    vendor_to_name = (
        df_asp
        .drop_duplicates('Vendor ID')
        .set_index('Vendor ID')['Name 1']
        .to_dict()
    )

    # ---------------------------------
    # ASP Name/Alias -> Vendor ID lookup
    # (equivalent to checking B/C/D)
    # ---------------------------------

    name_to_vendor = {}

    for _, row in df_asp.iterrows():

        vendor_id = row['Vendor ID']

        # Official Name
        if row['Name 1']:
            name_to_vendor[row['Name 1']] = vendor_id

        # Aliases
        for alias_col in alias_cols:
            alias_value = row[alias_col]

            if alias_value:
                name_to_vendor[alias_value] = vendor_id

    # ---------------------------------
    # Process each row
    # ---------------------------------

    for idx in df_result.index:

        origin_vendor_id = str(
            df_result.at[idx, 'Origin Vendor ID']
        ).strip()

        # ---------------------------------
        # CASE 1
        # Origin Vendor ID exists
        # ---------------------------------

        if (
            pd.notna(df_result.at[idx, 'Origin Vendor ID'])
            and origin_vendor_id != ''
            and origin_vendor_id.lower() != 'nan'
        ):

            asp_name = vendor_to_name.get(origin_vendor_id)

            if asp_name:

                df_result.at[idx, 'Origin ASP'] = asp_name
                df_result.at[idx, 'Actual ASP'] = asp_name
                df_result.at[idx, 'Actual Vendor ID'] = origin_vendor_id

        # ---------------------------------
        # CASE 2
        # Origin Vendor ID blank
        # ---------------------------------

        else:

            actual_asp = str(
                df_result.at[idx, 'Actual ASP']
            ).strip()

            if actual_asp and actual_asp.lower() != 'nan':

                vendor_id = name_to_vendor.get(actual_asp)

                if vendor_id:

                    asp_name = vendor_to_name.get(vendor_id)

                    if asp_name:

                        df_result.at[idx, 'Origin Vendor ID'] = vendor_id
                        df_result.at[idx, 'Actual Vendor ID'] = vendor_id

                        df_result.at[idx, 'Origin ASP'] = asp_name
                        df_result.at[idx, 'Actual ASP'] = asp_name

    return df_result

def format_columns_for_df_combined_asp_vendor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formats specific columns in the df_combined_asp_vendor DataFrame to desired types.

    Args:
        df (pd.DataFrame): The DataFrame to format.

    Returns:
        pd.DataFrame: The DataFrame with formatted columns.
    """
    df_formatted = df.copy()

    # Convert date columns to datetime, coercing errors to NaT
    date_cols = ['Creation Date', 'WH Ship      (LAPS)']
    for col in date_cols:
        if col in df_formatted.columns:
            df_formatted[col] = pd.to_datetime(df_formatted[col], errors='coerce')

    # Convert integer/text columns to string type
    str_cols = ['WO#', 'Customer Phone No ', 'Origin Vendor ID', 'Actual Vendor ID']
    for col in str_cols:
        if col in df_formatted.columns:
            # Convert to string, then handle NaN values explicitly to avoid 'nan' string
            df_formatted[col] = df_formatted[col].astype(str).replace('nan', np.nan)

    return df_formatted


##### MAIN FUNCTION CALL #####
### function new_wo_filter_detection 
df_new_wo = new_wo_filter_detection(df_devi3, df_devi2)

### function process_new_work_orders
df_new_wo_process1_final = process_new_work_orders(df_devi3, df_new_wo)

### function combine_wo_and_customer_info
df_devi1_processed = process_customer_info(df_devi1)
df_new_wo_process1_updated = update_actual_asp_from_devi1(df_new_wo_process1_final, df_devi1)
df_new_wo_only = combine_wo_and_customer_info(df_new_wo_process1_updated, df_devi1_processed)

### function df_devi4_processed_and_merged
df_devi4_processed_and_merged = process_devi4_data(df_devi4, df_devi2, df_new_wo_only)

df_devi2_open_only = df_devi2[~df_devi2['Status'].isin(['completed', 'cancelled', 'Completed', 'Cancelled'])]

# function combine_devi2_new_wo_with_consolidation
df_combined_devi2_new_wo_open = combine_devi2_new_wo_with_consolidation(df_devi2, df_new_wo_only)

# function filter_devi2_not_in_devi4
filtered_devi2_df = filter_devi2_not_in_devi4(df_devi2, df_devi4_processed_and_merged)

# Define the desired final column order
final_columns_order = [
    'Creation Date', 'WO#', 'SN', 'Product', 'Status', 'Service Order Description',
    'Part Description', 'Actual ASP', 'Origin Vendor ID', 'Information',
    'Customer Address', 'Customer Name', 'Customer Phone No ', 'Status Part', 'WH Ship      (LAPS)', 'process'
]

# function merge_and_reorder_dfs
df_final_consolidated = merge_and_reorder_dfs(df_devi4_processed_and_merged, df_combined_devi2_new_wo_open, final_columns_order)

# function update_actual_vendor_id
# Columns will be aligned by name, and missing columns will be filled with NaN
df_combined_final_report = pd.concat([filtered_devi2_df, df_final_consolidated], ignore_index=True)
df_combined_final_report = update_actual_vendor_id(df_combined_final_report, df_devi2)

# function update_asp_information
df_combined_final_report = update_asp_information(
    df_combined_final_report,
    df_devi12
)

# function format_columns_for_df_combined_asp_vendor
df_combined_asp_vendor_formatted = format_columns_for_df_combined_asp_vendor(df_combined_final_report)

# export excel files
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_file_path = os.path.join(_BASE_DIR, '..', '..', '..', 'excels', 'df_combined_final_report.xlsx')
df_combined_final_report.to_excel(output_file_path, index=False)


