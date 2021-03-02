import random
import json
import os
import io
import tempfile
import uuid
import string
import base64
import numpy as np

from PIL import Image, ImageFile

# fix truncate ??
ImageFile.LOAD_TRUNCATED_IMAGES = True

# thumbnail size
t_size = (320, 320)
m_size = (40, 40)

def getObjName(prefix, size=11):
    chars = string.ascii_letters + string.digits
    return prefix + '/' + ''.join(random.choice(chars) for x in range(size)) + '.webp'

def dhash(image):
    arr = np.array(image.resize((9, 8), Image.ANTIALIAS).convert('L')).astype('uint8')
    hash_mat = arr[:, 1:] > arr[:, :-1]
    return ''.join('%0.2x' % x for x in np.packbits(hash_mat))

def update(db, uImage):
    tx = db.txn()
    try:
        tx.mutate(set_obj=uImage)
        tx.commit()
    finally:
        tx.discard()

 
"""
input: 
{ "bucket": "test", "object": "RN9BSDpxhM.jpg", "imageUid":"0x56712571", "imageSizeUid":"0x2312312" }
"""
def handle(client, db, body):
    # load req
    json_in = json.loads(body)
    bucket = json_in['bucket']
    objectName = json_in['object']
    prefix = objectName.split("/")[0] # get prefix from objectName
    imageUID = json_in['imageUid']
    sizeUID = json_in['imageSizeUid']
    
    # create temp files
    tmpname = str(uuid.uuid1())
    file_input = tempfile.gettempdir() + '/' + tmpname
    file_output = tempfile.gettempdir() + '/out.' + tmpname
    file_thumbnail = tempfile.gettempdir() + '/t.' + tmpname

    # get object to file
    client.fget_object(bucket, objectName, file_input)

    # process image
    with Image.open(file_input) as im:
        
        # calc image size
        (im_width, im_height) = im.size

        # gen dhash key
        hashkey = dhash(im)

        # convert to webp
        im.save(file_output, "WEBP")
        
        # mk small (+ add Image.ANTIALIAS)
        im.thumbnail(t_size, Image.ANTIALIAS)
        (sm_width, sm_height) = im.size
        im.save(file_thumbnail, "WEBP")
        
        # create mini thumbnail
        im.thumbnail(m_size)
        buf = io.BytesIO()
        im.convert('RGB').save(buf,format='PNG',optimize=True)
        data = "data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()

    # store webp
    wb = client.fput_object(bucket, getObjName(prefix), file_output, content_type='image/webp')

    # store small
    sm = client.fput_object(bucket, getObjName(prefix), file_thumbnail, content_type='image/webp')

    # update db 
    update(db,uImage={
        'uid': imageUID, 
        'Image.hash': hashkey, 
        'Image.thumbnail': data, 
        'Image.sizes': [
            {
               'uid': sizeUID,
               'ImageSize.width': im_width,
               'ImageSize.height': im_height,
            },
            {
                'uid': '_:wb',
                'dgraph.type': 'ImageSize',
                'ImageSize.width': im_width,
                'ImageSize.height': im_height,
                'ImageSize.type': 'wb',
                'ImageSize.path': bucket + '/' + wb.object_name,
            },
            {
                'uid': '_:sm', 
                'dgraph.type': 'ImageSize', 
                'ImageSize.width': sm_width, 
                'ImageSize.height': sm_height, 
                'ImageSize.type': 'sm', 
                'ImageSize.path': bucket + '/' + sm.object_name,
            },
        ]
    })

    # cleanup
    os.remove(file_input)
    os.remove(file_output)
    os.remove(file_thumbnail)
