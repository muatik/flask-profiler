class BaseStorage(object):
    """docstring for BaseStorage"""

    def __init__(self):
        super(BaseStorage, self).__init__()

    def filter(self, criteria):
        raise Exception("Not implemented Error")

    def getSummary(self, criteria):
        raise Exception("Not implemented Error")

    def insert(self, measurement):
        raise Exception("Not implemented Error")

    def delete(self, measurementId):
        raise Exception("Not implemented Error")

    def truncate(self):
        raise Exception("Not implemented Error")
