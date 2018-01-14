import _pickle as cPickle
import os

class PickleApi:
	def __init__(self):
		self.pickle_dict = {}
		self.database_name = '\database.db'
		self.file_path = self.getAddonPath() + self.database_name
		if os.path.isfile(self.file_path):
			if os.path.getsize(self.file_path) > 0:
				with open(self.file_path, 'rb') as pickle_file:
					self.pickle_dict = cPickle.load(pickle_file)
		else:
			self.pickle_dict = {'0':'0'}
			with open(self.file_path, 'wb') as pickle_file:
				cPickle.dump(self.pickle_dict, pickle_file)
				
	def getDict(self):
		return self.pickle_dict
		
	def save(self):
		with open(self.file_path,'wb') as pickle_file:
			cPickle.dump(self.pickle_dict, pickle_file)
		
	def getAddonPath(self):
		path = os.path.dirname(os.path.abspath(__file__))
		return path		


pickle = PickleApi()