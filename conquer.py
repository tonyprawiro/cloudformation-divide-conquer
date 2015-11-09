#!/usr/bin/python

import sys
import json
import os.path
from collections import OrderedDict

sCWD = os.getcwd()

# Make sure input filename is passed to the script
sInputFile = ""
try:
	sInputFile = sys.argv[1]
except:
	print "E/ Unable to find input file name. Usage: conquer.py input.json output.json"
	sys.exit(1)

# Make sure output filename is passed to the script
sOutputFile = ""
try:
	sOutputFile = sys.argv[2]
except:
	print "E/ Unable to find output file name. Usage: conquer.py input.json output.json"
	sys.exit(1)

# Determine the full path name of the input/output json file
sInputFile = "%s/%s" % (sCWD, sInputFile)
sOutputFile = "%s/%s" % (sCWD, sOutputFile)

# Make sure input and output file isn't the same
if sInputFile == sOutputFile:
	print "E/ Input and output file can't be the same"
	sys.exit(1)

# Try to open and parse json input file
stInputJSON = {}
try:
	sFileContent = ""
	with open(sInputFile) as data_file:
		stInputJSON = json.load(data_file, object_pairs_hook=OrderedDict)
except:
	print "E/ Unable to open or parse template file: %s" % (sInputFile)
	sys.exit(1)

# Make sure it has CloudFormation signature
try:
	sAWSTemplateFormatVersion = stInputJSON["AWSTemplateFormatVersion"]
except:
	print "E/ Unable to determine CloudFormation template format version. Is this a valid CloudFormation template ?"
	sys.exit(1)

# It has ? Ok good, let's prepare the output
stOutput = OrderedDict({
	"AWSTemplateFormatVersion": sAWSTemplateFormatVersion
})

# Now expand "Resource" node
stOutputResources = OrderedDict({})
stInputResources = OrderedDict({})
try:
	stInputResources = stInputJSON["Resources"]
except:
	print "N/ Unable to access Resources section. Does the template has any Resource at all ?"

# If there is any Resources, iterate
for sInputResourceID, value in stInputResources.items():
	sOutputResourceID = sInputResourceID
	resultValue = value
	if isinstance(value, str) or isinstance(value, unicode):
		aSegments = value.split("::")
		if len(aSegments) == 4 and aSegments[0] == "Resources":
			sSegmentResourceProd = aSegments[1]
			sSegmentResourceType = aSegments[2]
			sSegmentResourceID = aSegments[3]
			if sSegmentResourceID == "~":
				sSegmentResourceID = sInputResourceID
			sValueFile = "%s/Resources/%s/%s/%s.json" % (sCWD, sSegmentResourceProd, sSegmentResourceType, sSegmentResourceID)
			if os.path.isfile(sValueFile):
				try:
					with open(sValueFile) as value_file:
						resultValue = json.load(value_file)
				except:
					print "W/ Parsing `%s`: file %s contains invalid JSON object" % (sInputResourceID, sValueFile)
			else:
				# The resourcetype/id.json file does not exist
				print "N/ Parsing `%s`: unable to locate file: %s" % (sInputResourceID, sValueFile)
		else:
			# Value isn't in "Resources::yeah::right::whatever" format 
			print "N/ Parsing `%s`: value is string but isn't in supported pointer format: %s" % (sInputResourceID, value)
	else:
		# Value is not a string
		print "N/ Parsing `%s`: value isn't a string" % (sInputResourceID)

	stOutputResources[sOutputResourceID] = resultValue

# Hook in the Resources node
stOutput["Resources"] = stOutputResources

# Write output
try:
	f = open(sOutputFile, 'w')
	f.write(json.dumps(stOutput, indent=2))
	f.close()
except Exception, e:
	print "E/ Unable to write to output file: %s (%s)" % (sOutputFile, str(e))