# Import packages
import pandas as pd
import numpy as np
import datetime as dt

# Bring in data
data = pd.read_csv("data/mustard_tables.csv")

# Bring in cat2 data
cat2_data = pd.read_csv("data/em23c_output.csv")

# Bring in cat2 plans data
cat2_plans = pd.read_csv("data/cat2_plans.csv")

# # Get date into mmm-yy format
# cat2_plans['date'] = pd.to_datetime(data['date'], format='%d/%m/%Y').dt.strftime('%b-%y')

# Rename monthdate as date and orgcode as org_name
cat2_data = cat2_data.rename(columns={'monthformatted': 'date',
                                      'orgcode': 'org_name',
                                      'value': 'actual'
                                      })
# Rename org_name values
cat2_data['org_name'] = cat2_data['org_name'].replace({'RYD': ' SECAM',
                                                       'RYE': ' SCAS',
                                                       'Y59': 'SE Region'
                                                         })
# Filter for latest monthstart
latest_monthstart = cat2_data['monthstart'].max()
cat2_data = cat2_data[cat2_data['monthstart'] == latest_monthstart]
# Drop monthstart column
cat2_data = cat2_data.drop(columns=['monthstart'])
# Create metric_name, variable and metric_type columns, to match mustard data
# cat2_data['metric_name'] = 'Cat2 (MTD)'
cat2_data['variable'] = 'value'
# cat2_data['metric_type'] = 'actual'
# Amend value column to be numeric minutes
cat2_data['actual'] = pd.to_numeric(cat2_data['actual'], errors='coerce') / 60
# Remove white space from start of org_name values
cat2_data['org_name'] = cat2_data['org_name'].str.strip()

# Amend cat2_plans value column to be numeric minutes
cat2_plans['plan'] = pd.to_numeric(cat2_plans['plan'], errors='coerce') / 60

# Join cat2 plans to cat2 data
cat2_data = pd.merge(cat2_data, cat2_plans, 
                     on=['date', 'org_name', 'metric_name'], 
                     how='left'
                     )

# Unpivot cat2_data to show plan and value in variable column
cat2_data = pd.melt(cat2_data,
                    id_vars=['date', 'org_name', 'metric_name', 'variable'],
                    value_vars=['actual', 'plan'],
                    var_name='metric_type',
                    value_name='value'
                    )

# Make variable column values same as metric_type values
cat2_data['variable'] = cat2_data['metric_type']

# Union the two dataframes together
data = pd.concat([data, cat2_data], ignore_index=True)

# Set custom order for org_name
custom_order = [
    "SE Region",
    "BOB ICS",
    "BHT",
    "OUH",
    "RBH",
    "Frimley ICS",
    "Frimley",
    "HIOW ICS",
    "HHFT",
    "IOW",
    "PHU",
    "UHSotn",
    "KM ICS",
    "DGT",
    "EKH",
    "MTW",
    "MedwayFT",
    "Surrey ICS",
    "ASP",
    "RSCH",
    "SASH",
    "Sussex ICS",
    "ESH",
    "QVH",
    "UHSx",
    "SCAS",
    "SECAM"
    ]

# Set dictionary to group metric_names
metric_groups = {
    '12hrs': 'UEC',
    '4hrs': 'UEC',
    '4hrs (MTD)': 'UEC',
    'Cat2 (MTD)': 'UEC',
    'Cat2 (YTD)': 'UEC',
    '52ww performance': 'Elective',
    '52ww performance (MTD)': 'Elective',
    'Cancer 62d': 'Elective',
    'Cancer FDS': 'Elective',
    'DM01': 'Elective',
    'RTT performance': 'Elective',
    'RTT performance (MTD)': 'Elective',
    'Time to first OPA': 'Elective'
    }

# Map metric_names to their groups
data['metric_group'] = data['metric_name'].map(metric_groups)
# .fillna(data['metric_name'])

# Create new column, concatenating variable and date
data['metric_date'] = data['metric_name'] + ' - ' + data['date']

# Amend 'value' to 'actual' in 'variable' column
data['variable'] = data['variable'].replace({'value': 'actual'})

# Split UEC and elective up to separate dataframes
uec_data = data[data['metric_group'] == 'UEC'].copy()
elective_data = data[data['metric_group'] == 'Elective'].copy()

