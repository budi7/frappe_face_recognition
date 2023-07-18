import frappe

def writeLog(user_id, user_name, dateTime, org_id, license_code):
    attendance = frappe.new_doc("Attendance")
    attendance.user_id = user_id
    attendance.user_name = user_name
    attendance.date_time = dateTime
    attendance.org_id = org_id
    attendance.license_code = license_code
    attendance.insert(ignore_permissions=True)

    return {'status': 'success', 'message': 'Attendance saved successfully'}