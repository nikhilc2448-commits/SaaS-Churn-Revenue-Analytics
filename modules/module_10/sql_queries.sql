-- MODULE 10 - SQL ANALYSIS

CREATE DATABASE IF NOT EXISTS saas_churn;
USE saas_churn;

-- RENAME TABLE
--     saas_customers_cleaned TO saas_customers,
--     saas_subscriptions_cleaned TO saas_subscriptions,
--     saas_tickets_cleaned TO saas_tickets,
--     saas_usage_cleaned TO saas_usage;

    
-- Q1 - Customer revenue summary
-- JOIN + GROUP BY

SELECT
    c.CustomerID,
    c.CompanyName,
    c.Industry,
    SUM(s.MRR) AS TotalMRR
FROM saas_customers c
LEFT JOIN saas_subscriptions s
    ON c.CustomerID = s.CustomerID
GROUP BY
    c.CustomerID,
    c.CompanyName,
    c.Industry
ORDER BY TotalMRR DESC;


-- Q2 - Revenue by plan
-- GROUP BY

SELECT
    PlanName,
    COUNT(*) AS SubscriptionCount,
    SUM(MRR) AS TotalMRR,
    AVG(MRR) AS AverageMRR
FROM saas_subscriptions
GROUP BY PlanName
ORDER BY TotalMRR DESC;


-- Q3 - Industries with high revenue
-- JOIN + GROUP BY + HAVING

SELECT
    c.Industry,
    COUNT(DISTINCT c.CustomerID) AS Customers,
    SUM(s.MRR) AS TotalMRR
FROM saas_customers c
JOIN saas_subscriptions s
    ON c.CustomerID = s.CustomerID
GROUP BY c.Industry
HAVING SUM(s.MRR) > 5000
ORDER BY TotalMRR DESC;


-- Q4 - Customer value category
-- CASE

SELECT
    c.CustomerID,
    c.CompanyName,
    SUM(s.MRR) AS TotalMRR,
    CASE
        WHEN SUM(s.MRR) >= 1000 THEN 'High Value'
        WHEN SUM(s.MRR) >= 500 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS CustomerValue
FROM saas_customers c
LEFT JOIN saas_subscriptions s
    ON c.CustomerID = s.CustomerID
GROUP BY
    c.CustomerID,
    c.CompanyName
ORDER BY TotalMRR DESC;


-- Q5 - Customers above average MRR
-- SUBQUERY

SELECT
    c.CustomerID,
    c.CompanyName,
    SUM(s.MRR) AS TotalMRR
FROM saas_customers c
JOIN saas_subscriptions s
    ON c.CustomerID = s.CustomerID
GROUP BY
    c.CustomerID,
    c.CompanyName
HAVING SUM(s.MRR) > (
    SELECT AVG(MRR)
    FROM saas_subscriptions
);


-- Q6 - Customer usage summary
-- CTE + JOIN

WITH usage_summary AS (
    SELECT
        CustomerID,
        AVG(Logins) AS AverageLogins,
        AVG(ActiveUsers) AS AverageActiveUsers,
        AVG(SessionMinutes) AS AverageSessionMinutes
    FROM saas_usage
    GROUP BY CustomerID
)

SELECT
    c.CustomerID,
    c.CompanyName,
    u.AverageLogins,
    u.AverageActiveUsers,
    u.AverageSessionMinutes
FROM saas_customers c
JOIN usage_summary u
    ON c.CustomerID = u.CustomerID
ORDER BY u.AverageLogins DESC;


-- Q7 - Rank customers by MRR
-- WINDOW FUNCTION

SELECT
    c.CustomerID,
    c.CompanyName,
    SUM(s.MRR) AS TotalMRR,
    RANK() OVER (
        ORDER BY SUM(s.MRR) DESC
    ) AS RevenueRank
FROM saas_customers c
JOIN saas_subscriptions s
    ON c.CustomerID = s.CustomerID
GROUP BY
    c.CustomerID,
    c.CompanyName;


-- Q8 - Find orphan subscriptions
-- LEFT JOIN + orphan record handling

SELECT
    s.SubscriptionID,
    s.CustomerID,
    s.PlanName,
    s.MRR
FROM saas_subscriptions s
LEFT JOIN saas_customers c
    ON s.CustomerID = c.CustomerID
WHERE c.CustomerID IS NULL;