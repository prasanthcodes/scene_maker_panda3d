import asyncore, socket
PORT = 55443

class FileServer(asyncore.dispatcher):
  bufSize = 2**15
  def __init__(self):
      asyncore.dispatcher.__init__(self)
      self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
      self.bind(('', PORT))
      self.listen(1)

  def handle_close(self):
      self.close()

  def handle_accept(self):
      c,a=self.accept()
      data=c.recv(self.bufSize)
      if data:
         IDE.IDE_openFilesFromSocket(data)

  def handle_read(self):
      pass
