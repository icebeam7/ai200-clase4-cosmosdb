# Laboratorio 2 - Optimización de consultas, RU e índices

**Objetivo:** contrastar dos políticas de indexación. Las variaciones no garantizan una mejora uniforme: observa qué consultas se benefician y cuáles pueden empeorar.

## 1. Pre-requisitos

Continúa trabajando en la terminal del Laboratorio 1.

Si abriste otra terminal, vuelve a definir `RG`, `ACCOUNT` y `DB` tal como en el laboratorio 1.

## 2. Crear contenedor optimizado

Usamos un **contenedor separado** para no cambiar la indexación de datos originales; la configuración incluye rutas de rango y un índice compuesto para `category + published`.

Crea el contenedor con la política de indexación optimizada:

```bash
az cosmosdb sql container create --resource-group "$RG" --account-name "$ACCOUNT" --database-name "$DB" --name documents_optimized --partition-key-path /tenant --idx @config/optimized-index.json
```

Inspecciona la política de indexación usando CLI:
(Política con exclusión de rutas no necesarias y un índice compuesto.)

```bash
az cosmosdb sql container show --resource-group "$RG" --account-name "$ACCOUNT" --database-name "$DB" --name documents_optimized --query 'resource.indexingPolicy' --output json
```


## 3. Medir consumo de RU

Ejecuta las mediciones de RU y resultados:

```bash
python -m src.lab2
```

El ejemplo inserta 12 documentos en el contenedor optimizado, realiza dos consultas en ambos contenedores y muestra cantidad de resultados y RU de la última página de cada consulta.

**Advertencia:** con un corpus tan pequeño, diferencias de 1 RU pueden ser ruido. No consideres esto un benchmark de producción; varía el tamaño de datos y repite las ejecuciones.

## 4. Discutir coherencia

Consulta el nivel de consistencia configurado en la cuenta:

```bash
az cosmosdb show --name "$ACCOUNT" --resource-group "$RG" --query 'consistencyPolicy' --output json
```

**Session** es un equilibrio típico para aplicaciones interactivas. Compara conceptualmente con Strong, Bounded Staleness, Consistent Prefix y Eventual.

## 5. Verificación en Portal

**Cosmos DB → Data Explorer → documents_optimized** para comprobar 12 documentos; **Metrics → Total Request Units** para observar consumo agregado (tiene retraso y está sujeto a otras operaciones). El número de RU mostrado por Python corresponde a la solicitud, no al total de la cuenta.

