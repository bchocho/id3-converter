import argparse
import os
import sys
import tagger

def main():
	parser = argparse.ArgumentParser(description=
	"""Convert ID3 tags that have messed up "encoding""")
	parser.add_argument('path')
	parser.add_argument('--from-encoding',
		default='euc-kr')
	parser.add_argument('--to-encoding',
		default='utf_16')
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

	convert(args.path, args.out_dir, args.from_encoding, args.to_encoding,
		args.dry_run, args.move, args.verbose)

def print_verbose(verbose, line):
	if verbose:
		print line

def convert(path, out_dir, from_encoding, to_encoding, dry_run, move, verbose):
	if (os.path.isdir(path)):
		for p in os.listdir(path):
			convert(os.path.join(path, p), out_dir, from_encoding, to_encoding, dry_run, move, verbose)
	elif (os.path.isfile(path)):
		# Ignore ID3v1, no one cares anyway
		try:
			id3 = tagger.ID3v2(path)
			tag_exists = id3.tag_exists()
		except:
			print "Could not parse ID3v2: %s" % path
			tag_exists = False

		if tag_exists:
			songname = ''
			artist = ''
			all_correct_encoding = True
			for frame in id3.frames:
				try:
					print_verbose(verbose, "BEFORE: %s (%s) %s" % \
						(frame.fid, frame.encoding, str(frame.strings)))
					is_correct_encoding = True
					if len(frame.strings) > 0:
						newframestr = u''
						# Check if correct encoding
						if frame.encoding == 'utf_16':
							is_correct_encoding = True
						else:
							for framestr in frame.strings:
								try:
									framestr.encode(frame.encoding)
								except:
									print "COULD NOT ENCODE "+frame.fid
									is_correct_encoding = False
									all_correct_encoding = False
						# Create string with corrent encoding
						for framestr in frame.strings:
							if is_correct_encoding:
								print_verbose(verbose, 'IF: '+framestr.encode(frame.encoding))
								try:
									newframestr += framestr
								except Exception, e:
									#noop = 0
									print e
							else:
								try:
									print_verbose(verbose, 'ELSE: '+framestr.decode(from_encoding))
									newframestr += framestr.decode(from_encoding)
								except Exception, e:
									newframestr = u''
									print e
						if frame.fid == 'TIT2' or frame.fid == 'TT2': #TT2 is v2.2
							songname = newframestr
							print_verbose(verbose, 'SONGNAME: '+songname)
						elif frame.fid == 'TPE1' or frame.fid == 'TP1':
							artist = newframestr
							print_verbose(verbose, 'ARTIST: '+artist)
						# Replace string if it was previously bad
						if not is_correct_encoding:
							frame.set_text(newframestr, to_encoding)
					print_verbose(verbose, (" AFTER: %s (%s) %s" % \
						(frame.fid, frame.encoding, str(frame.strings))))
				except Exception, e:
					noop = 0
					print_verbose(verbose, ("%s - unprintable" % frame.fid))
					print_verbose(verbose, e)
			if not all_correct_encoding:
				# TODO fix the problem where an errant '\x00' screws everything up
				if len(artist) == 0 or len(songname) == 0:
					print "UNKNOWN ARTIST: %s OR SONGNAME: %s" % (artist, songname)#(map(hex, map(ord, artist)), map(hex, map(ord, songname)))
				else:
					filename = '%s - %s.mp3' % (artist, songname)
					filename = filename.replace('\x00','').replace('/','-')
					print filename
					if not dry_run:
						id3.commit_to_file(os.path.join(out_dir, filename))
						if move:
							try:
								os.remove(path)
							except Exception, e:
								print("Could not remove "+path)
			#id3.commit_to_file(id3.artist.decode('euc-kr')+' - '+id3.songname.decode('euc-kr')+'.mp3')

		# TODO: just change the filename encoding, but this is more difficult!
		# Can't figure out how the filepath is encoded/decoded
		# Instead, rename to "artist - songname"?

		#print type(path)
		#print map(ord, '1-01')
		#print map(ord, '.mp3')
		#print map(ord, path)[16:]
		#print map(hex, map(ord, path))[16:]
		#print path
		#print path.decode('euc_kr')#.encode('utf-8')
	elif (os.path.exists(path)):
		print 'Error, '+path+' exists but is neither a file or dir'
	else:
		print 'Error, '+path+' is neither a file or dir'

if __name__ == "__main__":
    main()