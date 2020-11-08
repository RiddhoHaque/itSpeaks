from os import walk
f = []
for (dirpath, dirnames, filenames) in walk('/home/riddho/itSpeaksFlask/static/uploads/audiobooks/1_5'):
	f.extend(filenames)
	break

print(f)
