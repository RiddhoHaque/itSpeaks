import subprocess

def textToWav(text,file_name):
   subprocess.call(["espeak", "-w"+file_name+".wav", text, "-s "+str(100)])

textToWav('riddhohaque @ gmail.com!','hello')
