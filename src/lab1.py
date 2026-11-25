"""Laboratorio 1: CRUD y consultas parametrizadas."""
import argparse, json
from pathlib import Path
from azure.cosmos import exceptions
from src.common import container, env, request_charge

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['seed','get','query','update','delete'])
    parser.add_argument('--id',default='doc-01')
    parser.add_argument('--category',default='rag')
    args=parser.parse_args()
    
    col=container(env('COSMOS_SOURCE_CONTAINER','documents'))

    if args.action=='seed':
        items=json.loads(Path('data/documents.json').read_text(encoding='utf-8'))
        for item in items: col.upsert_item(item)
        print(f'{len(items)} documentos insertados/actualizados; última operación RU={request_charge(col)}')

    elif args.action=='get':
        item=col.read_item(item=args.id,partition_key='training')
        print(json.dumps(item,ensure_ascii=False,indent=2));print('RU:',request_charge(col))

    elif args.action=='query':
        statement='SELECT c.id, c.title, c.category FROM c WHERE c.tenant = @tenant AND c.category = @category'
        rows=list(col.query_items(statement,parameters=[{'name':'@tenant','value':'training'},{'name':'@category','value':args.category}],partition_key='training'))
        print(json.dumps(rows,ensure_ascii=False,indent=2));print('RU último segmento:',request_charge(col))

    elif args.action=='update':
        item=col.read_item(args.id,partition_key='training')
        item['content'] += ' Actualización detectada por el laboratorio 4.'
        col.replace_item(item['id'],item)
        print('Actualizado:',args.id,'RU:',request_charge(col))
    
    elif args.action=='delete':
        col.delete_item(args.id,partition_key='training')
        print('Eliminado:',args.id)

if __name__=='__main__':
    main()
