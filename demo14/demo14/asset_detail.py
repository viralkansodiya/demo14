import frappe
from frappe.utils import now

@frappe.whitelist(allow_guest=True)
def get_total_asset():
    data = frappe.request.json
    custodian = data.get("custodian")
    location = data.get("location")

    if not custodian:
        frappe.response["message"]={
            "succes_key":0,
            "error_msg":"custodian ID Missing"
        }
        return

    if not location:
        frappe.response["message"]={
            "succes_key":0,
            "error_msg":"arg location missing"
        }
        return

    serial_no = frappe.db.sql(f"""
            Select r.rfid_tagging_id , r.custodian, r.name, r.serial_number, r.description
            From `tabRFID Record` as r
            Where custodian = '{custodian}' and r.location = '{location}'
    """,as_dict=1)

    total_asset = len(serial_no)
    final_data = {}
    rfid =[]
    
    for row in serial_no:
        rfid.append(row.rfid_tagging_id)

    final_data.update({"total" : total_asset})
    final_data.update({"rfid_list" : rfid })

    frappe.response["message"]={
        "succes_key":1,
        "data":final_data
    }

    return


@frappe.whitelist(allow_guest=True)
def get_asset_details():
    data = frappe.request.json
    custodian = data.get("custodian")
    location = data.get("location")
    rfid_list = data.get("rfid_list")

    if not custodian:
        frappe.response["message"]={
            "succes_key":0,
            "error_msg":"Custodian ID Missing"
        }
        return
    
    current_time = now()

    if not location:
        frappe.response["message"]={
            "succes_key":0,
            "error_msg":"arg location missing"
        }
        return 

    rfid_data = frappe.db.get_list('RFID Record',
                filters={
                    'custodian' : custodian ,
                    'location' : location
                },
                fields=["name", "sage_asset_id", "rfid_tagging_id", "rfid_tagging_id_asci", "location", "custodian", 'last_scanned_time', 'last_scanned_by', 'is_scanned'],
                ignore_permissions = 1
            )

    total_asset = len(rfid_data)
    final_data = {}
    final_data.update({"total" : total_asset})

    found_map = {}
    all_rfid = []
    not_found = []
    found = []
    extra = []

    for row in rfid_data:
        if row.is_scanned:
            found.append(row.get('rfid_tagging_id'))
            all_rfid.append(row.get('rfid_tagging_id'))
            continue
        found_map[row.get('rfid_tagging_id')] = row
        all_rfid.append(row.get('rfid_tagging_id'))
        if row.get('rfid_tagging_id').upper() not in rfid_list:
            not_found.append(row.get('rfid_tagging_id'))
    
    

    for row in rfid_list:
        if row.lower() in all_rfid:
            found.append(row.lower())
        else:
            extra.append(row.lower())

    for row in found:
        if row:
            rfid_doc = frappe.db.get_value("RFID Record", {"rfid_tagging_id": row.lower()}, "name")
            if not frappe.db.get_value("RFID Record", rfid_doc, "last_scanned_time"):
                frappe.db.set_value("RFID Record", rfid_doc, "last_scanned_by", custodian)
                frappe.db.set_value("RFID Record", rfid_doc, "last_scanned_time", current_time)
                frappe.db.set_value("RFID Record", rfid_doc, "is_scanned", 1)
                frappe.db.commit()
    #         new_found.append(row)
    #     elif row not in new_not_found:
    #         new_not_found.append(row)
            
    #     for row in not_found:
    #         rfid_doc = frappe.db.get_value("RFID Record", {"rfid_tagging_id": row}, "name")
    #         last_scanned_time = frappe.db.get_value("RFID Record", rfid_doc, "last_scanned_time")
    #         if last_scanned_time:
    #             if row not in new_found:
    #                 new_found.append(row)
    #         else:
    #             if row not in new_not_found:
    #                 new_not_found.append(row)
        
        
    final_data.update({"total_found" : len(list(set(found)))})
    final_data.update({"rfid_found" : list(set(found))})
    final_data.update({"total_not_found":len(not_found)})
    final_data.update({"rfid_not_found" : not_found})
    final_data.update({"total_extra":len(extra)})
    final_data.update({"extra_rfid" : extra})
    
    frappe.response["message"]={
        "succes_key":1,
        "data":final_data
    }

    return


import random
import string


@frappe.whitelist(allow_guest=True)
def get_location_list():
    frappe.session.user = "Administrator"
    warehouse_list =  frappe.db.get_list("Asset Location", fields=["location"], pluck="location")
    frappe.response["message"]={
        "succes_key":1,
        "data":warehouse_list
    }


