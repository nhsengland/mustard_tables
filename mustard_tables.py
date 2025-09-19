# Import packages
import pandas as pd
import numpy as np

# Bring in data
data = pd.read_csv("data/mustard_tables.csv")

# # Replace any string values with NaN -- this can be renmoved when put into prod
# data['value'] = data['value'].apply(lambda x: np.nan if isinstance(x, str) and not x.replace('.', '', 1).isdigit() else x)

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
    "UHSx"
    ]

# Set dictionary to group metric_names
metric_groups = {
    '12hrs': 'UEC',
    '4hrs': 'UEC',
    '4hrs (MTD)': 'UEC',
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
                           '4hrs',
                           '52ww performance',
                           '52ww performance (MTD)',
                           'DM01'
                           ]

# Set up list for metrics where higher is better
higher_is_better_metrics = ['Cancer 62d',
                            'Cancer FDS',
                            '4hrs (MTD)',
                            'RTT performance',
                            'RTT performance (MTD)',
                            'Time to first OPA'
                            ]

# Concatenate lists with date to match metric_date column
higher_is_worse_metrics = [metric + ' - ' + date for metric in higher_is_worse_metrics for date in data['date'].unique()]
higher_is_better_metrics = [metric + ' - ' + date for metric in higher_is_better_metrics for date in data['date'].unique()]

# Create list of metrics to ignore for actual vs plan comparison
ignore_metrics = ['RTT performance (MTD) - ' + date for date in data['date'].unique()]
ignore_metrics += ['4hrs (MTD) - ' + date for date in data['date'].unique()]
ignore_metrics += ['52ww performance (MTD) - ' + date for date in data['date'].unique()]

# Loop through dataframes
for df in [uec_data, elective_data]:

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

    # Force all columns apart from 'org_name' and 'actual_gt_plan' to be float
    for col in pivot_table.columns:
        if col != 'org_name' or col != 'actual_gt_plan':
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

    # Function to apply mustard background and thicker left border to cells where actual is worse than plan
    def style_actual_vs_plan(row):
        if metric in higher_is_better_metrics:
            return [
                'background-color: #FFC000' if (
                    col[1] == 'actual' and
                    pd.notna(row[col]) and
                    (col[0], 'plan') in row.index and
                    pd.notna(row[(col[0], 'plan')]) and
                    row[col] < row[(col[0], 'plan')]
                ) else ''
                for col in row.index
            ]
        elif metric in higher_is_worse_metrics:
            return [
                'background-color: #FFC000' if (
                    col[1] == 'actual' and
                    pd.notna(row[col]) and
                    (col[0], 'plan') in row.index and
                    pd.notna(row[(col[0], 'plan')]) and
                    row[col] > row[(col[0], 'plan')]
                ) else ''
                for col in row.index
            ]
    
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