# Limpieza de recursos del laboratorio

Estos pasos eliminan TODOS los recursos del grupo creado para prácticas. Verifica que el grupo **no contenga recursos de otros proyectos**.

Define el nombre del grupo de recursos a eliminar:

```bash
RG=rg-ai200-cosmos-demo
```

Comprueba si el grupo existe y muestra sus datos principales:

```bash
az group list --query "[?name=='$RG'].{nombre:name,ubicacion:location}" --output table
```

Elimina el grupo de recursos y todos sus contenidos:

```bash
az group delete --name "$RG" --yes --no-wait
```

Verifica más tarde:

Confirma si el grupo todavía existe:

```bash
az group exists --name "$RG"
```

La eliminación es asíncrona. Si el deployment Foundry estaba en otro grupo y se creó exclusivamente para esta práctica, elimínalo por separado tras verificar su uso. Nunca elimines un recurso compartido sin autorización.