def generate_unique_code(length=10):
    # Generates a random alphanumeric code
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_multiple_unique_codes(count=20, length=10):
    # Generates a set of unique codes to ensure no duplicates
    codes = set()
    while len(codes) < count:
        code = generate_unique_code(length)
        codes.add(code)
    return list(codes)

# Generate 20 unique 10-character codes
def get_unic_number():
    doc_list = frappe.db.get_list("Serial No", pluck="name")
    unique_codes = generate_multiple_unique_codes()
    for idx, code in enumerate(unique_codes):
        frappe.db.set_value("Serial No", doc_list[idx], "custom_rfid_asset_tag", code)


@frappe.whitelist(allow_guest=True)
def get_rfid_info():
    data = frappe.request.json
    rfid = data.get("rfid")
    conditions = " and rfid_tagging_id in {} ".format(
                "(" + ", ".join([f'"{l}"' for l in rfid]) + ")")
    if not rfid:
        frappe.response["message"]={
            "succes_key":0,
            "error_msg":"RFID parameters missing"
        }
        return

    data = frappe.db.sql(f"""
        Select sage_asset_id, rfid_tagging_id, rfid_tagging_id_asci, serial_number , description, category, location,new_location, custodian, purchase_date, extended_description, specific_location, new_serial_number, 
        taggable , status, save_time, last_scanned_by, last_scanned_time, submit_time, remark_for_found_asset,  remark_other, remark_for_not_found_asset, remark_for_extra_asset , new_remark
        From `tabRFID Record` 
        Where 1=1 {conditions}
    """,as_dict=1)

    frappe.response["message"]={
            "succes_key":1,
            "data":data
        }
    return


@frappe.whitelist(allow_guest=True)
def save_after_scanning():
    """
        { 
            "data" : {
                    "rfid" :"....",
                    "serial_no" : "......serial_no.......",
                    "remark_for_found_asset" : ".......remark......",
                    "remark_for_not_found_asset" : ".......remark_for_not_found_asset......",
                    "remark_for_extra_asset" : "..........remark_for_extra_asset....."
                    "remark_other" : ".....remark_other......",
                }
        }
        
    """

    data = frappe.request.json
    data = data.get('data')
    try:
        for row in data:
            if not row.get('rfid'):
                frappe.response["message"]={
                "succes_key":0,
                "error_message": "RFID parameter is missing"
                }
                return 
            if not row.get("serial_no"):
                frappe.response["message"]={
                "succes_key":0,
                "error_message": "Serial No parameter is missing"
                }
                return 
            if name := frappe.db.exists("RFID Record", {"serial_number" : row.get("serial_no"), "rfid_tagging_id": row.get("rfid")}):
                doc = frappe.get_doc("RFID Record", name)
                if not doc.submit_time:
                    if row.get("remark_for_found_asset"):
                        doc.remark_for_found_asset = row.get("remark_for_found_asset")
                    if row.get("remark_for_not_found_asset"):
                        doc.remark_for_not_found_asset = row.get("remark_for_not_found_asset")
                    if row.get("remark_for_extra_asset"):
                        doc.remark_for_extra_asset = row.get("remark_for_extra_asset")
                    if row.get("remark_other"):
                        doc.remark_other = row.get("remark_other")

                    doc.save_time = now()

                    doc.save(ignore_permissions = True)
                    frappe.db.commit()
                    frappe.response["message"]={
                        "succes_key":1,
                        "success_message": "Successfully Updated"
                        }
                else:
                    frappe.response["message"]={
                        "succes_key":0,
                        "success_message": f"RFID {doc.name} is already submitted" 
                        }
    except Exception as e:
        frappe.response["message"]={
            "succes_key":0,
            "error_message": e
            }
    
    
        
