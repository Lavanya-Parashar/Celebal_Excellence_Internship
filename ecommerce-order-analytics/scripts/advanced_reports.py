import sqlite3
import pandas as pd
import os

os.makedirs("data/reports", exist_ok=True)

conn = sqlite3.connect("ecommerce.db")

def execute_query(query, title, filename):

    print("\n" + "="*60)
    print(title)
    print("="*60)

    df = pd.read_sql_query(query, conn)

    print(df)

    df.to_csv(f"data/reports/{filename}", index=False)

    print(f"\nSaved : {filename}")

query7 = """
SELECT
o.region_code,
DATE(o.order_date) AS order_date,

ROUND(SUM(
oi.quantity*oi.unit_price*
(1-oi.discount_percent/100.0)
),2) AS daily_revenue,

ROUND(

SUM(

SUM(

oi.quantity*oi.unit_price*
(1-oi.discount_percent/100.0)

)

)

OVER(

PARTITION BY o.region_code

ORDER BY DATE(o.order_date)

)

,2)

AS running_total

FROM orders o

JOIN order_items oi

ON o.order_id=oi.order_id

GROUP BY o.region_code,DATE(o.order_date)

ORDER BY o.region_code,DATE(o.order_date);

"""

execute_query(

query7,

"Query 7 : Running Revenue",

"query7_running_revenue.csv"

)

query8 = """
SELECT

category,

product_name,

total_revenue,

DENSE_RANK()

OVER(

PARTITION BY category

ORDER BY total_revenue DESC

)

AS rank_in_category

FROM(

SELECT

p.category,

p.product_name,

ROUND(

SUM(

oi.quantity*oi.unit_price*

(1-oi.discount_percent/100.0)

),2)

AS total_revenue

FROM products p

JOIN order_items oi

ON p.product_id=oi.product_id

GROUP BY p.product_id

);

"""

execute_query(

query8,

"Query 8 : Product Ranking",

"query8_product_ranking.csv"

)

query9 = """
SELECT

customer_id,

order_date,

LAG(order_date)

OVER(

PARTITION BY customer_id

ORDER BY order_date

)

AS previous_order,

ROUND(

JULIANDAY(order_date)-

JULIANDAY(

LAG(order_date)

OVER(

PARTITION BY customer_id

ORDER BY order_date

)

)

,2)

AS days_gap

FROM orders

WHERE customer_id!='UNKNOWN';

"""

execute_query(

query9,

"Query 9 : Order Gap",

"query9_order_gap.csv"

)

query10 = """
WITH monthly_revenue AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.customer_id != 'UNKNOWN'
    GROUP BY o.customer_id, month
),

customer_category AS (
    SELECT *,
        CASE
            WHEN revenue > 10000 THEN 'High'
            WHEN revenue BETWEEN 5000 AND 10000 THEN 'Medium'
            ELSE 'Low'
        END AS customer_segment
    FROM monthly_revenue
)

SELECT
    month,
    customer_segment,
    COUNT(customer_id) AS customer_count
FROM customer_category
GROUP BY month, customer_segment
ORDER BY month;
"""

execute_query(
    query10,
    "Query 10 : Monthly Customer Segmentation",
    "query10_customer_segment.csv"
)

query11 = """
WITH customer_value AS (

SELECT

customer_id,

ROUND(SUM(

oi.quantity*oi.unit_price*
(1-oi.discount_percent/100.0)

),2)

AS total_value

FROM orders o

JOIN order_items oi

ON o.order_id=oi.order_id

WHERE customer_id!='UNKNOWN'

GROUP BY customer_id

)

SELECT

customer_id,

total_value,

NTILE(4)

OVER(

ORDER BY total_value DESC

)

AS quartile,

CASE

WHEN NTILE(4) OVER(ORDER BY total_value DESC)=1 THEN 'Platinum'

WHEN NTILE(4) OVER(ORDER BY total_value DESC)=2 THEN 'Gold'

WHEN NTILE(4) OVER(ORDER BY total_value DESC)=3 THEN 'Silver'

ELSE 'Bronze'

END

AS quartile_label

FROM customer_value;

"""

