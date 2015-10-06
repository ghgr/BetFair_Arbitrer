"""
The MIT License (MIT)

Copyright (c) 2015 Eduardo Pena Vina

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import datetime

class LogManager:
	def __init__(self, logs_directory,event_id=None):
		self.logs_directory = logs_directory
		self.event_id = event_id
		self.open_files= {}
	

	def parseFilename(self,filename):
		if filename==None:
			return None
		filename = str(filename)
		filename = filename.replace(".log","")
		if self.event_id!=None:
			filename+="_"+str(self.event_id)
		filename+=".log"
		return filename

	def log(self,filename,*kwdata):
		filename = self.parseFilename(filename)

		if filename in self.open_files:
			w=self.open_files[filename]
		else:
			w = open(self.logs_directory+"/"+filename,"w")
			self.open_files[filename]=w
			w.write("File "+str(filename)+" created at "+str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))+"\n")
	
		for elem in kwdata:
			w.write(str(elem)+" ")
		w.write("\n")
	
	def close(self, filename=None):
		filename = self.parseFilename(filename)
		if filename==None:
			for filename,w in self.open_files.iteritems():
				w.write("File "+str(filename)+" closed at "+str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))+"\n")
				w.close()
		else:
			w = self.open_files[filename]
			w.write("File "+str(filename)+" closed at "+str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))+"\n")
			del self.open_files[filename]

	def flush(self,filename=None):
		filename = self.parseFilename(filename)
		if filename==None:
			for filename,w in self.open_files.iteritems():
				w.flush()
		else:
			self.open_files[filename].flush()


if __name__=="__main__":
	log = LogManager("test")
	log.log("log1.log",1234,"hola amigo",[1,2,3])
	log.log("log1.log",1234,"hola amigo",[1,2,3])
	log.log("log1.log",1234,"hola amigo",[1,2,3])
	log.flush("log1")
	log.log("log1.log",1234,"ahola amigo",[1,2,3])
	log.close("log1")
	log.close()

