
  
  create or replace view c##BAI_TEST.personal_monthly_revenue as
    WITH doanh_thu_pe AS (
    SELECT
        TO_CHAR(DỮ_LIỆU_BÁN_HÀNG.NGÀY_HẠCH_TOÁN, 'YYYY-MM') AS thang,
        DỮ_LIỆU_BÁN_HÀNG.MÃ_NHÂN_VIÊN_BÁN,
        NHÂN_VIÊN.NHÂN_VIÊN_BÁN,
        SUM(DỮ_LIỆU_BÁN_HÀNG.doanh_thu) AS tong_doanh_thu
    FROM
        "DỮ_LIỆU_BÁN_HÀNG" 
    JOIN
        "NHÂN_VIÊN" ON DỮ_LIỆU_BÁN_HÀNG.MÃ_NHÂN_VIÊN_BÁN = NHÂN_VIÊN.MÃ_NHÂN_VIÊN_BÁN
    GROUP BY
        TO_CHAR(DỮ_LIỆU_BÁN_HÀNG.NGÀY_HẠCH_TOÁN, 'YYYY-MM'),
        DỮ_LIỆU_BÁN_HÀNG.MÃ_NHÂN_VIÊN_BÁN,
        NHÂN_VIÊN.NHÂN_VIÊN_BÁN
    ORDER BY
        thang, NHÂN_VIÊN.NHÂN_VIÊN_BÁN
)
SELECT
    thang,
    MÃ_NHÂN_VIÊN_BÁN,
    NHÂN_VIÊN_BÁN,
    tong_doanh_thu
FROM
    doanh_thu_pe
ORDER BY
    thang, NHÂN_VIÊN_BÁN