execute_query(

query11,

"Query 11 : Customer Quartiles",

"query11_customer_quartiles.csv"

)

query12 = """
WITH monthly_revenue AS (

SELECT

strftime('%Y',order_date) year,

strftime('%m',order_date) month,

ROUND(SUM(

oi.quantity*oi.unit_price*
(1-oi.discount_percent/100.0)

),2)

AS revenue

FROM orders o

JOIN order_items oi

ON o.order_id=oi.order_id

GROUP BY year,month

)

SELECT

cur.year,

cur.month,

cur.revenue,

prev.revenue AS prev_year_revenue,

ROUND(

(cur.revenue-prev.revenue)

*100.0/

prev.revenue

,2)

AS yoy_growth_percent

FROM monthly_revenue cur

LEFT JOIN monthly_revenue prev

ON cur.month=prev.month

AND cur.year=CAST(prev.year AS INTEGER)+1;

"""

execute_query(

query12,

"Query 12 : YoY Revenue",

"query12_yoy.csv"

)

query13 = """
WITH customer_categories AS (

SELECT

o.customer_id,

o.order_date,

p.category

FROM orders o

JOIN order_items oi

ON o.order_id=oi.order_id

JOIN products p

ON oi.product_id=p.product_id

WHERE customer_id!='UNKNOWN'

)

SELECT

customer_id,

FIRST_VALUE(category)

OVER(

PARTITION BY customer_id

ORDER BY order_date

)

AS first_category,

LAST_VALUE(category)

OVER(

PARTITION BY customer_id

ORDER BY order_date

ROWS BETWEEN UNBOUNDED PRECEDING

AND UNBOUNDED FOLLOWING

)

AS last_category

FROM customer_categories;

"""

execute_query(

query13,

"Query 13 : Category Shift",

"query13_category_shift.csv"

)

query14 = """
WITH customer_revenue AS (

SELECT

o.customer_id,

ROUND(

SUM(
oi.quantity*oi.unit_price*
(1-oi.discount_percent/100.0)
),2

) AS revenue

FROM orders o

JOIN order_items oi

ON o.order_id=oi.order_id

WHERE customer_id!='UNKNOWN'

GROUP BY customer_id

),

ordered AS(

SELECT

customer_id,

revenue,

SUM(revenue)

OVER(

ORDER BY revenue DESC

)

AS cumulative_revenue,

SUM(revenue)

OVER()

AS total_revenue

FROM customer_revenue

)

SELECT

customer_id,

revenue,

cumulative_revenue,

ROUND(
(cumulative_revenue*100.0)/total_revenue,
2
) AS cumulative_percent

FROM ordered;
"""

execute_query(
query14,
"Query 14 : Cumulative Distribution",
"query14_cumulative_distribution.csv"
)

query15 = """
WITH cohort AS (

SELECT

customer_id,

strftime('%Y-%m',registration_date)

AS cohort_month

FROM customers

),

orders_month AS(

SELECT

customer_id,

strftime('%Y-%m',order_date)

AS order_month

FROM orders

WHERE customer_id!='UNKNOWN'

)

SELECT

c.cohort_month,

o.order_month,

COUNT(DISTINCT o.customer_id)

AS active_customers

FROM cohort c

LEFT JOIN orders_month o

ON c.customer_id=o.customer_id

GROUP BY c.cohort_month,o.order_month

ORDER BY c.cohort_month,o.order_month;
"""

execute_query(
query15,
"Query 15 : Cohort Analysis",
"query15_cohort.csv"
)

query16 = """
SELECT

oi1.product_id

AS product_a,

oi2.product_id

AS product_b,

COUNT(*)

AS times_bought_together

FROM order_items oi1

JOIN order_items oi2

ON oi1.order_id=oi2.order_id

AND oi1.product_id<oi2.product_id

GROUP BY

oi1.product_id,

oi2.product_id

ORDER BY

times_bought_together DESC;
"""

execute_query(
query16,
"Query 16 : Frequently Bought Together",
"query16_product_pairs.csv"
)

conn.close()

print("\nAll Advanced Reports Generated Successfully.")