@frappe.whitelist(allow_guest=True)
def submit_after_scanning():
    """
        args = [
            {
                "rfid" :"....",
                "serial_no" : "......serial_no.......",
                "remark_for_found_asset" : ".......remark......",
                "remark_for_not_found_asset" : ".......remark_for_not_found_asset......",
                "remark_for_extra_asset" : "..........remark_for_extra_asset....."
            "remark_other" : ".....remark_other......",
            }
        ]
    """

    data = frappe.request.json
    data = data.get('data')
    try:
        for row in data:
            if not row.get('rfid'):
                frappe.response["message"]={
                "succes_key":1,
                "success_message": "RFID parameter is missing"
                }
                return 
            if not row.get("serial_no"):
                frappe.response["message"]={
                "succes_key":1,
                "success_message": "Serial No parameter is missing"
                }
                return 
            if name := frappe.db.exists("RFID Record", {"serial_number" : row.get("serial_no"), "rfid_tagging_id": row.get("rfid")}):
                doc = frappe.get_doc("RFID Record", name)
                if not doc.submit_time:
                    if row.get("remark_for_found_asset"):
                        doc.remark_for_found_asset = row.get("remark_for_found_asset")
                    if row.get("remark_for_not_found_asset"):
                        doc.remark_for_not_found_asset = row.get("remark_for_not_found_asset")
                    if row.get("remark_for_extra_asset"):
                        doc.remark_for_extra_asset = row.get("remark_for_extra_asset")
                    if row.get("remark_other"):
                        doc.remark_other = row.get("remark_other")

                    doc.submit_time = now()

                    doc.save(ignore_permissions = True)
                    frappe.db.commit()
                    frappe.response["message"]={
                        "succes_key":1,
                        "success_message": "Successfully Updated"
                        }
                else: 
                    frappe.response["message"]={
                        "succes_key":0,
                        "success_message": f"RFID {doc.name} is already submitted" 
                        }
    except Exception as e:
        frappe.response["message"]={
            "succes_key":0,
            "error_message": e
            }

    
    
    

    
 


@frappe.whitelist(allow_guest=True)
def fetch_all_reason():
    frappe.session.user = "Administrator"
    data = frappe.db.get_list("Reason", pluck="name", order_by='creation ASC',)
    frappe.response["message"]={
            "succes_key":1,
            "success_message": data
        }
    return 

@frappe.whitelist(allow_guest=True)
def replace_asset_rfid_code():
    data = frappe.request.json
    rfid = data.get('rfid')
    serial_no = data.get('serial_no')

    if not serial_no:
        frappe.response["message"]={
            "succes_key":0,
            "error_code": "serial no is missing"
        }
        return

    if rfid_record := frappe.db.exists("RFID Record", {"serial_number" : serial_no}):
        name = frappe.db.get_value("RFID Record", {"rfid_tagging_id" : rfid}, "name")

        old_asset = frappe.get_doc("RFID Record", name)
        old_asset.rfid_tagging_id = ''
        old_asset.rfid_tagging_id_asci = ''
        old_asset.save(ignore_permissions=True)

        doc = frappe.get_doc("RFID Record", rfid_record)
        doc.rfid_tagging_id = rfid
        doc.rfid_tagging_id_asci = get_asci_code(rfid)
        doc.save(ignore_permissions = True)  
        frappe.db.commit()
        frappe.response["message"]={
            "succes_key":1,
            "success_message": "RFID Successfully Transfer to Asset Record {0}".format(doc.name)
        }
        return
    else:
        frappe.response["message"]={
            "succes_key":0,
            "error_code": "This serial No not available in ERP system"
        }
        return


@frappe.whitelist(allow_guest=True)
def update_items():
    data = frappe.request.json
    rfid = data.get('rfid')
    if not rfid:
        frappe.response["message"]={
            "succes_key":0,
            "error_code": "Parameter rfid is missing"
        } 
        return

    serial_no = data.get("serial_no")
    if not serial_no:
        frappe.response["message"]={
            "success_key":0,
            "error_code": "Parameter serial no is missing"
        }
        return

    if rfid := frappe.db.exists("RFID Record", {"rfid_tagging_id":rfid}):
        doc = frappe.get_doc("RFID Record", rfid)
        if doc.serial_number != serial_no:
            doc.new_serial_number = serial_no
        
        if data.get("new_remark"):
            doc.new_remark = data.get("new_remark")
            
        if data.get("new_location"):
            if doc.location != data.get('new_location'):
                doc.new_location = data.get('new_location')

        if data.get("new_serial_no"):
            if doc.new_serial_number != data.get('new_serial_no'):
                doc.new_serial_number = data.get('new_serial_no')
        
        if data.get("remark_for_found_asset") and  data.get("remark_for_found_asset") != "":
            doc.remark_for_found_asset = data.get("remark_for_found_asset")

        if data.get("remark_for_not_found_asset") and  data.get("remark_for_not_found_asset") != "":
            doc.remark_for_not_found_asset = data.get("remark_for_not_found_asset")

        if data.get("remark_for_extra_asset") and  data.get("remark_for_extra_asset") != "":
            doc.remark_for_extra_asset = data.get("remark_for_extra_asset")

        doc.save(ignore_permissions = True)
        frappe.db.commit()
        frappe.response["message"]={
            "success_key":1,
            "error_code": "Serial No and remark is updated in database successfully"
        }


    
    
def get_asci_code(hex_string):
    ascii_string = bytes.fromhex(hex_string).decode('utf-8')
    return ascii_string