import argparse
import os
import sys
import logging
import tagger

def main():
	parser = argparse.ArgumentParser(description=
	'''Convert ID3 tags that have messed up "encoding"''')
	parser.add_argument('path')
	parser.add_argument('--from-encoding',
		default='euc-kr')
	parser.add_argument('--out-dir',
		default='out/')
	parser.add_argument('--dry-run',
		action='store_true')
	parser.add_argument('--move',
		action='store_true')
	parser.add_argument('--verbose',
		action='store_true')
	parser.set_defaults(dry_run=False, move=False, verbose=False)

	args = parser.parse_args()

	if not os.path.isdir(args.out_dir):
		print "Could not use out-dir %s" % args.out_dir
		sys.exit(1)

	convert(args.path, args.out_dir, args.from_encoding,
		args.dry_run, args.move, args.verbose)

def print_verbose(verbose, line):
	if verbose:
		print line

def is_encoding_correct(str, encoding):
	if encoding == 'utf-16': # TODO: Is this necessary?
		return True
	else: 
		try:
			str.encode(encoding)
			return True
		except:
			return False

def decode_string(str, from_encoding):
	decoded_str = str.decode(from_encoding)
	return decoded_str

def frame_strings_to_string(frame_strings):
	str = u''
	for framestr in frame_strings:
		str += framestr
	return str

def create_filepath(out_dir, artist, songname):
	if artist != None and len(artist) == 0:
		artist = "UNKNOWN ARTIST"
	if songname != None and len(songname) == 0:
		songname = "UNKNOWN SONG"
	filename = '%s - %s.mp3' % (artist, songname)
	filename = filename.replace('\x00','').replace('/','-') # fix the problem where an errant '\x00' screws everything up
	print filename
	return os.path.join(out_dir, filename)

def write_file(id3, filepath, move):
	# TODO: right now, if we get the same filename it will get overwritten
	id3.commit_to_file(filepath)
	if move:
		try:
			os.remove(path)
		except Exception, e:
			print("Could not remove "+path)


def convert(path, out_dir, from_encoding, dry_run, move, verbose):
	if (os.path.isdir(path)):
		for p in os.listdir(path):
			convert(os.path.join(path, p), out_dir, from_encoding, dry_run, move, verbose)
	elif (os.path.isfile(path)):
		# Ignore ID3v1, no one cares anyway
		try:
			id3 = tagger.ID3v2(path)
			tag_exists = id3.tag_exists()
		except:
			print "Could not parse ID3v2: %s" % path
			tag_exists = False

		if tag_exists:
			all_encoding_is_correct = True
			for frame in id3.frames:
				print_verbose(verbose, "BEFORE: %s (%s) %s" % \
					(frame.fid, frame.encoding, str(frame.strings)))

				frame_encoding_is_correct = True
				# Check if at least one incorrect encoding
				for framestr in frame.strings:
					if not is_encoding_correct(framestr, frame.encoding):
						print "Found bad encoding "+path+", "+frame.fid
						frame_encoding_is_correct = False
						all_encoding_is_correct = False
				# If at least one incorrect encoding, convert all to UTF-8
				if not frame_encoding_is_correct:
					frame.encoding = "utf_8"
					for idx, framestr in enumerate(frame.strings):
						try:
							frame.strings[idx] = decode_string(framestr, from_encoding)
							print_verbose(verbose, "reencoded string %s" % frame.strings[idx])
						except Exception, e:
							print "Could not convert "+path+", "+frame.fid+" using "+from_encoding
							logging.exception("Stack Trace")
							# TODO: stop looking at this file
				if frame.fid == 'TPE1' or frame.fid == 'TP1':
					artist = frame_strings_to_string(frame.strings)
				elif frame.fid == 'TIT2' or frame.fid == 'TT2':
					songname = frame_strings_to_string(frame.strings)

				print_verbose(verbose, (" AFTER: %s (%s) %s" % \
					(frame.fid, frame.encoding, str(frame.strings))))

			if not all_encoding_is_correct:
				filepath = create_filepath(out_dir, artist, songname)
				if not dry_run:
					write_file(id3, filepath, move)
	elif (os.path.exists(path)):
		print 'Error, '+path+' exists but is neither a file or dir'
	else:
		print 'Error, '+path+' is neither a file or dir'

if __name__ == "__main__":
    main()