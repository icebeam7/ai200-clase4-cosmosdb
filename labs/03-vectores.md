# Laboratorio 3 - Embeddings reales y búsqueda semántica

**Objetivo:** generar embeddings con el deployment real `text-embedding-3-small` en Microsoft Foundry, almacenarlos en Cosmos DB y usar `VectorDistance`.

## 1. Crear/seleccionar el modelo

Necesitas un recurso Microsoft Foundry / Azure OpenAI con deployment de **embeddings** existente y un endpoint compatible con `/openai/v1/`. 

A continuación, ejecuta los siguientes comandos, que sirven para crear: 

- El recurso de Microsoft Foundry
- Un proyecto en dicho recurso
- Un modelo de embeddings en dicho proyecto

Primero se establecen las variables y luego se crean los recursos:

```bash
FOUNDRY_ACCOUNT="ai200-foundry-${SUFFIX}"
FOUNDRY_PROJECT="ai200-project-${SUFFIX}"

FOUNDRY_MODEL="text-embedding-3-small"
FOUNDRY_MODEL_VERSION="1"

az cognitiveservices account create \
  --name "$FOUNDRY_ACCOUNT" \
  --resource-group "$RG" \
  --location "$LOCATION" \
  --kind "AIServices" \
  --sku "S0" \
  --custom-domain "$FOUNDRY_ACCOUNT" \
  --assign-identity

az cognitiveservices account project create \
  --name "$FOUNDRY_ACCOUNT" \
  --resource-group "$RG" \
  --project-name "$FOUNDRY_PROJECT" \
  --location "$LOCATION"

az cognitiveservices account deployment create \
  --name "$FOUNDRY_ACCOUNT" \
  --resource-group "$RG" \
  --deployment-name "$FOUNDRY_MODEL" \
  --model-name "$FOUNDRY_MODEL" \
  --model-version "$FOUNDRY_MODEL_VERSION" \
  --model-format OpenAI \
  --sku-capacity 50 \
  --sku-name GlobalStandard
```

Para asignar acceso al usuario actual, obtén los datos siguientes:

Consulta el identificador de la suscripción activa:

```bash
az account show --query id -o tsv
```

Consulta el identificador del usuario que inició sesión:

```bash
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv)
```

Consulta el identificador ARM del recurso Foundry:

```bash
ARM_ID=$(az cognitiveservices account show --resource-group $RG --name $FOUNDRY_ACCOUNT --query id --output tsv)
```

Asignación de rol **por el propietario del recurso**, reemplazando valores:

Asigna al usuario el rol de acceso a inferencia de OpenAI:

```bash
az role assignment create --assignee-object-id "$USER_OBJECT_ID" --assignee-principal-type User --role "Cognitive Services OpenAI User" --scope "$ARM_ID"
```

Configura en `.env`:

Define las variables de configuración del endpoint (la variable `FOUNDRY_ACCOUNT` creada anteriormente) y el modelo:

```ini
FOUNDRY_OPENAI_ENDPOINT=https://TU-RECURSO.openai.azure.com/openai/v1/
EMBEDDING_DEPLOYMENT=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

## 2. Crear contenedor vectorial usando Azure CLI

**Importante:** vector embedding policy + vector index se establecen en la creación de un contenedor NUEVO. Para una dimensión diferente, edita `config/vector-embedding.json` antes de crear el contenedor.

Habilita Vector Search en tu cuenta de CosmosDB

```bash
az cosmosdb update \
  --name "$ACCOUNT" \
  --resource-group "$RG" \
  --capabilities EnableNoSQLVectorSearch
```

Crea el contenedor y configura sus políticas vectoriales (se requiere throughput dedicado):

```bash
az cosmosdb sql container create --resource-group "$RG" --account-name "$ACCOUNT" --database-name "$DB" --name documents_vectors --partition-key-path /tenant --idx @config/vector-index.json --vector-embeddings @config/vector-embedding.json --throughput 400
```

Comprueba la política de embeddings y el índice:

Muestra las políticas vectorial e de indexación del contenedor:

```bash
az cosmosdb sql container show --resource-group "$RG" --account-name "$ACCOUNT" --database-name "$DB" --name documents_vectors --query 'resource.{vectorEmbeddingPolicy:vectorEmbeddingPolicy,indexingPolicy:indexingPolicy}' --output json 
```

## 3. Generación de embeddings

Genera y almacena los embeddings de los documentos:

```bash
python -m src.lab3 index
```

Obtendrás 12 embeddings de 1536 dimensiones del deployment Foundry y se guardarán junto con cada documento en la colección vectorial.

## 4. Búsqueda semántica

Busca documentos similares a una pregunta sobre optimización de costos:

```bash
python -m src.lab3 search --question "¿Cómo disminuir el costo de consultas de una base de datos?"
```

Busca documentos similares filtrados por la categoría `rag`:

```bash
python -m src.lab3 search --question "¿Qué es recuperación aumentada por generación?" --category rag
```

Los resultados aparecen ordenados por `VectorDistance` con métrica coseno (distancia menor = más parecido). El corpus es mínimo: la finalidad es observar el comportamiento, no evaluar precisión de recuperación estadísticamente.

## 5. Revisar en Azure Portal

**Data Explorer → documents_vectors → Items:** abre un documento y comprueba que existe el campo numérico `embedding` (1536 valores). También puedes ejecutar consultas NoSQL desde Data Explorer para mostrar resultados, pero la actividad guiada se realiza en CLI.

**Resultado esperado:** embeddings generados realmente en Foundry y búsqueda vectorial funcional en Cosmos DB.
