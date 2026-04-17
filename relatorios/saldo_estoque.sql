

SELECT 
    i.codpro,
    MAX(p.descr) AS descr,
    MAX(c.clas) AS clas,
    MAX(c.ncont) AS ncont,
    
    SUM(CASE 
        WHEN i.tipomov = 'E' THEN i.qtdade 
        ELSE 0 
    END) AS entradas_qtd,
    
    SUM(CASE 
        WHEN i.tipomov = 'S' THEN i.qtdade 
        ELSE 0 
    END) AS saidas_qtd,
    
    SUM(CASE 
        WHEN i.tipomov = 'E' THEN i.qtdade 
        WHEN i.tipomov = 'S' THEN -i.qtdade 
        ELSE 0 
    END) AS estoque_atual

FROM movesti i
INNER JOIN movestc c 
    ON i.codestc = c.codestc

INNER JOIN cadpro p 
    ON i.codpro = p.codpro

WHERE c.dtemis BETWEEN ? AND ?

GROUP BY 
    i.codpro

