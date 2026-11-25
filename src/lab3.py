"""Laboratorio 3: embeddings reales Foundry y búsqueda por similitud vectorial."""
import argparse, json
from src.common import container,env,embed,request_charge

def index():
    source=container(env('COSMOS_SOURCE_CONTAINER','documents'))
    destination=container(env('COSMOS_VECTOR_CONTAINER','documents_vectors'))
    docs=list(source.query_items('SELECT * FROM c WHERE c.tenant=@t',parameters=[{'name':'@t','value':'training'}],partition_key='training'))
    for doc in docs:
        doc.pop('_rid',None);doc.pop('_self',None);doc.pop('_etag',None);doc.pop('_attachments',None);doc.pop('_ts',None)
        doc['embedding']=embed(doc['title']+'\n'+doc['content'])
        destination.upsert_item(doc)
        print('Vector guardado:',doc['id'],'dimensiones:',len(doc['embedding']))

def search(question,category=None):
    col=container(env('COSMOS_VECTOR_CONTAINER','documents_vectors'))
    vector=embed(question)
    
    sql='SELECT TOP 5 c.id,c.title,c.category,VectorDistance(c.embedding,@vector) AS distance FROM c WHERE c.tenant=@tenant'
    params=[{'name':'@vector','value':vector},{'name':'@tenant','value':'training'}]
    
    if category:
        sql+=' AND c.category=@category';params.append({'name':'@category','value':category})
    
    sql+=' ORDER BY VectorDistance(c.embedding,@vector)'
    
    results=list(col.query_items(query=sql,parameters=params,partition_key='training'))
    
    print(json.dumps(results,indent=2,ensure_ascii=False));print('RU última página:',request_charge(col))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['index','search'])
    parser.add_argument('--question',default='¿Cómo mejorar el rendimiento y las RU de una consulta?')
    parser.add_argument('--category',default=None)
    args=parser.parse_args()
    
    if args.action=='index':
        index()
    else:
        search(args.question,args.category)

if __name__=='__main__':
    main()
