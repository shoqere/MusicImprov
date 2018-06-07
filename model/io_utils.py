import json
import os
import music21
from numpy import array, zeros, shape, ndarray, sin, cos, pi, sqrt, argmin
from scripts import args, to_onehot, MusicXML, XMLtoNoteSequence
from xml.etree import cElementTree

try:
	with open('score_list.json', 'r') as f:
		score_list = json.load(f)
except IOError:
	score_list = []

def create_dataset(folder):
	"""
	Generate training and testing dataset from a folder of MusicXML file
	:param folder: the path to the folder
	:return: a list of input-output, input args, output args
	"""
	if args.savedata:
		try:
			with open(args.phrase_file + '.json', 'r') as f:
				data = json.load(f)
		except IOError:
			data = []

		scores = os.listdir(folder)
		for score in scores:
			if (score.endswith('.mxl')) and (score not in score_list):
				score_list.append(score)
				print('Processing ' + score + '...')
				s = MusicXML()
				try:
					s.from_file(folder + '/' + score)
				except (cElementTree.ParseError,
				        music21.musicxml.xmlToM21.MusicXMLImportException,
				        music21.exceptions21.StreamException):
					print("Conversion failed.")
					continue

				transformer = XMLtoNoteSequence()
				if s.time_signature.ratioString != '4/4':
					print("Skipping this because it's " + s.time_signature.ratioString)
					continue
				try:
					melody = transformer.transform(s)
				except:
					continue
				# print(len(melody))
				data.append(melody)

				print str(len(score_list)) + "(" +  str(len(data))+")/" + str(len(scores))

			with open('score_list.json', 'w') as f:
				json.dump(score_list, f)

			with open(args.phrase_file + '.json', 'w') as f:
				json.dump(data, f)

	with open(args.phrase_file+'.json') as f:
		data = json.load(f)

	melodies = data
	inputs = []
	outputs = []
	print('Datashape: ', shape(data))
	input_shape = (args.num_bars * args.steps_per_bar, 3)
	output_shape = (args.steps_per_bar, 3)
	for i, melody in enumerate(melodies):
		# next_melody = melodies[i+1]
		# next_melody = [n + 2 for n in next_melody]
		# outputs.append(to_onehot(next_melody, output_shape[1]))
		# inputs.append(encode_melody(melody))
		j = 0
		while j < len(melody) - (args.num_bars+1) * args.steps_per_bar:
			next_bar = melody[j+args.steps_per_bar * args.num_bars: j+args.steps_per_bar*(args.num_bars + 1)]
			next_bar = [n+2 for n in next_bar]
			inputs.append(encode_melody(melody[j: j + args.steps_per_bar * args.num_bars]))
			outputs.append(encode_melody(next_bar))
			j += args.steps_per_bar

	print(shape(inputs))
	print(shape(outputs))
	print(input_shape)
	print(output_shape)
	return array(inputs), array(outputs), input_shape, output_shape

def midi_to_name(midi):
	midi = midi + 48
	names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

	# octave = (midi / 12) - 1
	note_index = midi % 12
	return names[note_index]

def name_to_spiral(name):
	r = 4
	h = 1
	spiral = ["C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "D#", "A#", "F"]
	k = spiral.index(name)
	return [r*sin(k*pi/2), r*cos(k*pi/2), r*h]

def dist(p1, p2):
	dist = 0
	for i in range(len(p1)):
		dist += (p1[i] - p2[i]) ** 2
	return sqrt(dist)


def spiral_to_name(position):
	r = 4
	h = 1
	spiral = ["C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "D#", "A#", "F"]
	positions = [[r*sin(k*pi/2), r*cos(k*pi/2), r*h] for k in range(len(spiral))]
	distances = array([dist(position, p) for p in positions])
	return spiral[distances.argmin()]

def name_to_midi(name):
	names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
	return 60 + names.index(name)

def encode_melody(melody):
	"""
	Encode a melody sequence into the net's input
	:param melody:
	:return:
	"""
	return [name_to_spiral(midi_to_name(n+2)) for n in melody]

	melody = [n + 2 for n in melody]
	input_sequence = []
	context = zeros(12)
	prev = 0
	silent = 0

	i = 0
	first_note = melody[i]
	while first_note < 0:
		first_note = melody[i+1]
		i += 1

	for k, n in enumerate(melody):
		feature = zeros(32)
		pitchclass = zeros(13)
		if n >= 2:
			interval = n - prev
			prev = n
			silent = 0
			interval_from_first_note = n - first_note
			pitchclass[int((n + 22) % 12)] = 1
			interval_from_last_note = n
		else: # silence
			silent += 1
			interval = 0
			interval_from_first_note = 0
			pitchclass[12] = 1

		position = n
		position_in_bar = k
		feature[0] = position
		feature[1:14] = pitchclass
		feature[15] = interval
		feature[16:28] = context
		feature[29] = silent
		feature[30] = interval_from_first_note
		feature[31] = position_in_bar
		input_sequence.append(feature)

		if n >= 2:
			context[int((n + 22) % 12)] += 1

	return input_sequence
