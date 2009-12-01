from os import path
import csv
import re
import sys
import unicodedata
from django.utils.encoding import smart_unicode, force_unicode
from htmlentitydefs import name2codepoint

def csv_to_dict(filename):
	output_dict = []
	pattern = re.compile(r'\"([\w\'-]*)\"')
	input_buffer = open(filename, 'rb')
	csv_reader = csv.reader(input_buffer)
	first_row = True
	for row in csv_reader:
		if first_row:
			clean_row = clean_dict_strings(row, pattern)
			keys = clean_row
			first_row = False
		else:
			output_dict.append({})
			clean_row = clean_dict_strings(row, pattern)
			for i,f in enumerate(clean_row):
				output_dict[-1][keys[i]] = f
	return output_dict

def clean_dict_strings(dict, pattern=re.compile(r'\"([\w\'-]*)\"')):
	for i,f in enumerate(dict):
		f = f.strip()
		re_match = pattern.match(f)
		if re_match:
			dict[i] = pattern.sub(r'\1', f)
		else:
			dict[i] = f
		try:
			dict[i] = int(dict[i])
		except ValueError:
			pass
	return dict

def slugify(s, entities=True, decimal=True, hexadecimal=True, instance=None, slug_field='slug', filter_dict=None):
	s =smart_unicode(s)
	
	if entities:
		s = re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)
	
	if decimal:
		try:
			s = re.sub('&#(\d+);', lambda m: unichr(int(m.group(1))), s)
		except:
			pass
	
	if hexadecimal:
		try:
			s = re.sub('&#x([\da-fA-F]+);', lambda m: unichr(int(m.group(1), 16)), s)
		except:
			pass
	
	s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
	s = re.sub(r'[^-a-z0-9]+', '-', s.lower())
	s = re.sub('-{2,}', '-', s).strip('-')
	slug = s
	
	if instance:
		def get_query():
			query = instance.__class__.objects.filter(**{slug_field: slug})
			if filter_dict:
				query = query.filter(**filter_dict)
			if instance.pk:
				query = query.exclude(pk=instance.pk)
			return query
		counter = 1
		while get_query():
			slug = "%s-%s" % (s, counter)
			counter += 1
		
	return slug

def process_import_file(import_file, session, tmpfile_location='/tmp/'):
    """
    Open the uploaded file and save it to the temp file location specified
    in BATCH_IMPORT_TEMPFILE_LOCATION, adding the current session key to
    the file name. Then return the file name so it can be stored in the
    session for the current user.

    **Required arguments**
    
    ``import_file``
        The uploaded file object.
       
    ``session``
        The session object for the current user.
        
    ** Returns**
    
    ``save_file_name``
        The name of the file saved to the temp location.
        
        
    """
    IMPORT_TEMPFILE_LOCATION = tmpfile_location
    import_file_name = import_file.name
    session_key = session.session_key
    save_file_name = session_key + import_file_name
    destination = open(path.join(IMPORT_TEMPFILE_LOCATION, save_file_name), 'wb+')
    for chunk in import_file.chunks():
        destination.write(chunk)
    destination.close()
    return save_file_name
