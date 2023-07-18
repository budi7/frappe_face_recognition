import frappe
from frappe_face_recognition.frappe_face_recognition import recognition

def responder(response):
    frappe.clear_messages()

    if response["status"] == 'error':
        frappe.local.response["message"] = {
            "success_key":0,
            "message": response["message"],
            "data": {}
        }
    else:
        frappe.local.response["message"] = {
            "success_key":1,
            "message": response["status"] if "status" in response else "Success",
            "data": response["data"] if "data" in response else {}
        }

@frappe.whitelist( allow_guest=True )
def registerDevice(sn = None, device = None):
    # assign sn to a device
    # validate sn been used or no
    responder()
    return

@frappe.whitelist( allow_guest=True )
def registerFace(image, primary_id, secondary_id, name):
    try:
        result = recognition.register(image, primary_id, secondary_id, name)
        responder(result)
    except Exception as e:
        responder({
            'status': 'error', 
            'message': str(e)
        })
    return

@frappe.whitelist(allow_guest=True )
def recognizeFace(image, device_id):
    try:
        result = recognition.recognize(image)
        responder(result)
    except Exception as e:
        responder({
            'status': 'error', 
            'message': str(e)
        })
    return

@frappe.whitelist(allow_guest=True )
def verifyFace(primary_id, secondary_id):
    try:
        result = recognition.verify(photo = image)
        responder(result)
    except Exception as e:
        responder({
            'status': 'error', 
            'message': str(e)
        })
    return