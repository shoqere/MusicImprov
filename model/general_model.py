from model import *
from scripts import args, paras
import abc
import csv
from keras.callbacks import ModelCheckpoint, EarlyStopping, TensorBoard, CSVLogger
from keras.optimizers import Adam

class ToSeqModel(object):
	"""
		Create a general structure of the neural network
	"""
	def __init__(self, input_shape, output_shape, model_folder, model_name):
		self._model_name = model_name
		self._model_folder = model_folder
		self._file_path = model_folder + '/' + model_name + ".hdf5"
		self._input_shape = input_shape
		self._output_shape = output_shape
		self.optimizer = Adam(lr=0.001, clipnorm=1., clipvalue=0.5)
		self.model = None
		self.define_models()

	@abc.abstractmethod
	def define_models(self):
		pass

	def load(self, num='best'):
		try:
			self.model.load_weights(self._model_folder + '/' + self._model_name + '_' + str(num) +'.hdf5')
		except IOError:
			pass

	@abc.abstractmethod
	def fit(self, data, callbacks_list):
		pass

	def train(self, data, test_data):
		try:
			self.load()
		except IOError:
			pass

		checkpoint = ModelCheckpoint(
			self._model_folder + '/' + self._model_name + '_best.hdf5',
			monitor='val_loss',
			verbose=0,
			save_weights_only=True,
			save_best_only=True
		)
		csv_logger = CSVLogger(self._model_folder + '/' + self._model_name + '_' + 'training.log', append=True)
		early_stopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=paras.early_stopping, verbose=0, mode='min')
		tensorboard = TensorBoard(log_dir="logs/" + paras.exp_name + '/' + self._model_name)
		inspect = Eval(self._model_folder + '/' + self._model_name, self.get_score, data, test_data)
		callbacks_list = [ProgbarLoggerVerbose('samples'), inspect, csv_logger, tensorboard, checkpoint, early_stopping]

		# Train
		history = self.fit(data, callbacks_list)

	@abc.abstractmethod
	def get_score(self, inputs, outputs):
		pass

	@abc.abstractmethod
	def generate(self, inputs):
		pass

	@abc.abstractmethod
	def get_score(self, inputs, outputs):
		pass


