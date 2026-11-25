"""Clientes compartidos: clave Cosmos únicamente para el laboratorio local; Foundry usa Entra ID."""
import os
from functools import lru_cache
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

load_dotenv()

def env(name: str, fallback: str | None = None) -> str:
    value = os.getenv(name, fallback)
    if not value or value.startswith('REEMPLAZAR') or 'REEMPLAZAR' in value:
        raise ValueError(f'Configura {name} en .env')
    return value

@lru_cache
def cosmos():
    return CosmosClient(env('COSMOS_ENDPOINT'), credential=env('COSMOS_KEY'))

def container(name: str):
    return cosmos().get_database_client(env('COSMOS_DATABASE', 'ai200docs')).get_container_client(name)

@lru_cache
def embeddings_client():
    provider = get_bearer_token_provider(DefaultAzureCredential(), 'https://ai.azure.com/.default')
    return OpenAI(base_url=env('FOUNDRY_OPENAI_ENDPOINT'), api_key=provider)

def embed(text: str) -> list[float]:
    response = embeddings_client().embeddings.create(model=env('EMBEDDING_DEPLOYMENT'), input=text)
    vector = response.data[0].embedding
    required = int(env('EMBEDDING_DIMENSIONS', '1536'))
    if len(vector) != required:
        raise ValueError(f'Dimensión incompatible: {len(vector)} frente a {required}')
    return vector

def request_charge(client):
    headers = client.client_connection.last_response_headers
    return headers.get('x-ms-request-charge', 'no disponible') if headers else 'no disponible'
