#!/bin/bash
# ---------------------------------------------------------------
# ETL con puras herramientas de Unix
# Fundamentos de Inteligencia Artificial
# Myranda Belen Infante Castillo - 2430384
#
# Uso:  ./script.sh
# Deja en la carpeta: merged_data.csv, X.csv y y.csv
# ---------------------------------------------------------------

set -euo pipefail

# Si no fijo esto, sort y join ordenan distinto y el join sale vacio.
# Me paso y me costo un rato encontrarlo.
export LC_ALL=C

OECD="oecd_bli_2015.csv"
GDP="gdp_per_capita.csv"

# Checo que si existan antes de empezar
for f in "$OECD" "$GDP"; do
    if [ ! -f "$f" ]; then
        echo "Falta el archivo $f" >&2
        exit 1
    fi
done


# =========================================================
# 1. Analisis exploratorio
# =========================================================
echo "=========================================="
echo " 1. ANALISIS EXPLORATORIO"
echo "=========================================="

echo ""
echo "-- Numero de lineas --"
wc -l "$OECD" "$GDP"

echo ""
echo "-- Encabezado OCDE (separado por comas) --"
head -n 1 "$OECD"

echo ""
echo "-- Encabezado FMI (separado por tabuladores) --"
# cat -A me marca los tabuladores como ^I para comprobar el delimitador
head -n 1 "$GDP" | cat -A

echo ""
echo "-- Cuantas columnas trae cada uno --"
echo "OCDE: $(head -n 1 "$OECD" | awk -F',' '{print NF}') columnas"
echo "FMI:  $(head -n 1 "$GDP" | awk -F'\t' '{print NF}') columnas"

echo ""
echo "-- Primeras filas del OCDE --"
head -n 3 "$OECD"

echo ""
echo "-- Primeras filas del FMI --"
head -n 3 "$GDP"


# =========================================================
# 2. Filtrado de satisfaccion de vida (OCDE)
# =========================================================
echo ""
echo "=========================================="
echo " 2. FILTRADO OCDE"
echo "=========================================="

# El archivo trae muchos indicadores mezclados. Solo quiero:
#   columna 3  = INDICATOR   -> SW_LIFS (Life satisfaction)
#   columna 7  = INEQUALITY  -> TOT (Total, o sea sin separar por sexo o ingreso)
# y me quedo con columna 2 (Country) y columna 15 (Value)
awk -F',' '$3=="SW_LIFS" && $7=="TOT" {print $2 "," $15}' "$OECD" > tmp_oecd.csv

echo "Filas de satisfaccion extraidas: $(wc -l < tmp_oecd.csv)"
head -n 5 tmp_oecd.csv


# =========================================================
# 3. Normalizacion del PIB (FMI)
# =========================================================
echo ""
echo "=========================================="
echo " 3. NORMALIZACION FMI"
echo "=========================================="

# Aqui hay tres cosas que limpiar:
#   - el delimitador es tabulador, no coma
#   - los millares vienen con coma: 50,961.865 -> 50961.865
#   - las ultimas dos lineas son basura (una vacia y la nota de la fuente)
# NR>1 salta el encabezado, gsub quita las comas y el if descarta lo vacio
awk -F'\t' 'NR>1 { gsub(/,/, "", $6); if ($1 != "" && $6 != "") print $1 "," $6 }' "$GDP" > tmp_gdp.csv

echo "Filas de PIB extraidas: $(wc -l < tmp_gdp.csv)"
head -n 5 tmp_gdp.csv


# =========================================================
# 4. Fusion de los dos datasets
# =========================================================
echo ""
echo "=========================================="
echo " 4. JOIN"
echo "=========================================="

# join necesita que los dos archivos esten ordenados por la llave,
# si no, se salta filas sin avisar
sort -t',' -k1,1 tmp_oecd.csv > tmp_oecd_sorted.csv
sort -t',' -k1,1 tmp_gdp.csv  > tmp_gdp_sorted.csv

# Inner join por el nombre del pais (campo 1 de los dos archivos).
# Solo quedan los paises que aparecen en ambos.
echo "Pais,Satisfaccion_Vida,PIB_Capita" > merged_data.csv
join -t',' -1 1 -2 1 tmp_oecd_sorted.csv tmp_gdp_sorted.csv >> merged_data.csv

echo "Paises en el dataset final: $(( $(wc -l < merged_data.csv) - 1 ))"
head -n 6 merged_data.csv


# =========================================================
# 5. Preparacion para el modelo
# =========================================================
echo ""
echo "=========================================="
echo " 5. X e y"
echo "=========================================="

# X = la variable independiente (PIB), y = la que quiero predecir (satisfaccion).
# tail -n +2 quita el encabezado porque scikit-learn no lo necesita.
cut -d',' -f3 merged_data.csv | tail -n +2 > X.csv
cut -d',' -f2 merged_data.csv | tail -n +2 > y.csv

echo "X.csv -> $(wc -l < X.csv) valores"
echo "y.csv -> $(wc -l < y.csv) valores"

# Si no coinciden algo salio mal, mejor que truene aqui
if [ "$(wc -l < X.csv)" -ne "$(wc -l < y.csv)" ]; then
    echo "X e y no tienen el mismo numero de filas" >&2
    exit 1
fi


# =========================================================
# 6. Limpieza
# =========================================================
rm -f tmp_oecd.csv tmp_gdp.csv tmp_oecd_sorted.csv tmp_gdp_sorted.csv

echo ""
echo "Listo. Se generaron merged_data.csv, X.csv y y.csv"
