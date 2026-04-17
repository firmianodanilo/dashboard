SELECT 
    EXTRACT(MONTH FROM dtban) AS mes,
    SUM(CASE WHEN tipomov = 'E' THEN valor ELSE 0 END) AS entrada,
    SUM(CASE WHEN tipomov = 'S' THEN valor ELSE 0 END) AS saida
FROM movban
WHERE dtban IS NOT NULL
GROUP BY mes
ORDER BY mes

WHERE dtvenc BETWEEN ? AND ?
{{filtro_empresa}}