from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras.layers import Activation, GaussianNoise
from keras.layers import Dense, Input, Lambda, LSTM, Concatenate, RepeatVector, Bidirectional, Layer, Multiply, Add, TimeDistributed
from keras.models import Model, Sequential
from keras.utils import plot_model
from model import *
from scripts import args, MelodySequence

class NoteRNN(object):
	def __init__(self, input_shape, output_shape , model_name):
		self._model_name = model_name
		self._file_path = "weights/{}.hdf5".format(self._model_name)
		self._input_shape = input_shape
		self._output_shape = output_shape
		self.define_models()

	def define_models(self):

		self.model = Sequential()
		self.model.add(LSTM(args.num_units, input_shape=(None, self._input_shape[1]), return_sequences=True))
		self.model.add(TimeDistributed(Dense(self._output_shape[1], activation='softmax')))

		self.optimizer = Adam(clipnorm=1., clipvalue=0.5)
		self.model.compile(optimizer=self.optimizer, loss='categorical_crossentropy', metrics=['acc'])
		self.model.summary()

		plot_model(self.model, to_file='model.png')

	def train(self, data, test_data, testscore):
		try:
			self.load()
		except IOError:
			pass

		checkpoint = ModelCheckpoint(
			self._file_path,
			monitor='val_loss',
			verbose=0,
			save_best_only=True,
			save_weights_only=True,
			mode='min'
		)
		early_stopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=2, verbose=0, mode='min')

		callbacks_list = [checkpoint, early_stopping]

		all_history = {'loss': [],
		               'val_loss': [],
		               'acc': [],
		               'val_acc': []}

		starting_lrate = 1e-3
		ending_lrate = 1e-5

		def train_generator(inputs, outputs):
			for i in range(len(inputs)):
				yield array([inputs[i]]), array([outputs[i]])


		for i in range(args.epochs):
			print('=' * 80)
			print("EPOCH " + str(i + 1))
			lrate = starting_lrate - (starting_lrate - ending_lrate) / args.epochs * i
			K.set_value(self.optimizer.lr, lrate)

			# Train
			history = self.model.fit_generator(train_generator(data.inputs, data.outputs),
				callbacks=callbacks_list,
				epochs=1,
			    steps_per_epoch=len(data.inputs),
				verbose=2
			)
			self.model.save(self._file_path.format(self._model_name))

			# all_history['val_acc'] += history.history['val_acc']

			# Evaluation
			print '###Test Score: ', self.get_score(test_data.inputs, test_data.outputs, printing=(i+1) % 10 == 0)

			self.generate_from_primer(testscore, save_name='melody' + str(i))

		plot_training_loss(self._model_name, all_history)

	def generate(self, inputs):
		return self.model.predict(inputs)[0]

	def load(self):
		try:
			self.model.load_weights(self._file_path)
		except IOError:
			pass

	def get_score(self, inputs, outputs, printing=False):
		y_pred = []
		y_true = []
		for i in range(len(inputs)):
			prediction = self.generate(array([inputs[i]]))
			if printing and i % 5 == 0:
				print 'y=%s, yhat=%s' % ([n - 3 for n in one_hot_decode(outputs[i])], [n - 3 for n in one_hot_decode(prediction)])
			y_pred += one_hot_decode(prediction)
			y_true += one_hot_decode(outputs[i])
		print 'f1 score', micro_f1_score(y_pred, y_true, printing=printing)

	def generate_from_primer(self, testscore, length=args.num_output_bars * args.steps_per_bar, save_name='untitled', cut=False):
		# Generation
		input_shape = get_input_shapes()
		original = [0] + [n + 3 for n in testscore[:input_shape[0]]]
		primer = [n for n in original]
		silence = 0
		while True:
			output = self.generate(array([to_onehot(primer, input_shape[1])]))
			output = one_hot_decode(output)[-1]
			if output < 3:
				silence += 1
			else:
				silence = 0
			if cut and silence >= args.steps_per_bar:
				original = original[:-silence]
				primer = primer[1:-silence]
				print 'Cut'
				silence = 0
				continue
			original.append(output)
			primer.append(output)
			if len(original) > length + args.num_input_bars * args.steps_per_bar:
				MelodySequence([int(n - 3) for n in original[1:]]).to_midi('generated/' + save_name, save=True)
				print 'Generated: ', [int(n - 3) for n in original[1:]]
				break
