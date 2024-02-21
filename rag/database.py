# import sys
# sys.path.append('../')
import os
os.chdir("..")
import json
from src.book_preprocess import get_book_data
from llama_index.core import Document
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from IPython.display import Markdown, display
import chromadb
from rag.config import *

def get_book_transcripts_data():
    book_doc_data = get_book_data(100)
    with open('artifacts\YouTube_API_Transcripts\chunked_transcripts_mba.json', 'r') as file:
        mba_data = json.load(file)

    with open('artifacts\YouTube_API_Transcripts\chunked_transcripts_undergrad.json', 'r') as file:
        undergrad_data = json.load(file)

    with open('artifacts\YouTube_API_Transcripts\chunked_misc_transcripts.json', 'r') as file:
        misc_data = json.load(file)
    
    all_data_list = []
    for book_doc in book_doc_data:
        # try:
        if book_doc=={}: continue
        # book = book_doc['book_source']
        # if book!= curr_book:
            # print(book_doc)

            # curr_book = book
        all_data_list.append(
            Document(
                text=book_doc['text'],
                metadata={
                    'page_num_coordinates':str(book_doc['page_num_coordinates']),
                    'book_source':book_doc['book_source'],
                },
                excluded_embed_metadata_keys=['page_num_coordinates','book_source'],
                excluded_llm_metadata_keys=['page_num_coordinates','book_source'],
            )
        )

    for json_data in [undergrad_data,mba_data,misc_data]:
        for youtube_id, text_list in json_data.items():
            all_data_list.append(
                Document(
                    text=text_list[0]['text'],
                    metadata={
                        "youtube_id":youtube_id,
                        "start_timestamp":text_list[0]['start_time'],
                    },
                    excluded_embed_metadata_keys=['youtube_id','start_timestamp'],
                    excluded_llm_metadata_keys=['youtube_id','start_timestamp'],
                )
            )
            # break
    return all_data_list

def create_database():
    all_data_list = get_book_transcripts_data()
    ad_project_db = chromadb.PersistentClient(path="ad_project_db")
    ad_project_chroma_collection = ad_project_db.get_or_create_collection(COLLECTION_NAME)
    embed_model = OpenAIEmbedding(model=EMBEDDING_MODEL)
    vector_store = ChromaVectorStore(chroma_collection=ad_project_chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        all_data_list, storage_context=storage_context, embed_model=embed_model
    )

    return index

def load_database(path:str):
    db2 = chromadb.PersistentClient(path=path)
    embed_model = OpenAIEmbedding(model=EMBEDDING_MODEL)
    chroma_collection = db2.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index_ = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )
    return index_

def query_database(query_text,index):
    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(query_text)

    return nodes

