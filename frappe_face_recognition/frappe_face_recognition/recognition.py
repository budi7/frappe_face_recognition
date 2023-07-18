import face_recognition
import tempfile
import os
import base64
import sys
from frappe import _
import frappe
import json
import datetime

def register(image, primary_id, secondary_id, person_name):
    # Step 1: Save the image inside the directory
    public_files_dir = os.path.join(frappe.local.site_path, 'public', 'files')
    new_folder_name = 'frappe_face_recognition'
    new_folder_path = os.path.join(public_files_dir, new_folder_name)

    # Save the image with the primary_id as the filename
    image_data = base64.b64decode(image)
    image_filename = primary_id + '.jpg'
    image_path = os.path.join(new_folder_path, image_filename)

    try:
        with open(image_path, 'wb') as file:
            file.write(image_data)
    except Exception as e:
        return {'status': 'error', 'message': 'Failed to save the image: {0}'.format(image_filename)}
        # return {'status': 'error', 'message': str(e)}

    # Step 2: Map parameters to the Person doctype
    person = frappe.new_doc('Person')
    person.primary_id = primary_id
    person.enabled = True
    person.secondary_id = secondary_id
    person.person_name = person_name

    # Step 3: Extract face features from the image
    try:
        image_data = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image_data)

        face_detected = len(face_encodings)
        if  face_detected > 0:
            face_encoding_array = face_encodings[0]
            face_encoding_list = face_encoding_array.tolist()
            person.person_feature = json.dumps(face_encoding_list)
        else:
            return {'status': 'error', 'message': 'No face detected in the image'}
    except Exception as e:
        # return {'status': 'error', 'message': 'Failed to extract face features'}
        os.remove(image_path)
        return {'status': 'error', 'message': str(e)}

    # Step 4: Insert the field person_photo_path with the image path
    person.person_photo_path = '/files/frappe_face_recognition/' + image_filename

    # Step 5: Save the document
    try:
        person.insert(ignore_permissions=True)
    except Exception as e:
        # return {'status': 'error', 'message': 'Failed to create the Person document'}
        os.remove(image_path)
        return {'status': 'error', 'message': str(e)}

    # Step 6: Update the cached data
    update_cached_data(face_encodings[0], person.primary_id, person.person_name)

    return {'status': 'success', 'message': 'Person document created successfully'}

def recognize(photo):
    # Step 1: Load all face feature data from the Person doctype using the cache
    face_encodings = get_cached_face_encodings()
    person_names = get_cached_person_names()

    # Step 2: Save the photo to a temporary file
    encoded_photo = base64.b64decode(photo)
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        temp_filename = temp_file.name
        temp_file.write(encoded_photo)

    # Step 3: Load the saved photo into the face recognition module
    unknown_image = face_recognition.load_image_file(temp_filename)

    # Step 4: Perform face recognition using the loaded photo and face feature data
    unknown_face_encodings = face_recognition.face_encodings(unknown_image)

    # Step 5: Handle face recognition results
    face_detected = len(unknown_face_encodings)
    if face_detected < 1:
        return {'status': 'error', 'message': 'No face detected in the photo'}

    face_distances = face_recognition.face_distance(face_encodings, unknown_face_encodings[0])
    min_distance = min(face_distances)
    min_distance_index = face_distances.argmin()
    
    if min_distance <= 0.6:
        recognized_person = list(person_names.keys())[min_distance_index]
        save_known_photo(encoded_photo, recognized_person)
        return {'status': 'success', 'data': {'primary_id': recognized_person, 'person_name': person_names[recognized_person]}}
    else:
        save_unknown_photo(encoded_photo)
        return {'status': 'error', 'message': 'Identity not recognized'}


def verify(primary_id, secondary_id):
    # Step 1: Check if primary_id and secondary_id belong to the same person in the Person doctype
    person = frappe.get_all('Person', filters={'primary_id': primary_id, 'secondary_id': secondary_id})
    if person:
        person = frappe.get_doc('Person', person[0].name)
        return {'status': 'success', 'data': {'primary_id': person.primary_id, 'person_name': person.person_name}}
    else:
        return {'status': 'error', 'message': 'Not recognized'}

def reset_cached_face_encodings():
    frappe.cache().set_value('person_names', None)
    frappe.cache().set_value('face_encodings', None)

def get_cached_face_encodings():
    cache_key = 'face_encodings'
    face_encodings = frappe.cache().get_value(cache_key)
    if face_encodings is None:
        face_encodings = load_face_encodings_from_db()
        frappe.cache().set_value(cache_key, face_encodings)
    return face_encodings

def get_cached_person_names():
    cache_key = 'person_names'
    person_names = frappe.cache().get_value(cache_key)
    if person_names is None:
        person_names = load_person_names_from_db()
        frappe.cache().set_value(cache_key, person_names)
    return person_names

def load_face_encodings_from_db():
    query = """
        SELECT name, person_feature FROM `tabPerson`
    """
    results = frappe.db.sql(query, as_dict=True)
    
    face_encodings = []
    for result in results:
        person_feature = result['person_feature']
        face_encoding = json.loads(person_feature)
        face_encodings.append(face_encoding)
        
    return face_encodings

def load_person_names_from_db():
    query = """
        SELECT name, person_name FROM `tabPerson`
    """
    results = frappe.db.sql(query, as_dict=True)
    return {result['name']: result['person_name'] for result in results}

def update_cached_data(face_encoding, primary_id, person_name):
    cache_key = 'face_encodings'
    cached_face_encodings = frappe.cache().get_value(cache_key)
    if cached_face_encodings is None:
        cached_face_encodings = []
    cached_face_encodings.append(face_encoding)
    frappe.cache().set_value(cache_key, cached_face_encodings)

    cache_key = 'person_names'
    cached_person_names = frappe.cache().get_value(cache_key)
    if cached_person_names is None:
        cached_person_names = {}
    cached_person_names[primary_id] = person_name
    frappe.cache().set_value(cache_key, cached_person_names)

def save_known_photo(image_data, person_id):
    public_files_dir = os.path.join(frappe.local.site_path, 'public', 'files')
    known_folder_path = os.path.join(public_files_dir, 'frappe_face_recognition')
    known_folder_path = os.path.join(known_folder_path, 'known')

    # Generate the timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")

    image_filename = f"{timestamp}_{person_id}.jpg"
    image_path = os.path.join(known_folder_path, image_filename)

    try:
        if not os.path.exists(known_folder_path):
            os.makedirs(known_folder_path)
        with open(image_path, 'wb') as file:
            file.write(image_data)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def save_unknown_photo(image_data):
    public_files_dir = os.path.join(frappe.local.site_path, 'public', 'files')
    unknown_folder_path = os.path.join(public_files_dir, 'frappe_face_recognition')
    unknown_folder_path = os.path.join(unknown_folder_path, 'unknown')

    # Generate the timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")

    image_filename = f"{timestamp}_{person_id}.jpg"
    image_path = os.path.join(unknown_folder_path, image_filename)

    try:
        if not os.path.exists(unknown_folder_path):
            os.makedirs(unknown_folder_path)
        with open(image_path, 'wb') as file:
            file.write(image_data)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

    
def is_valid_image(image_data):
    # Check if the image data is a valid image format
    # Perform your own validation logic here
    # For example, you can use a library like Pillow to validate the image format
    try:
        from PIL import Image
        Image.open(image_data)
        return True
    except Exception:
        return False


def testImage(path): 
    # check image is valid
    pass


# todo 
# error log library 
