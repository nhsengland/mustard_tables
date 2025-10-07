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
    # SE Region
    'SE Region',
    #BOB
    'Buckinghamshire, Oxfordshire And Berkshire West ICS',
    'Buckinghamshire Healthcare NHS Trust',
    'Oxford University Hospitals NHS Foundation Trust',
    'Royal Berkshire NHS Foundation Trust',
    'Berks Health',
    'BHT',
    'OHealth',
    #Frimley
    'Frimley Health & Care ICS',
    'Frimley Health NHS Foundation Trust',
    #HIOW
    'Hampshire And The Isle Of Wight ICS',
    'Hampshire Hospitals NHS Foundation Trust',
    'Isle of Wight NHS Trust',
    'Portsmouth Hospitals University National Health Service Trust',
    'University Hospital Southampton NHS Foundation Trust',
    'HIOW FT',#this was Southern Health and is now HIOW trust
    #KM
    'Kent And Medway ICS', 
    'Dartford And Gravesham NHS Trust',
    'East Kent Hospitals University NHS Foundation Trust',
    'Maidstone And Tunbridge Wells NHS Trust',
    'Medway NHS Foundation Trust',
    'KM SCP',
    'KCH',
    #Surrey
    'Surrey Heartlands Health & Care Partnership ICS',
    'Ashford And St Peters Hospitals NHS Foundation Trust',
    'Royal Surrey County Hospital NHS Foundation Trust',
    'Surrey And Sussex Healthcare NHS Trust',
    'SBorders',
    'SECAMB',
    #Sussex
    'Sussex Health And Care Partnership ICS',
    'East Sussex Healthcare NHS Trust',
    'Queen Victoria Hospital NHS Foundation Trust',
    'University Hospitals Sussex NHS Foundation Trust',
    'SxPartnership',
    # Amb trusts
    "SCAS",
    "SECAM"
    ]

# Set dictionary to group metric_names
metric_groups = {
    '12hrs': 'UEC',
    '12hrs performance (MTD)': 'UEC',
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
                           '12hrs performance (MTD)',
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

first_dates = data.groupby('metric_name')['date'].min().to_dict()

# Set order of columns for final output - note this works even when splitting by metric_group
col_custom_order_uec = pd.MultiIndex.from_tuples([
    # UEC metrics
    ('4hrs - ' + first_dates['4hrs'], 'actual'),
    ('4hrs - ' + first_dates['4hrs'], 'plan'),
    ('4hrs (MTD) - ' + first_dates['4hrs (MTD)'], 'actual'),
    ('4hrs (MTD) - ' + first_dates['4hrs (MTD)'], 'plan'),
    ('12hrs - ' + first_dates['12hrs'], 'actual'),
    ('12hrs - ' + first_dates['12hrs'], 'plan'),
    ('12hrs - ' + first_dates['12hrs'], 'actual_numerator'),
    ('12hrs - ' + first_dates['12hrs'], 'plan_numerator'),
    ('12hrs performance (MTD) - ' + first_dates['12hrs performance (MTD)'], 'actual'),
    ('12hrs performance (MTD) - ' + first_dates['12hrs performance (MTD)'], 'plan'),
    ('Cat2 (MTD) - ' + first_dates['Cat2 (MTD)'], 'actual'),
    ('Cat2 (MTD) - ' + first_dates['Cat2 (MTD)'], 'plan'),
    ('Cat2 (YTD) - ' + first_dates['Cat2 (YTD)'], 'actual'),
    ('Cat2 (YTD) - ' + first_dates['Cat2 (YTD)'], 'plan'),
    ('4hrs - ' + first_dates['4hrs'], 'actual_gt_plan'),
    ('4hrs (MTD) - ' + first_dates['4hrs (MTD)'], 'actual_gt_plan'),
    ('12hrs - ' + first_dates['12hrs'], 'actual_gt_plan'),
    ('Cat2 (MTD) - ' + first_dates['Cat2 (MTD)'], 'actual_gt_plan'),
    ('Cat2 (YTD) - ' + first_dates['Cat2 (YTD)'], 'actual_gt_plan'),
    ])
col_custom_order_elective = pd.MultiIndex.from_tuples([
    # Elective metrics
    ('RTT performance - ' + first_dates['RTT performance'], 'actual'),
    ('RTT performance - ' + first_dates['RTT performance'], 'plan'),
    ('RTT performance (MTD) - ' + first_dates['RTT performance (MTD)'], 'actual'),
    ('RTT performance (MTD) - ' + first_dates['RTT performance (MTD)'], 'plan'),
    ('52ww performance - ' + first_dates['52ww performance'], 'actual'),
    ('52ww performance - ' + first_dates['52ww performance'], 'plan'),
    ('52ww performance (MTD) - ' + first_dates['52ww performance (MTD)'], 'actual'),
    ('52ww performance (MTD) - ' + first_dates['52ww performance (MTD)'], 'plan'),
    ('Time to first OPA - ' + first_dates['Time to first OPA'], 'actual'),
    ('Time to first OPA - ' + first_dates['Time to first OPA'], 'plan'),
    ('Cancer FDS - ' + first_dates['Cancer FDS'], 'actual'),
    ('Cancer FDS - ' + first_dates['Cancer FDS'], 'plan'),
    ('Cancer 62d - ' + first_dates['Cancer 62d'], 'actual'),
    ('Cancer 62d - ' + first_dates['Cancer 62d'], 'plan'),
    ('DM01 - ' + first_dates['DM01'], 'actual'),
    ('DM01 - ' + first_dates['DM01'], 'plan'),
    ('RTT performance - ' + first_dates['RTT performance'], 'actual_gt_plan'),
    ('RTT performance (MTD) - ' + first_dates['RTT performance (MTD)'], 'actual_gt_plan'),
    ('52ww performance - ' + first_dates['52ww performance'], 'actual_gt_plan'),
    ('DM01 - ' + first_dates['DM01'], 'actual_gt_plan'),
    ('52ww performance (MTD) - ' + first_dates['52ww performance (MTD)'], 'actual_gt_plan'),
    ('Time to first OPA - ' + first_dates['Time to first OPA'], 'actual_gt_plan'),
    ('Cancer FDS - ' + first_dates['Cancer FDS'], 'actual_gt_plan'),
    ('Cancer 62d - ' + first_dates['Cancer 62d'], 'actual_gt_plan')
    ])

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

    # Remove rows where all values are NaN
    pivot_table = pivot_table.dropna(how='all')

    # Reindex columns to col_custom_order
    if df_name == "uec":
        pivot_table = pivot_table.reindex(columns=col_custom_order_uec)
    else:
        pivot_table = pivot_table.reindex(columns=col_custom_order_elective)

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