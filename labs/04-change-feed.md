# Laboratorio 4 - Procesador del Change Feed (SDK .NET)

**Objetivo:** utilizar el Change Feed Processor REAL con su contenedor de leases para detectar inserciones y actualizaciones y recalcular embeddings mediante Microsoft Foundry.

¿Por qué .NET? El procesador automático con leases/checkpoints se ofrece en SDK .NET; para Python se ofrece el modelo de consumo pull con tokens administrados por el desarrollador. Este repositorio no confunde ambos.

## 1. Crear el contenedor de leases (Azure CLI)

Este contenedor necesita clave de partición `/id` y no debe tener TTL.

Crea el contenedor que almacenará leases y checkpoints:

```bash
az cosmosdb sql container create --resource-group "$RG" --account-name "$ACCOUNT" --database-name "$DB" --name leases --partition-key-path /id
```

Usamos el mismo throughput compartido que en las prácticas 1 y 2.

## 2. Ejecutar el worker .NET desde la raíz

Necesitas .NET SDK 10 y `.env` ya configurado. **El archivo `.env` es cargado por Python, no por .NET directamente**. Puedes exportar las variables a la sesión o pegarlas en terminal (sin subir credenciales al repositorio). Ejemplo en Bash:

Configura el endpoint de Cosmos DB:

```bash
export COSMOS_ENDPOINT="https://TU_CUENTA.documents.azure.com:443/"
```

Configura la clave de acceso de Cosmos DB:

```bash
export COSMOS_KEY="CLAVE_SOLO_DE_LABORATORIO"
```

Configura el nombre de la base de datos:

```bash
export COSMOS_DATABASE=ai200docs
```

Configura el contenedor de origen:

```bash
export COSMOS_SOURCE_CONTAINER=documents
```

Configura el contenedor de destino vectorial:

```bash
export COSMOS_VECTOR_CONTAINER=documents_vectors
```

Configura el contenedor de leases:

```bash
export COSMOS_LEASE_CONTAINER=leases
```

Configura el endpoint de inferencia Foundry:

```bash
export FOUNDRY_OPENAI_ENDPOINT="https://TU_RECURSO.openai.azure.com/openai/v1/"
```

Configura el deployment de embeddings:

```bash
export EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

Configura la dimensión de los embeddings:

```bash
export EMBEDDING_DIMENSIONS=1536
```

Ahora inicia el procesador:

Inicia el procesador del Change Feed:

```bash
dotnet run --project src/change-feed-worker
```

Este es un proceso **continuo**: observa nuevos cambios, toma checkpoints en `leases` y actualiza `documents_vectors`. Déjalo corriendo para la siguiente etapa.

## 3. Producir un cambio en otra terminal

Abre otra terminal. Con tu entorno Python activo y `.env` configurado:

Actualiza un documento para generar un cambio:

```bash
python -m src.lab1 update --id doc-03
```

En la terminal del worker observarás un mensaje similar a `indexado: doc-03`. A continuación consulta los resultados con:

Ejecuta una búsqueda semántica para comprobar el documento actualizado:

```bash
python -m src.lab3 search --question "¿Cómo medimos el costo de una consulta en RU?"
```

## 4. Comprobar en Azure Portal

- **Data Explorer → leases → Items:** confirma la existencia de documentos de checkpoints/leases.
- **Data Explorer → documents_vectors → Items → doc-03:** abre el registro y confirma que el texto actualizado y su embedding están presentes.
- Observa el worker: si reinicias el proceso, los checkpoints ayudan a retomar el seguimiento sin empezar siempre desde cero.

## 5. Discusión técnica

- La implementación es **at-least-once**: el mismo cambio puede reprocesarse si existe un fallo antes de confirmar el checkpoint. `upsert` por ID hace este flujo idempotente respecto al documento de destino (aunque podría gastar tokens de nuevo).
- La lectura por defecto es **latest version**: inserciones y actualizaciones, sin eliminación. Para detectar borrados se necesita otra estrategia o un modo específico con sus requisitos.
- En producción incorpora reintentos selectivos, observabilidad, secretos seguros, límites de tasa y costes de embeddings.
- Si fallan las llamadas de Foundry, el procesador puede reintentar lotes; no confundas este comportamiento con un resultado garantizado sin configuración.

**Resultado esperado:** actualización real del documento indexado, sin consultas manuales repetidas desde la aplicación.
