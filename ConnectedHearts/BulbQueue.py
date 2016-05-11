from multiprocessing.queues import Queue

class BulbQueue(Queue):
    """ 
    BulbQueue inherits from multiprocessing.Queue, but has the added 
    functionality that it keeps track of its size while putting and getting 
    elements from the queue. Multiprocessing.Queue makes no guarantees when
    calling its size method.
    """
    def __init__(self):
        super(BulbQueue, self).__init__()
        self.queuesize = 0

    def empty(self):
        return super(BulbQueue, self).empty()

    def size(self):
        queuesize = self.queuesize
        return queuesize

    def get(self):
        if not self.empty():
            self.queuesize -= 1
            return super(BulbQueue, self).get() 
        else:
            return None

    def put(self, item):
        super(BulbQueue, self).put(item)
        self.queuesize += 1
