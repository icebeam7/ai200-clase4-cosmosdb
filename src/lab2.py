"""Laboratorio 2: medir RU para consultas; comparaciones orientativas, no benchmark."""
import json
from pathlib import Path
from src.common import container, env, request_charge

def run(c,sql,params):
    rows=list(c.query_items(query=sql,parameters=params,partition_key='training'))
    
    # Header expuesto por el SDK refleja la última página; con pocos items suele ser una sola.
    return len(rows),request_charge(c)

def main():
    source=container(env('COSMOS_SOURCE_CONTAINER','documents'))
    optimized=container(env('COSMOS_COMPARE_CONTAINER','documents_optimized'))
    
    for doc in json.loads(Path('data/documents.json').read_text(encoding='utf-8')):
        optimized.upsert_item(doc)
    
    queries=[
        ('Filtro por categoría','SELECT * FROM c WHERE c.tenant=@t AND c.category=@c',[{'name':'@t','value':'training'},{'name':'@c','value':'performance'}]),
        ('Ordenado por fecha','SELECT c.id,c.title FROM c WHERE c.category=@c ORDER BY c.published DESC',[{'name':'@c','value':'performance'}]),
    ]
    
    for name,sql,params in queries:
        print('\n'+name)
        for label,client in [('predeterminado',source),('optimizado',optimized)]:
            try:
                count,ru=run(client,sql,params)
                print(f'{label}: {count} elementos, RU última página={ru}')
            except Exception as e:
                print(f'{label}: error {type(e).__name__}: {e}')
    
    print('Nota: corpus pequeño; comparar varias ejecuciones y el impacto en escrituras.')

if __name__=='__main__': 
    main()
