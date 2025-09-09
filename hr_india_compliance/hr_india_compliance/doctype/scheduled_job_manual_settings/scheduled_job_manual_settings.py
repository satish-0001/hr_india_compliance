# Copyright (c) 2024, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ScheduledJobManualSettings(Document):

	@frappe.whitelist()
	def get_function_names(self,module_path):
		module = frappe.get_module(module_path)
		function_names = [fn for fn in dir(module) if callable(getattr(module, fn)) and getattr(module, fn).__module__ == module_path and fn.startswith('run_')]
		return function_names