# Set up list for metrics where higher is worse
higher_is_worse_metrics = ['12hrs',
                           'Cat2 (MTD)',
                           'Cat2 (YTD)',
                           '52ww performance',
                           '52ww performance (MTD)',
                           'DM01'
                           ]

# Set up list for metrics where higher is better
higher_is_better_metrics = ['Cancer 62d',
                            'Cancer FDS',
                            '4hrs',
                            '4hrs (MTD)',
                            'RTT performance',
                            'RTT performance (MTD)',
                            'Time to first OPA'
                            ]

# Concatenate lists with date to match metric_date column
higher_is_worse_metrics = [metric + ' - ' + date for metric in higher_is_worse_metrics for date in data['date'].unique()]
higher_is_better_metrics = [metric + ' - ' + date for metric in higher_is_better_metrics for date in data['date'].unique()]

# # Create list of metrics to ignore for actual vs plan comparison
# ignore_metrics = ['RTT performance (MTD) - ' + date for date in data['date'].unique()]
# ignore_metrics += ['4hrs (MTD) - ' + date for date in data['date'].unique()]
# ignore_metrics += ['52ww performance (MTD) - ' + date for date in data['date'].unique()]

# # Set order of columns for final output - note this works even when splitting by metric_group
# col_custom_order_uec = pd.MultiIndex.from_tuples([
#     # UEC metrics
#     ('12hrs - ' + data['date'].unique()[0], 'actual'),
#     ('12hrs - ' + data['date'].unique()[0], 'plan'),
#     ('4hrs - ' + data['date'].unique()[0], 'actual'),
#     ('4hrs - ' + data['date'].unique()[0], 'plan'),
#     ('4hrs (MTD) - ' + data['date'].unique()[0], 'actual'),
#     ('4hrs (MTD) - ' + data['date'].unique()[0], 'plan'),
#     ('Cat2 (MTD) - ' + data['date'].unique()[0], 'actual'),
#     ('Cat2 (MTD) - ' + data['date'].unique()[0], 'plan'),
#     ('12hrs - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('4hrs - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('4hrs (MTD) - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('Cat2 (MTD) - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ])
# col_custom_order_elective = pd.MultiIndex.from_tuples([
#     # Elective metrics
#     ('RTT performance - ' + data['date'].unique()[0], 'actual'),
#     ('RTT performance - ' + data['date'].unique()[0], 'plan'),
#     ('RTT performance - ' + data['date'].unique()[0], 'numerator_actual'),
#     ('RTT performance - ' + data['date'].unique()[0], 'numerator_plan'),
#     ('RTT performance (MTD) - ' + data['date'].unique()[0], 'actual'),
#     ('RTT performance (MTD) - ' + data['date'].unique()[0], 'plan'),
#     ('52ww performance - ' + data['date'].unique()[0], 'actual'),
#     ('52ww performance - ' + data['date'].unique()[0], 'plan'),
#     ('52ww performance (MTD) - ' + data['date'].unique()[0], 'actual'),
#     ('52ww performance (MTD) - ' + data['date'].unique()[0], 'plan'),
#     ('Time to first OPA - ' + data['date'].unique()[0], 'actual'),
#     ('Time to first OPA - ' + data['date'].unique()[0], 'plan'),
#     ('Cancer FDS - ' + data['date'].unique()[0], 'actual'),
#     ('Cancer FDS - ' + data['date'].unique()[0], 'plan'),
#     ('Cancer 62d - ' + data['date'].unique()[0], 'actual'),
#     ('Cancer 62d - ' + data['date'].unique()[0], 'plan'),
#     ('DM01 - ' + data['date'].unique()[0], 'actual'),
#     ('DM01 - ' + data['date'].unique()[0], 'plan'),
#     ('RTT performance - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('RTT performance (MTD) - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('52ww performance - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('DM01 - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('52ww performance (MTD) - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('Time to first OPA - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('Cancer FDS - ' + data['date'].unique()[0], 'actual_gt_plan'),
#     ('Cancer 62d - ' + data['date'].unique()[0], 'actual_gt_plan')
#     ])

