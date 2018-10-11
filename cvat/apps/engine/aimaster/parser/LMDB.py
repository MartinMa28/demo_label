import cv2
import sys
import os
import base64
from cvat.apps.engine.aimaster.hbase.HBase import HBase

import lmdb
import caffe
from PIL import Image

class LMDB(object):
  def __init__(self, ip='10.0.5.2'):
    self.client = HBase(ip)
    
  def Upload(self, src, dest, table_name):
    tables = self.client.get_tables()
    if table_name in tables:
      print ("table name" + table_name + " already exists!")
      return
    self.client.create_table(table_name,["Data:", "Label:", "Keys:"])
        
    if not os.path.exists(dest):
      os.makedirs(dest)
      
    env_db = lmdb.Environment(src)
    txn = env_db.begin()
    datum = caffe.proto.caffe_pb2.Datum()
    
    index = 1
    for key, value in txn.cursor():
      datum.ParseFromString(value)

      size = datum.width * datum.height
      pixles1 = datum.data[0:size]
      pixles2 = datum.data[size:2*size]
      pixles3 = datum.data[2*size:3*size]

      image1 = Image.frombytes('L', (datum.width, datum.height), pixles1)
      image2 = Image.frombytes('L', (datum.width, datum.height), pixles2)
      image3 = Image.frombytes('L', (datum.width, datum.height), pixles3)

      image = Image.merge("RGB",(image3, image2, image1))
      imageName = dest + "/" + str(index) + ".jpg"
      image.save(imageName)

      file = open(imageName, 'rb')
      base64_data = base64.b64encode(file.read())
      
      self.client.put(table_name, str(index), {"Data:":base64_data, "Label:":str(datum.label), "Keys:":str(key)})
      index = index + 1
    
    env_db.close()
    
  def Download(self, table, dest):
    values = self.client.scan_value(table, "1", ["Data:","Label:"])

    image_path = dest + "/Image"
    if not os.path.exists(image_path):
      os.makedirs(image_path)
    label_file = open(dest+"/label.txt", "a+")

    for i in range(len(values[1])):
      image_data = base64.b64decode(values[0][i])
      image_name = image_path + "/" + str(i) + ".jpg"
      tmp_file = open(image_name, 'wb')
      tmp_file.write(image_data)
      tmp_file.close()

      label_file.write(image_name + "	" + values[1][i] + "\n")
    
    label_file.close()

