# Laboratorio 1 - Cosmos DB para NoSQL: SDK, CRUD y consultas

**Objetivo:** provisionar la base de datos con `az`, poblarla y consultarla con SDK Python. 

Se espera entender la diferencia entre `read_item` (lectura puntual) y SQL parametrizado.

### 1. Autenticar Azure CLI y seleccionar la suscripción

Ejecuta **uno por uno** los siguientes comandos en terminal Bash (Cloud Shell también sirve para `az`, pero los ejemplos Python se ejecutan desde tu máquina):

Inicia sesión en Azure:

```bash
az login
```

Muestra la suscripción activa:

```bash
az account show --output table
```

Selecciona una suscripción si tienes varias:

```bash
az account set --subscription "ID_O_NOMBRE_DE_TU_SUSCRIPCION"
```

### 2. Definir nombres y crear recursos

Los nombres son ejemplos: la variable `ACCOUNT` se genera con un sufijo aleatorio para usar un nombre globalmente único y en minúsculas (de 3 a 44 caracteres). En Bash las variables permanecen en tu sesión:

Define el nombre del grupo de recursos:

```bash
RG=rg-ai200-cosmos-demo
```

Define la región donde se crearán los recursos:

```bash
LOCATION=francecentral
```

Genera un sufijo aleatorio y define el nombre de la cuenta Cosmos DB:

```bash
SUFFIX="$(date +%s)$RANDOM"
ACCOUNT="ai200demo${SUFFIX}"
```

Define el nombre de la base de datos:

```bash
DB=ai200docs
```

Crea el grupo de recursos:

```bash
az group create --name "$RG" --location "$LOCATION"
```

Crea la cuenta Cosmos DB:

```bash
az cosmosdb create --resource-group "$RG" --name "$ACCOUNT" --locations regionName="$LOCATION" failoverPriority=0 --default-consistency-level Session
```

> La cuenta usa aprovisionamiento estándar basado en RU. Comprueba disponibilidad y costos de la región elegida. 

Crea la base de datos con throughput compartido:

```bash
az cosmosdb sql database create --resource-group "$RG" --account-name "$ACCOUNT" --name "$DB" --throughput 1000
```

Crea el contenedor de origen con clave de partición `/tenant` y throughput compartido de la base de datos:

Crea el contenedor de documentos:

```bash
az cosmosdb sql container create --resource-group "$RG" --account-name "$ACCOUNT" --database-name "$DB" --name documents --partition-key-path /tenant --idx @config/default-index.json
```

### 3. Preparar variables locales

Consulta el endpoint:

Obtén el endpoint del account Cosmos DB:

```bash
az cosmosdb show --resource-group "$RG" --name "$ACCOUNT" --query documentEndpoint --output tsv
```

Para el laboratorio local únicamente, consulta la clave de la cuenta; **no la compartas ni la subas a GitHub**:

Obtén la clave primaria de acceso:

```bash
az cosmosdb keys list --resource-group "$RG" --name "$ACCOUNT" --type keys --query primaryMasterKey --output tsv
```

Crea un archivo `.env` a partir de `.env.example`

```bash
cp .env.example .env
```

Abre `.env` y reemplaza `COSMOS_ENDPOINT` y `COSMOS_KEY`. Los demás nombres tienen valores predeterminados. Revisa que `.env` quede fuera de Git.

Crea un entorno virtual e instala las dependencias:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

Carga los documentos de ejemplo en la base de datos:

```bash
python -m src.lab1 seed
```

Consulta un documento por su identificador:

```bash
python -m src.lab1 get --id doc-01
```

Consulta documentos por categoría:

```bash
python -m src.lab1 query --category performance
```

Prueba modificar el contenido de `doc-01` (lo volveremos a modificar en laboratorio 4):

Actualiza el documento `doc-01`:

```bash
python -m src.lab1 update --id doc-01
```

**No cierres la terminal. La usaremos en los demas demos.**

### 5. Explicaciones adicionales

- El JSON contiene `id`, `tenant`, `category`, `title`, `content` y `published`.
- La clave de partición `/tenant` debe incluirse en todas las escrituras y lecturas puntuales.
- `read_item(id, partition_key)` es distinto a una consulta SQL que filtra un conjunto.
- Las consultas parametrizadas pasan valores en una colección separada del SQL.
- La respuesta del SDK expone `x-ms-request-charge` en las cabeceras. En muestras pequeñas el ejemplo enseña el cargo del último segmento.

### 6. Verificación opcional en Azure Portal

**Azure Portal → cuenta Cosmos DB → Data Explorer → ai200docs → documents → Items.** Comprueba que existen al menos 12 documentos y abre `doc-01`. No modifiques recursos mediante Portal.