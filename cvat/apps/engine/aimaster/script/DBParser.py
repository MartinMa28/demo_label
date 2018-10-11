# -*- coding: utf-8 -*-

import os
import sqlite3


# 数据组成: [[name,confidence,scale,layer,xmin,ymin,xmax,ymax],....]
#   name: 标注的类别
#   confidence: 标注医生诊断的把握度
#   scale: 在scale倍镜下诊断
#   layer: 在第几层诊断
#   xmin,ymin,xmax,ymax: 标注在1倍镜下的坐标
#  例子：
#    db = DBReader()
#    db.Read('20010001测试_2018-01-09 18_39_29.db')
#    db.Save('new.db')
class DBio:
    def __init__(self, version=0):
        if version == 0:
            self.table_name = 'RegUnitInfo'
            self.map = {'label': 1, 'xmin': 2, 'ymin': 3, 'width': 4,
                        'height': 5}
        # elif version == 1:
        #     self.table_name = 'Annotations'
        #     self.map = {'label': 0, 'conf': 1, 'layer': 2, 'scale': 3,
        #                 'xmin': 4, 'ymin': 5, 'xmax': 6, 'ymax': 7}
        # elif version == 2:
        #     self.table_name = 'Annotations'
        #     self.map = {'label': 1, 'conf': 2, 'layer': 3, 'scale': 4,
        #                 'xmin': 5, 'ymin': 6, 'xmax': 7, 'ymax': 8}
        else:
            self.table_name = 'Annotations'
            self.map = {'Name': 'label', 'Confidence': 'conf', 'Layer': 'layer', 'Scale': 'scale',
                        'Left': 'xmin', 'Top': 'ymin', 'Right': 'xmax', 'Bottom': 'ymax'}

    def _dic_factory(self, cursor, row):
        data = {}
        for idx, col in enumerate(cursor.description):
            if col[0] in self.map:
                data[self.map[col[0]]] = row[idx]
        return data

    def Read(self, filepath):
        if not os.path.exists(filepath):
            return []
        db = sqlite3.connect(filepath)
        db.row_factory = self._dic_factory
        cursor = db.cursor()
        # RegUnitInfo Annotations
        cursor.execute("select * from " + self.table_name)
        return list(cursor)

    def Get(self, index=None):
        if index is None:
            return self.boxes
        else:
            return self.boxes[index]

    # 实验中，无法使用
    # do not use , it is experimental
    def Save(self, filepath, datas):
        db = sqlite3.connect(filepath)
        db.execute("CREATE TABLE IF NOT EXISTS Annotations("
                   "UID INTEGER PRIMARY KEY AUTOINCREMENT,"
                   "Name VARCHAR (256),"
                   "Confidence DOUBLE,"
                   "Layer    INT,"
                   "Scale    DOUBLE,"
                   "Left     DOUBLE,"
                   "Top      DOUBLE,"
                   "Right    DOUBLE,"
                   "Bottom   DOUBLE)")
        for data in datas:
            data['UID'] = None
            cmd = "Insert into Annotations(UID,Name,Confidence,Layer,Scale,Left,Top,Right,Bottom) " \
                  "values(:UID,:Name,:Confidence,:Layer,:Scale,:Left,:Top,:Right,:Bottom)"
            db.execute(cmd, data)
        try:
            db.commit()
        except:
            db.rollback()


def ReadDB(filepath, version=1):
    db = DBio(version)
    return db.Read(filepath)
