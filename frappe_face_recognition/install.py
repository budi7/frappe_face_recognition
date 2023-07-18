import os
from frappe import _
import frappe

def after_install():
    public_files_dir = os.path.join(frappe.local.site_path, 'public', 'files')
    new_folder_name = 'frappe_face_recognition'

    new_folder_path = os.path.join(public_files_dir, new_folder_name)

    if not os.path.exists(new_folder_path):
        try:
            os.makedirs(new_folder_path)
            frappe.msgprint(_('Created folder: {0}').format(new_folder_name))
        except OSError as e:
            frappe.msgprint(_('Failed to create folder: {0}').format(new_folder_name))
            frappe.log_error(_('Failed to create folder: {0}').format(new_folder_name), title='Folder Creation Failed', exc=e)
    else:
        frappe.msgprint(_('Folder already exists: {0}').format(new_folder_name))


def after_uninstall():
    pass