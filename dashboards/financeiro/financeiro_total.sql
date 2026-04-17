SELECT
    SUM(CASE WHEN tipomov = 'E' THEN valor ELSE 0 END) -
    SUM(CASE WHEN tipomov = 'S' THEN valor ELSE 0 END) AS total
FROM movban

WHERE dtvenc BETWEEN ? AND ?
{{filtro_empresa}}

