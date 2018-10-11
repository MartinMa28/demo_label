# from aimaster.parser.LMDB import LMDB
from cvat.apps.engine.aimaster.parser.KFB import KFB

class DATA_SET(object):
    def __init__(self, ip='10.0.5.2'):
        self.ip = ip
        self.kfb = KFB(self.ip)
        # self.lmdb = LMDB(self.ip)
        
    def __kfb_upload(self, src, dest, table_name, num=20, scale=20):
        self.kfb.Generate(src, dest, num, scale)
        self.kfb.Upload(dest, table_name, scale)
        
    def __lmdb_upload(self, src, dest, table_name):
        self.lmdb.Upload(src, dest, table_name)
        
    def __lmdb_download(self, table, dest):
        self.lmdb.Download(table, dest)

    def __kfb_download(self, table, dest, columns):
        self.kfb.Download(table, columns, dest)
        
    def upload(self, type, src, dest, table_name, num=20, scale=20):
        if type == 'kfb':
            self.__kfb_upload(src, dest, table_name, num, scale)
                
        elif type == 'lmdb':
            self.__lmdb_upload(src, dest, table_name)

    def download(self, type, table_name, dest, columns=[]):
        if type == 'lmdb':
            self.__lmdb_download(table_name, dest)

        elif type == 'kfb':
            self.__kfb_download(table_name, dest, columns)
            
