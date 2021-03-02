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

    start_time = time.time()
    handler.handle(client, db, request.get_data())
    elapsed_time = (time.time() - start_time) * 1000
    print("req processed in {}ms".format(elapsed_time))
    return ('', 200)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8009)
