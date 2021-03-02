#!/usr/bin/env python
from flask import Flask, request 
from waitress import serve
from minio import Minio
import pydgraph
import time
import os

from function import handler

# get params 
MINIO_URL = os.getenv('MINIO_URL')
MINIO_ACCESS = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET = os.getenv('MINIO_SECRET_KEY')
DB_URL= os.getenv('DB_URL')

app = Flask(__name__)

# create minio client
client = Minio(MINIO_URL, access_key=MINIO_ACCESS, secret_key=MINIO_SECRET, secure=False)

# db client 
db_stub = pydgraph.DgraphClientStub(DB_URL)
db = pydgraph.DgraphClient(db_stub)
        
@app.route('/', methods=['POST', 'HEAD'])
def call_handler():
    if request.method == 'HEAD':
        return ('', 200)

    try:
        handler.handle(client, db, request.get_data())
        return ('', 200)
    except Exception:
        return ('', 500)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8009)
