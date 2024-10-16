WITH doanh_thu_cte AS (
   SELECT
    TO_CHAR(NGÀY_HẠCH_TOÁN, 'YYYY-MM') AS thang,
    CHI_NHÁNH,
    SUM(DOANH_THU) AS tong_doanh_thu
FROM
    "DỮ_LIỆU_BÁN_HÀNG"
GROUP BY
    TO_CHAR(NGÀY_HẠCH_TOÁN, 'YYYY-MM'),
    CHI_NHÁNH
ORDER BY
    thang, CHI_NHÁNH
)

SELECT
    thang,
    CHI_NHÁNH,
    tong_doanh_thu
FROM
    doanh_thu_cte
ORDER BY
    thang, CHI_NHÁNH