# Loop through dataframes
for df in [elective_data, uec_data]:

    # Get first unique metric_group value for naming
    df_name = df['metric_group'].iloc[0].lower()

    # Create pivot table
    pivot_table = pd.pivot_table(df,
                                values='value',
                                index=['org_name'],
                                columns=['metric_date', 'variable'],
                                aggfunc='sum'
                                )
            
    # Reindex the pivot table to the custom order
    pivot_table = pivot_table.reindex(custom_order)

    # # Reindex columns to col_custom_order
    # if df_name == "uec":
    #     pivot_table = pivot_table.reindex(columns=col_custom_order_uec, fill_value=np.nan)
    # else:
    #     pivot_table = pivot_table.reindex(columns=col_custom_order_elective, fill_value=np.nan)

    # Force all columns apart from 'org_name' and 'actual_gt_plan' to be float
    for col in pivot_table.columns:
        if col != 'org_name' or col != 'actual_gt_plan' or col.startswith('Cat2 (MTD)'):
            pivot_table[col] = pd.to_numeric(pivot_table[col], errors='coerce')

    # Create column for each metric_name to show where actual is worse than plan
    def actual_greater_than_plan(row, metric):
        if metric in higher_is_better_metrics:
            actual = row.get((metric, 'actual'), np.nan)
            plan = row.get((metric, 'plan'), np.nan)
            if pd.notna(actual) and pd.notna(plan) and actual < plan:
                return True
            return False
        elif metric in higher_is_worse_metrics:
            actual = row.get((metric, 'actual'), np.nan)
            plan = row.get((metric, 'plan'), np.nan)
            if pd.notna(actual) and pd.notna(plan) and actual > plan:
                return True
            return False

    # Apply the function to each metric_name
    for metric in df['metric_date'].unique():
        pivot_table[(metric, 'actual_gt_plan')] = pivot_table.apply(lambda row: actual_greater_than_plan(row, metric), axis=1)

    def minutes_to_mmss(x):
        try:
            if pd.isna(x):
                return ""
            minutes = int(x)
            seconds = int(round((x - minutes) * 60))
            return f"{minutes:02d}:{seconds:02d}"
        except Exception:
            return ""

    # After creating the pivot_table, format Cat2 (MTD) columns:
    if 'Cat2 (MTD)' in df['metric_name'].values:
        for col in pivot_table.columns:
            if col[0].startswith('Cat2') and col[1] in ['actual', 'plan']:
                pivot_table[col] = pivot_table[col].apply(minutes_to_mmss)

    # Function to apply mustard background and thicker left border to cells where actual is worse than plan
    def style_actual_vs_plan(row):
        styles = []
        for col in row.index:
            metric = col[0]
            if metric in higher_is_better_metrics:
                if (
                    col[1] == 'actual'
                    and pd.notna(row[col])
                    and (metric, 'plan') in row.index
                    and pd.notna(row[(metric, 'plan')])
                    and row[col] < row[(metric, 'plan')]
                ):
                    styles.append('background-color: #FFC000')
                else:
                    styles.append('')
            elif metric in higher_is_worse_metrics:
                if (
                    col[1] == 'actual'
                    and pd.notna(row[col])
                    and (metric, 'plan') in row.index
                    and pd.notna(row[(metric, 'plan')])
                    and row[col] > row[(metric, 'plan')]
                ):
                    styles.append('background-color: #FFC000')
                else:
                    styles.append('')
            else:
                styles.append('')
        return styles
    
    # Apply percentage for appropriate columns
    def percent_or_number(x):
        try:
            if pd.isna(x):
                return ""
            if x == True or x == False:
                return ""
            x = float(x)
            if abs(x) < 1:
                return f"{x*100:.1f}%"
            else:
                return f"{x:,.0f}"
        except Exception:
            return x
        
    # Function to apply mustard background to cells actual_gt_plan is equal to 1
    def highlight_flagged_cells(row):  
        return [
            'background-color: #FFC000' if (
                col[1] == 'actual_gt_plan' and row[col] == True
            ) else ''
            for col in row.index
        ]
    
    # # Set table styles
    # table_styles_extra = [
    #     {'selector': 'table', 'props': [
    #         ('margin', '40px auto'),
    #         ('border-collapse', 'separate'),
    #         ('border-spacing', '0'),
    #         ('box-shadow', '0 4px 24px rgba(0,0,0,0.10)'),
    #         ('border-radius', '12px'),
    #         ('overflow', 'hidden'),
    #         ('background-color', '#fff'),
    #         ('font-family', 'Arial'),
    #     ]},
    #     {'selector': 'caption', 'props': [
    #         ('caption-side', 'top'),
    #         ('font-size', '1.3em'),
    #         ('font-weight', 'bold'),
    #         ('padding', '12px'),
    #         ('color', '#333'),
    #         ('letter-spacing', '1px'),
    #         ('background', '#f9f9f9'),
    #         ('border-radius', '12px 12px 0 0'),
    #     ]},
    #     {'selector': 'thead th', 'props': [
    #         ('position', 'sticky'),
    #         ('top', '0'),
    #         ('z-index', '2'),
    #         ('background-color', '#f2f2f2'),
    #         ('color', '#333'),
    #         ('font-weight', 'bold'),
    #         ('font-family', 'Arial'),
    #         ('font-size', '13px'),
    #         ('border-bottom', '2px solid #FFC000'),
    #         ('padding', '10px 8px'),
    #     ]},
    #     {'selector': 'tbody td', 'props': [
    #         ('padding', '8px'),
    #         ('border', '1px solid #ddd'),
    #         ('color', 'black'),
    #         ('font-family', 'Arial'),
    #         ('font-size', '12px'),
    #         ('background-color', '#fff'),
    #         ('transition', 'background 0.2s'),
    #     ]},
    #     {'selector': 'tbody tr:nth-child(even)', 'props': [
    #         ('background-color', '#f7fafc'),
    #     ]},
    #     {'selector': 'tbody tr:nth-child(odd)', 'props': [
    #         ('background-color', '#fdf6e3'),
    #     ]},
    #     {'selector': 'tbody tr:hover', 'props': [
    #         ('background-color', '#ffe9b3'),
    #     ]},
    #     {'selector': '.level0', 'props': [
    #         ('border-left', '3px solid #666'),
    #         ('border-right', '3px solid #666'),
    #         ('font-family', 'Arial'),
    #         ('font-size', '12px'),
    #     ]},
    # ]

    # Apply styling to the pivot table html output
    styled_pivot_table = (
        pivot_table.style
            .apply(style_actual_vs_plan, axis=1) # Apply mustard background
            .apply(highlight_flagged_cells, axis=1) # Apply mustard background
            .set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#f2f2f2'), ('color', '#333'), ('font-weight', 'bold'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': 'td', 'props': [('padding', '8px'), ('border', '1px solid #ddd'), ('color', 'black'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#f9f9f9')]},
                {'selector': 'tr:nth-child(odd)', 'props': [('background-color', "#f5f5f5e6")]},
                {'selector': 'tr:hover', 'props': [('background-color', '#f1f1f1')]},
                # Thicker borders for metric_name groups (top-level column headers)
                {'selector': '.level0', 'props': [('border-left', '3px solid #666'), ('border-right', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                # Thicker borders for all org_names with 'ICS' in the name
                {'selector': '.row0', 'props': [('border-top', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': '.row1', 'props': [('border-top', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': '.row5', 'props': [('border-top', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': '.row7', 'props': [('border-top', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': '.row12', 'props': [('border-top', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': '.row17', 'props': [('border-top', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': '.row21', 'props': [('border-top', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                {'selector': '.row25', 'props': [('border-top', '3px solid #666'), ('font-family', 'Arial'), ('font-size', '12px')]},
                ], overwrite=False)
            .set_properties(**{
                'text-align': 'center',
                'color': 'black',
                'font': 'Arial',
                'font-size': '12px',
                'min-width': '50px',
                'max-width': '50px',
                'width': '50px',
                'height': '5px'
                })
            .set_caption("Mustard Data Pivot Table")
            .format(percent_or_number)
    )

    # Export the styled table to an HTML file
    styled_pivot_table.to_html(f"mustard_pivot_table_{df_name}.html")

    # Export the pivot table to an Excel file
    pivot_table.to_excel(f"mustard_pivot_table_{df_name}.xlsx", engine='openpyxl')

    # Display the styled table in a Jupyter Notebook (if applicable)
    styled_pivot_table