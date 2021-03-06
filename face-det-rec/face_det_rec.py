#
# Face detection and recognition using dlib and the face_recognition api.
# 
# References:
# See https://github.com/ageitgey/face_recognition.
# See https://www.pyimagesearch.com/2018/06/18/face-recognition-with-opencv-python-and-deep-learning/.
#
# Part of the smart-zoneminder project:
# See https://github.com/goruck/smart-zoneminder.
#
# Copyright (c) 2018 Lindo St. Angel.
#

import face_recognition
import argparse
import pickle
import cv2
import json

import sys
from sys import argv
from sys import exit
from sys import stdout

# Get image paths from command line.
if len(sys.argv) == 1:
    exit('No test image file paths were supplied!')

# Construct list from images given on command line. 
objects_detected = argv[1:]

# load the known faces and embeddings
# TODO - add error handleing. 
data = pickle.loads(open('/home/lindo/develop/smart-zoneminder/face-det-rec/encodings.pickle', "rb").read())

# List that will hold all images with any face detection information. 
objects_detected_faces = []

# Loop over the images given in the command line.  
for obj in objects_detected:
	json_obj = json.loads(obj)
	img = cv2.imread(json_obj['image'])

	for label in json_obj['labels']:
		# If the object detected is a person then try to identify face. 
		if label['name'] == 'person':
			# If no face is detected name will be set to None (null in json).
			name = None

			# First bound the roi using the coord info passed in.
			# The roi is area around person(s) detected in image.
			# (x1, y1) are the top left roi coordinates.
			# (x2, y2) are the bottom right roi coordinates.
			y2 = int(label['box']['ymin'])
			x1 = int(label['box']['xmin'])
			y1 = int(label['box']['ymax'])
			x2 = int(label['box']['xmax'])
			roi = img[y2:y1, x1:x2, :]

			# Covert from cv2 format.
			rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

			# detect the (x, y)-coordinates of the bounding boxes corresponding
			# to each face in the input image, then compute the facial embeddings
			# for each face
			box = face_recognition.face_locations(rgb, number_of_times_to_upsample=1,
				model='cnn')

			encodings = face_recognition.face_encodings(rgb, box)

			# loop over the facial embeddings
			for encoding in encodings:
				# attempt to match each face in the input image to our known encodings
				matches = face_recognition.compare_faces(data['encodings'],
					encoding)

				# If a face is detected but has no match set name to Unknown.
				name = 'Unknown'

				# check to see if we have found a match
				if True in matches:
					# find the indexes of all matched faces then initialize a
					# dictionary to count the total number of times each face
					# was matched
					matchedIdxs = [i for (i, b) in enumerate(matches) if b]
					counts = {}

					# loop over the matched indexes and maintain a count for
					# each recognized face face
					for i in matchedIdxs:
						name = data['names'][i]
						counts[name] = counts.get(name, 0) + 1

					# determine the recognized face with the largest number of
					# votes (note: in the event of an unlikely tie Python will
					# select first entry in the dictionary)
					name = max(counts, key=counts.get)

			# Add face name to label metadata.
			label['face'] = name

	# Add processed image to output list. 
	objects_detected_faces.append(json_obj)

# Convert json to string and return data. 
print(json.dumps(objects_detected_faces))
sys.stdout.flush()