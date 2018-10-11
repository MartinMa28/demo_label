import os
import sys
# import cv2
import random
import base64
from cvat.apps.engine.aimaster.script import DBParser
# from aimaster.script.kfbReader import reader
from cvat.apps.engine.aimaster.hbase.HBase import HBase

class KFB(object):
    def __init__(self, ip='10.0.5.2'):
        self.client = HBase(ip)
        self.mapper = {'Streptococcus': 0, 'AC': 8, 'Actinomyces': 14, 'AGC': 6, 'LSIL': 3, 'Trichomonad': 12, 'ASC-US': 2, 'Germ': 10, 'HSIL': 4, 'ASC-H': 1, 'Unidentified': 0, 'AIS': 7, 'Background': 0, 'Candida': 11, 'AGC-NOS': 5, 'Herpes': 13, 'SCC': 9}

    def __is_rect_intersect(self, roi, x, y):
        for i in range(len(roi)):
            lx = abs((x+75) - (roi[i][0]+roi[i][2]/2))
            ly = abs((y+75) - (roi[i][1]+roi[i][3]/2))
            if lx < ((150+roi[i][2])/2) and ly < ((150+roi[i][3])/2):
                return True
        return False

    def Get_Roi_Info(self, path, scale=20):
        roi_info = []
        db_path = path.replace('.kfb', '.db')
        if os.path.exists(db_path):
            db = DBParser.ReadDB(db_path, 2)
            for d in db:
                #print d
                if self.mapper.get(d['label']) is None:
                    print('wrong type detect. ', d['label'], db_path)
                    continue
                if self.mapper.get(d['label']) == 0 or self.mapper.get(d['label']) > 4:
                    continue

                x = min(d['xmax'], d['xmin']) * scale
                y = min(d['ymax'], d['ymin']) * scale
                h = abs(d['ymax'] - d['ymin']) * scale
                w = abs(d['xmax'] - d['xmin']) * scale

                if w <= 20 or h <= 20:
                    print('wrong db record:', d)
                    continue

                roi_info.append([x, y, w, h])
                
        else:
            assert ('neg' in path), 'the kfb is NOT negative slice but db file doesn\'t exist! do you forget to copy it\?'
        return roi_info

    def Generate_Pos_Samples(self, src, dest, scale=20):
        r = reader()
        r.ReadInfo(src)
        w = r.getWidth()
        h = r.getHeight()

        dest_dir = os.path.abspath(dest + "/" + src.split("/")[-1].split(".")[0] + "/pos")
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        roi_info = self.Get_Roi_Info(src)

        for d in roi_info:
            fname = "{}/{}_{}.jpg".format(dest_dir, d[1]+d[3]/2-75, d[0]+d[2]/2-75)
            img = r.ReadRoi(d[0]+d[2]/2-75, d[1]+d[3]/2-75, 150, 150, scale)
            cv2.imwrite(fname, img)

    def Generate_Neg_Samples(self, src, dest, num, scale=20):
        r = reader()
        r.ReadInfo(src)
        w = r.getWidth()
        h = r.getHeight()

        dest_dir = os.path.abspath(dest + "/" + src.split("/")[-1].split(".")[0] + "/neg")
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        roi_info = self.Get_Roi_Info(src)

        while(num > 0):
            x = random.uniform(0, w-150)
            y = random.uniform(0, h-150)
            if not self.__is_rect_intersect(roi_info, x, y):
                fname = "{}/{}_{}.jpg".format(dest_dir, y, x)
                img = r.ReadRoi(x, y, 150, 150, scale)
                cv2.imwrite(fname, img)
            num -= 1

    def Generate(self, src, dest, num=20, scale=20):
        for root, _, files in os.walk(src):
            for file in files:
                if file.endswith(".kfb"):
                    src = os.path.abspath(os.path.join(root, file))
                    dest = os.path.abspath(dest)
                    self.Generate_Neg_Samples(src, dest, num)
                    self.Generate_Pos_Samples(src, dest)

    def Upload(self, src, table_name, scale=20):
        tables = self.client.get_tables()
        if table_name in tables:
            print("table name" + table_name + " already exists!")
            return
        self.client.create_table(table_name,["pos", "neg"])
        
        _src = os.path.abspath(src)
        dirs = os.listdir(_src)
        for dir in dirs:
            path = _src + "/" + dir
            for root, _, files in os.walk(path + "/neg"):
                tmp_column = "neg:" + dir + "_s" + str(scale)
                index = 1
                for file in files:
                    if file.endswith(".jpg"):
                        image_src = os.path.abspath(os.path.join(root, file))
                        image_file = open(image_src, 'rb')
                        base64_data = base64.b64encode(image_file.read())
                        self.client.put(table_name, str(index), {tmp_column:base64_data})
                        index = index + 1

            for root, _, files in os.walk(path + "/pos"):
                tmp_column = "pos:" + dir + "_s" + str(scale)
                index = 1
                for file in files:
                    if file.endswith(".jpg"):
                        image_src = os.path.abspath(os.path.join(root, file))
                        image_file = open(image_src, 'rb')
                        base64_data = base64.b64encode(image_file.read())
                        self.client.put(table_name, str(index), {tmp_column:base64_data})
                        index = index + 1

    def Download(self, table, columns, dest):
        values = self.client.scan_value(table, "1", columns)

        for i in range(len(columns)):
            image_path = dest + "/" + columns[i]
            if not os.path.exists(image_path):
                os.makedirs(image_path)

            for j in range(len(values[i])):
                image_data = base64.b64decode(values[i][j])
                image_name = image_path + "/" + str(j) + ".jpg"
                tmp_file = open(image_name, 'wb')
                tmp_file.write(image_data)
                tmp_file.close()
