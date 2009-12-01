import os, sys
from django.template import RequestContext
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response

from product.models import ProductVariation
from inventory_import.forms import UploadImportFileForm
from inventory_import.utils import process_import_file, csv_to_dict

IMPORT_RESULTS_TEMPLATE = 'inventory_import/results.html'
IMPORT_UPLOAD_TEMPLATE = 'inventory_import/upload.html'
try:
	IMPORT_TEMPFILE_LOCATION = getattr(settings, 'IMPORT_TEMPFILE_LOCATION')
except (AttributeError, NameError):
	IMPORT_TEMPFILE_LOCATION = '/tmp/'

@staff_member_required
def upload(request, extra_context=None):
	"""
	Start the import process by presenting/accepting a form into
	which the user specifies the model for whom a CSV file is
	being uploaded and the file/path of the file to upload.
	
	**Required arguments**
	
	none.
	
	**Optional arguments**
	   
	``extra_context``
		A dictionary of variables to add to the template context. Any
		callable object in this dictionary will be called to produce
		the end result which appears in the context.	
	
	"""
	status_dict = {}
	status_dict['update_results_messages'] = []
	status_dict['error_results_messages'] = []
	status_dict['num_rows_processed'] = 0
	status_dict['num_items_updated'] = 0
	status_dict['num_errors'] = 0
	if request.method == 'POST':
		form = UploadImportFileForm(request.POST, request.FILES)
		if form.is_valid():
			save_file_name = process_import_file(form.cleaned_data['import_file'], request.session, IMPORT_TEMPFILE_LOCATION)
			import pdb
			pdb.set_trace()
			try:
				product_data = csv_to_dict(os.path.join(IMPORT_TEMPFILE_LOCATION, save_file_name))
			except IOError:
				status_dict['error_results_messages'].append('Error opening CSV file: '+ `sys.exc_info()[1]`)
				return _render_results_response(request, status_dict, extra_context)
			
			site = Site.objects.get_current()
			#TODO Make this more efficient!!
			for index, row in enumerate(product_data):
				sku = str(row['sfs_upcnum_v'])
				inventory = int(row['sfuqoh_v'])
				try:
					pv = ProductVariation.objects.get(product__sku=sku)
					pv.product.items_in_stock = inventory
					pv.product.save()
					status_dict['update_results_messages'].append('Updated inventory for: '+ sku)
				except ObjectDoesNotExist or ProductVariation.MultipleObjectsReturned:
					status_dict['error_results_messages'].append('Invalid or redundant sku : '+ sku)
			
			filepath = os.path.join(IMPORT_TEMPFILE_LOCATION, save_file_name)
			if os.path.isfile(filepath):
				os.remove(filepath)
			
			return _render_results_response(request, status_dict, extra_context)
	else:
		form = UploadImportFileForm()
	if extra_context is None:
		extra_context = {}

	context = RequestContext(request)
	for key, value in extra_context.items():
		context[key] = callable(value) and value() or value
		
	return render_to_response(IMPORT_UPLOAD_TEMPLATE, {'form': form}, context_instance=context)
	

def _render_results_response(request, status_dict, extra_context):
	"""
	Laziness function. I got tired of typing this every time... 
	
	""" 
	if extra_context is None:
		extra_context = {}

	context = RequestContext(request)
	for key, value in extra_context.items():
		context[key] = callable(value) and value() or value

	return render_to_response(IMPORT_RESULTS_TEMPLATE, status_dict, context_instance=context)