from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from hbase import Hbase
from hbase.ttypes import *

class HBase(object):
  def __init__(self, ip='10.0.5.2', port=9090):
    self.transport = TSocket.TSocket(ip, port)
    protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
    self.client = Hbase.Client(protocol)
    self.transport.open()
    
  def __del__(self):
    self.transport.close()

  def get_tables(self):
    return self.client.getTableNames()

  def create_table(self, tabel, columns):
    func = lambda col: ColumnDescriptor(col)
    column_families = map(func, columns)
    self.client.createTable(tabel, column_families)

  def delete_table(self, tablename):
    self.client.deleteTable(tablename)
  
  def put(self, table, row, columns):
    """
    Usage
    client.put("table_name", "rowkey", {"column":"value"})
    if you want upload pictures, the 'value' should be base64 format
    """
    # func = lambda (k, v): Mutation(column=k, value=v)
    # mutations = map(func, columns.items())
    mutations = map(Mutation, columns.items())
    self.client.mutateRow(table, row, mutations)

  def delete(self, table, row, column):
    self.client.deleteAll(table, row, column)

  def get_row(self, table, row):
    row = self.client.getRow(table, row)
    return row
  
  def get_value(self, table, row, column):
    result = self.client.get(table, row, column)
    return result[0].value

  def scan_value(self, table, start_row, column):
    values = []
    for i in range(len(column)):
      values.append([])
    scanner = self.client.scannerOpen(table, start_row, column)
    while True:
      result = self.client.scannerGet(scanner)
      if not result:
        break
      for i in range(len(column)):
        values[i].append(result[0].columns[column[i]].value)
    return values

