import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import *
from scripts.configure import args
from scripts import *


from collections import Counter


def melody_generate(model, testscore, use_generated_as_primer=True):
	count = 0
	whole = testscore[:args.num_bars * args.steps_per_bar - 1]
	positions = [k % 12 for k in range(args.num_bars * args.steps_per_bar - 1)]

	while True:
		primer = whole[-(args.num_bars * args.steps_per_bar-1):]
		output_note = model.generate(encode_melody(primer), array(positions), 'generated/bar_' + str(count))
		print(output_note)
		whole += [output_note]
		positions = [(k + count) % 12 for k in range(args.num_bars * args.steps_per_bar - 1)]

		count += 1
		if count > 128:
			MelodySequence(whole).to_midi('generated/whole', save=True)
			break
	# if use_generated_as_primer:
	# 	primer = transformer.transform(phrases[0])
	# 	print(primer)
	# 	primer.to_midi('original', save=True)
	# 	for i in range(5):
	# 		primer = model.generate(encode_melody(primer), 'generated/generate_' + str(i))
	pass

def generate():
	inputs1, inputs2, outputs, input_shape, input_shape2, output_shape = create_dataset(args.dataset)

	melody_model = MelodyAnswerNet(input_shape, input_shape2, output_shape, 'MelodyModel'
	                               + str(args.num_bars) + '_'
	                               + str(args.steps_per_bar) + '_'
	                               + str(args.dropout) + '_'
	                               + str(args.temperature) + args.note)


	testscore = MusicXML()
	testscore.from_file(args.test)
	transformer = XMLtoNoteSequence()
	testscore = transformer.transform(testscore)

	if args.train:
		melody_model.train(inputs1, inputs2, outputs, testscore)

	melody_generate(melody_model, testscore)

if __name__ == '__main__':
	generate()
