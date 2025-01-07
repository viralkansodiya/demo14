import frappe
from frappe.utils import now, flt

@frappe.whitelist(allow_guest=True)
def get_total_asset():
    data = frappe.request.json
    custodian = data.get("custodian")
    location = data.get("location")

    if not custodian:
        frappe.response["message"]={
            "success_key":0,
            "error_msg":"custodian ID Missing"
        }
        return

    if not location:
        frappe.response["message"]={
            "success_key":0,
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
        "success_key":1,
        "data":final_data
    }

    return

@frappe.whitelist(allow_guest=True)
def on_change_of_location_get_asset_details():
    data = frappe.request.json
    custodian = data.get("custodian")
    location = data.get("location")
    rfid_list = [ row.upper() for row in data.get("rfid_list") ]

    if not custodian:
        frappe.response["message"]={
            "success_key":0,
            "error_msg":"Custodian ID Missing"
        }
        return

    current_time = now()

    if not location:
        frappe.response["message"]={
            "success_key":0,
            "error_msg":"arg location missing"
        }
        return 

    rfid_data = frappe.db.get_list('RFID Record',
                filters={
                    'custodian' : custodian ,
                    'location' : location
                },
                fields=["name", "sage_asset_id", "rfid_tagging_id", "rfid_tagging_id_asci", "location", "custodian", 'last_scanned_time', 'last_scanned_by', 'is_scanned', "submit_time"],
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
            # found.append(row.get('rfid_tagging_id'))
            all_rfid.append(row.get('rfid_tagging_id').upper())
            continue
        found_map[row.get('rfid_tagging_id')] = row
        all_rfid.append(row.get('rfid_tagging_id').upper())
        # if row.get('rfid_tagging_id') not in rfid_list:
        #     not_found.append(row.get('rfid_tagging_id'))

    for row in rfid_list:
        if row.upper() in all_rfid:
            continue
        # else:
        #     extra.append(row.upper())
        
    final_data.update({"total_found" : len(list(set(found)))})
    final_data.update({"rfid_found" : list(set(found))})
    final_data.update({"total_not_found":len(not_found)})
    final_data.update({"rfid_not_found" : not_found})
    final_data.update({"total_extra":len(extra)})
    final_data.update({"extra_rfid" : extra})
    
    frappe.response["message"]={
        "success_key":1,
        "data":final_data
    }

    return


@frappe.whitelist(allow_guest=True)
def get_asset_details():
    data = frappe.request.json
    custodian = data.get("custodian")
    location = data.get("location")
    rfid_list = [ row.upper() for row in data.get("rfid_list") ]
    is_scanned = bool(data.get("is_scanned"))

    if not custodian:
        frappe.response["message"]={
            "success_key":0,
            "error_msg":"Custodian ID Missing"
        }
        return
    
    current_time = now()

    if not location:
        frappe.response["message"]={
            "success_key":0,
            "error_msg":"arg location missing"
        }
        return 

    rfid_data = frappe.db.get_list('RFID Record',
                filters={
                    'custodian' : custodian,
                    'location' : location
                },
                fields=["name", "sage_asset_id", "rfid_tagging_id", "rfid_tagging_id_asci", "location", "custodian", 'last_scanned_time', 'last_scanned_by', 'is_scanned', "submit_time"],
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
        if row.upper() in all_rfid:
            found.append(row.upper())
        else:
            extra.append(row.upper())
    final_not_found = []
    if is_scanned:
        for row in found:
            if row:
                rfid_doc = frappe.db.get_value("RFID Record", {"rfid_tagging_id": row.upper()}, "name")
                last_scanned_time = frappe.db.get_value("RFID Record", rfid_doc, "last_scanned_time")
                submit_time = frappe.db.get_value("RFID Record", rfid_doc, "submit_time")
                if not last_scanned_time and not submit_time:
                    frappe.db.set_value("RFID Record", rfid_doc, "last_scanned_by", custodian)
                    frappe.db.set_value("RFID Record", rfid_doc, "last_scanned_time", current_time)
                    frappe.db.set_value("RFID Record", rfid_doc, "is_scanned", 1)
                    frappe.db.commit()      
    

    
    final_found = []
    for row in found:
        if row:
            rfid_doc = frappe.db.get_value("RFID Record", {"rfid_tagging_id": row.upper()}, "name")
            last_scanned_time = frappe.db.get_value("RFID Record", rfid_doc, "last_scanned_time")
            submit_time = frappe.db.get_value("RFID Record", rfid_doc, "submit_time")
            if last_scanned_time:
                final_found.append(row.upper())
            if not last_scanned_time and submit_time:
                final_not_found.append(row.upper())
    
    
    for row in not_found:
        if row:
            rfid_doc = frappe.db.get_value("RFID Record", {"rfid_tagging_id": row.upper()}, "name")
            if frappe.db.get_value("RFID Record", rfid_doc, "submit_time"):
                final_not_found.append(row.upper())
                continue
            if not frappe.db.get_value("RFID Record", rfid_doc, "last_scanned_time"):
                final_not_found.append(row.upper())

    
    final_data.update({"total_found" : len(list(set(final_found)))})
    final_data.update({"rfid_found" : list(set(final_found))})
    final_data.update({"total_not_found":len(final_not_found)})
    final_data.update({"rfid_not_found" : final_not_found})
    final_data.update({"total_extra":len(extra)})
    final_data.update({"extra_rfid" : extra})
    
    frappe.response["message"]={
        "success_key":1,
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
        "success_key":1,
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
    rfid = [row.upper() for row in data.get("rfid")]
    conditions = " and rfid_tagging_id in {} ".format(
                "(" + ", ".join([f'"{l.upper()}"' for l in rfid]) + ")")

    if not rfid:
        frappe.response["message"]={
            "success_key":0,
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
            "success_key":1,
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
                "success_key":0,
                "error_message": "RFID parameter is missing"
                }
                return 
            if not row.get("serial_no"):
                frappe.response["message"]={
                "success_key":0,
                "error_message": "Serial No parameter is missing"
                }
                return 
            if name := frappe.db.exists("RFID Record", {"serial_number" : row.get("serial_no"), "rfid_tagging_id": row.get("rfid").upper()}):
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
                        "success_key":1,
                        "success_message": "Successfully Updated"
                        }
                else:
                    frappe.throw(f"RFID {doc.name} is already submitted" )
                    frappe.response["message"]={
                        "success_key":0,
                        "success_message": f"RFID {doc.name} is already submitted" 
                        }
    except Exception as e:
        frappe.response["message"]={
            "success_key":0,
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
                "success_key":1,
                "success_message": "RFID parameter is missing"
                }
                return 
            if not row.get("serial_no"):
                frappe.response["message"]={
                "success_key":1,
                "success_message": "Serial No parameter is missing"
                }
                return 
            if name := frappe.db.exists("RFID Record", {"serial_number" : row.get("serial_no"), "rfid_tagging_id": row.get("rfid").upper()}):
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
                        "success_key":1,
                        "success_message": "Successfully Updated"
                        }
                else:
                    frappe.throw(f"RFID {doc.name} is already submitted" )
                    frappe.response["message"]={
                        "success_key":0,
                        "success_message": f"RFID {doc.name} is already submitted" 
                        }
        
    except Exception as e:
        frappe.response["message"]={
            "success_key":0,
            "error_message": e
            }



@frappe.whitelist(allow_guest=True)
def fetch_all_reason():
    frappe.session.user = "Administrator"
    data = frappe.db.get_list("Reason", pluck="name", order_by='creation ASC',)
    frappe.response["message"]={
            "success_key":1,
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
            "success_key":0,
            "error_code": "serial no is missing"
        }
        return

    if rfid_record := frappe.db.exists("RFID Record", {"serial_number" : serial_no}):
        name = frappe.db.get_value("RFID Record", {"rfid_tagging_id" : rfid.upper()}, "name")

        old_asset = frappe.get_doc("RFID Record", name)
        old_asset.rfid_tagging_id = ''
        old_asset.rfid_tagging_id_asci = ''
        old_asset.save(ignore_permissions=True)

        doc = frappe.get_doc("RFID Record", rfid_record)
        doc.rfid_tagging_id = rfid.upper()
        doc.rfid_tagging_id_asci = get_asci_code(rfid.upper())
        doc.save(ignore_permissions = True)  
        frappe.db.commit()
        frappe.response["message"]={
            "success_key":1,
            "success_message": "RFID Successfully Transfer to Asset Record {0}".format(doc.name)
        }
        return
    else:
        frappe.response["message"]={
            "success_key":0,
            "error_code": "This serial No not available in ERP system"
        }
        return


@frappe.whitelist(allow_guest=True)
def update_items():
    data = frappe.request.json
    rfid = data.get('rfid')
    if not rfid:
        frappe.response["message"]={
            "success_key":0,
            "error_code": "Parameter rfid is missing"
        } 
        return

    serial_no = data.get("serial_no")

    if rfid := frappe.db.exists("RFID Record", {"rfid_tagging_id":rfid.upper()}):
        doc = frappe.get_doc("RFID Record", rfid)
        if doc.serial_number != serial_no:
            doc.new_serial_number = serial_no
    
        doc.new_remark = data.get("new_remark")
        # if doc.location != data.get('new_location'):
        doc.new_location = data.get('new_location')

        if doc.serial_number != data.get('new_serial_no'):
            doc.new_serial_number = data.get('new_serial_no')

        doc.remark_for_found_asset = data.get("remark_for_found_asset")

        doc.remark_for_not_found_asset = data.get("remark_for_not_found_asset")

        doc.remark_for_extra_asset = data.get("remark_for_extra_asset")
    
        doc.remark_other = data.get("remark_other")

        doc.save(ignore_permissions = True)
        frappe.db.commit()
        frappe.response["message"]={
            "success_key":1,
            "error_code": "Update has been completed"
        }
        return


    
    
def get_asci_code(hex_string):
    ascii_string = bytes.fromhex(hex_string).decode('utf-8')
    return ascii_string


@frappe.whitelist(allow_guest=True)
def update_multiple_rfid():
    data = frappe.request.json
    details = data.get('rfid_details')

    if not details:
        frappe.response["message"]={
            "success_key":0,
            "error_code": "rfid_details parameter is missing or rfid_details has empty list"
        }
        return
    meta = frappe.get_meta("RFID Record")
    fields = []
    for row in meta.fields:
        if row.fieldname not in ['sage_asset_id', 'rfid_tagging_id', 'rfid_tagging_id_asci']:
            fields.append(row.fieldname)
    updated_rfid_records = []
    unavailable_list = []
    submitted_list = []

    try:
        for row in details:
            if not row.get('rfid_tagging_id'):
                frappe.response["message"]={
                "success_key":0,
                "error_code": "'rfid' is missing (hexadecimal code)"
                }
                return

            if rfid := frappe.db.exists("RFID Record", {"rfid_tagging_id":row.get('rfid_tagging_id').upper()}):
                doc = frappe.get_doc("RFID Record", rfid)
                if not doc.submit_time:
                    for d in fields:
                        if d in ['new_serial_no']:
                            if row.get(d):
                                if doc.serial_no != row.get(d):
                                    doc.update({d : row.get(d)})
                        else:
                            if row.get(d):
                                doc.update({d : row.get(d)})
                    doc.save(ignore_permissions = True)
                    frappe.db.commit()
                    updated_rfid_records.append(row)
                submitted_list.append(row)
            else:
                unavailable_list.append(row)
        
        frappe.response["message"]={
                "success_key":1,
                "error_message": {'updated_rfid_records' : updated_rfid_records, 'unavailable_list_in_database' : unavailable_list, "submitted_list" : submitted_list}
                }
        return
    
    except Exception as e:
        frappe.log_error(e)
        frappe.response["message"]={
            "success_key":0,
            "error_message": e
            }

        
@frappe.whitelist(allow_guest=True)
def lock_all_document():
    
    data = frappe.request.json
    rfid_list = [ row.upper() for row in data.get("rfid_list") ]
    custodian = data.get("custodian")
    location = data.get("location")
    is_scanned = bool(data.get("is_scanned"))

    if not custodian:
        frappe.response["message"]={
            "success_key":0,
            "error_msg":"Custodian ID Missing"
        }
        return
    
    current_time = now()

    if not location:
        frappe.response["message"]={
            "success_key":0,
            "error_msg":"arg location missing"
        }
        return 

    rfid_data = frappe.db.get_list('RFID Record',
                filters={
                    'custodian' : custodian,
                    'location' : location
                },
                fields=["name", "sage_asset_id", "rfid_tagging_id", "rfid_tagging_id_asci", "location", "custodian", 'last_scanned_time', 'last_scanned_by', 'is_scanned', "submit_time"],
                ignore_permissions = 1
            )

    total_asset = len(rfid_data)
    final_data = {}
    final_data.update({"total" : total_asset})
    updated_record = []
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
        if row.upper() in all_rfid:
            found.append(row.upper())
        else:
            extra.append(row.upper())

    final_not_found = []

    final_found = []
    final_found = []
    for row in found:
        if row:
            rfid_doc = frappe.db.get_value("RFID Record", {"rfid_tagging_id": row.upper()}, "name")
            last_scanned_time = frappe.db.get_value("RFID Record", rfid_doc, "last_scanned_time")
            submit_time = frappe.db.get_value("RFID Record", rfid_doc, "submit_time")
            if last_scanned_time:
                final_found.append(row.upper())
                continue
            if not last_scanned_time and submit_time:
                final_not_found.append(row.upper())
                continue
            if not last_scanned_time and not submit_time:
                final_not_found.append(row.upper())
    
    
    for row in not_found:
        if row:
            rfid_doc = frappe.db.get_value("RFID Record", {"rfid_tagging_id": row.upper()}, "name")
            if frappe.db.get_value("RFID Record", rfid_doc, "submit_time"):
                final_not_found.append(row.upper())
                continue
            if not frappe.db.get_value("RFID Record", rfid_doc, "last_scanned_time"):
                final_not_found.append(row.upper())

    final_data.update({"total_found" : len(list(set(final_found)))})
    final_data.update({"rfid_found" : list(set(final_found))})
    final_data.update({"total_not_found":len(final_not_found)})
    final_data.update({"rfid_not_found" : final_not_found})
    final_data.update({"total_extra":len(extra)})
    final_data.update({"extra_rfid" : extra})
    
    flag = False
    no_remark_flag = False

    for row in final_data.get("rfid_not_found"):
        if name := frappe.db.exists("RFID Record", {"rfid_tagging_id" : row.upper()}):
            doc = frappe.get_doc("RFID Record", name)
            if doc.submit_time:
                flag = True
                break
            if not doc.remark_for_not_found_asset:
                no_remark_flag = True
                break
            doc.submit_time = now()
            doc.save(ignore_permissions = True)
            updated_record.append(row)
    if flag:
        frappe.response["message"]={
            "success_key" : 0,
            "error_message" : "Data has already been submitted. No resubmission allowed"
        }
        return
    if no_remark_flag:
        frappe.response["message"]={
            "success_key":0,
            "error_message": f"{row} doesn't have a New remark, Please Update"
        }
        return
    
    found_flag = False
    for row in final_data.get("rfid_found"):
        if name := frappe.db.exists("RFID Record", {"rfid_tagging_id" : row.upper()}):
            doc = frappe.get_doc("RFID Record", name)
            if doc.submit_time:
                found_flag = True
                break
            doc.submit_time = now()
            doc.save(ignore_permissions = True)
            updated_record.append(row)

    if found_flag:
        frappe.response["message"]={
            "success_key" : 0,
            "error_message" : "Data has already been submitted. No resubmission allowed"
        }
        return
    frappe.db.commit()

    frappe.response["message"]={
        "success_key":1,
        "error_message": f"Submitted successfully. {len(updated_record)} records locked"
    }
    return
