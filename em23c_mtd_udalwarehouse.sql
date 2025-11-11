with rawdata as (
SELECT
FORMAT(DATEADD(MONTH, DATEDIFF(MONTH, 0, [PeriodDateTimeStart]),0), 'MMM-yy') monthformatted,
DATEADD(MONTH, DATEDIFF(MONTH, 0, [PeriodDateTimeStart]),0) monthstart,
OrgCode as orgcode,
SUM(CASE WHEN metricid = 28 THEN CAST([MetricValue] AS float) END) [numerator], -- in seconds
SUM(CASE WHEN metricid = 27 THEN CAST([MetricValue] AS float) END) [denominator]

FROM
[Reporting_DCF_EmergencyCare_manual].[DCF_EmergencyCare_NHSI_Ambulance_Dashboard_Metrics]

WHERE
[MetricID] in (27,28) -- 27 incidents in seconds and 28 C2 incidents
and orgcode in ('RYE','RYD') -- SCAS and SECAMB
and perioddatetimestart >= '2025-04-01'

GROUP BY
FORMAT(DATEADD(MONTH, DATEDIFF(MONTH, 0, [PeriodDateTimeStart]),0), 'MMM-yy'),
DATEADD(MONTH, DATEDIFF(MONTH, 0, [PeriodDateTimeStart]),0),
orgcode
)

select
monthformatted,
monthstart,
orgcode,
numerator/denominator as [value]

from rawdata

union

select
monthformatted,
monthstart,
'Y59' as orgcode,
SUM(numerator)/ -- in seconds
SUM(denominator) as [value]

FROM rawdata

group by
monthformatted,
monthstart