import frappe

def execute(filters=None):
    columns = [
        {"label": "DCS", "fieldname": "dcs", "fieldtype": "Link", "options": "Warehouse"},
        {"label": "ACK LITER", "fieldname": "ack_liter", "fieldtype": "Float", "width": 120},
        {"label": "ACK KG", "fieldname": "ack_kg", "fieldtype": "Float", "width": 120},
        {"label": "ACK FAT", "fieldname": "ack_fat", "fieldtype": "Float", "width": 120},
        {"label": "ACK SNF", "fieldname": "ack_snf", "fieldtype": "Float", "width": 120},
        {"label": "ACK KG FAT", "fieldname": "ack_kg_fat", "fieldtype": "Float", "width": 120},
        {"label": "ACK KG SNF", "fieldname": "ack_kg_snf", "fieldtype": "Float", "width": 120},
        {"label": "REC LITER", "fieldname": "rec_liter", "fieldtype": "Float", "width": 120},
        {"label": "REC KG", "fieldname": "rec_kg", "fieldtype": "Float", "width": 120},
        {"label": "REC FAT", "fieldname": "rec_fat", "fieldtype": "Float", "width": 120},
        {"label": "REC SNF", "fieldname": "rec_snf", "fieldtype": "Float", "width": 120},
        {"label": "REC KG FAT", "fieldname": "rec_kg_fat", "fieldtype": "Float", "width": 120},
        {"label": "REC KG SNF", "fieldname": "rec_kg_snf", "fieldtype": "Float", "width": 120},
        {"label": "DIFF LITER", "fieldname": "diff_liter", "fieldtype": "Float", "width": 120},
        {"label": "DIFF KG", "fieldname": "diff_kg", "fieldtype": "Float", "width": 120},
        {"label": "DIFF FAT", "fieldname": "diff_fat", "fieldtype": "Float", "width": 120},
        {"label": "DIFF SNF", "fieldname": "diff_snf", "fieldtype": "Float", "width": 120},
        {"label": "DIFF KG FAT", "fieldname": "diff_kg_fat", "fieldtype": "Float", "width": 120},
        {"label": "DIFF KG SNF", "fieldname": "diff_kg_snf", "fieldtype": "Float", "width": 120},
    ]
    
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    dcs_filter = filters.get('dcs')
    shift = filters.get('shift')

    # Ensure dcs_filter is a list
    if not isinstance(dcs_filter, list):
        dcs_filter = [dcs_filter] if dcs_filter else []

    # Filter condition for DCS and shift
    dcs_condition = " AND dcs_id IN ({})".format(', '.join(['%s'] * len(dcs_filter))) if dcs_filter else ""
    shift_condition = " AND shift = %s" if shift else ""

    tank_condition = " AND tio.dcs IN ({})".format(', '.join(['%s'] * len(dcs_filter))) if dcs_filter else ""
    tank_shift_condition = " AND tio.shift = %s" if shift else ""

    # Query to get milk entry data
    milk_entry_sql_query = """
        SELECT 
            dcs_id as dcs, 
            SUM(volume) as ack_liter,
            SUM(volume*1.03) as ack_kg,
            AVG(fat) as ack_fat, 
            AVG(snf) as ack_snf,
            SUM(fat_kg) as ack_kg_fat, 
            SUM(snf_kg) as ack_kg_snf
        FROM 
            `tabMilk Entry`
        WHERE 
            date BETWEEN %s AND %s
            AND docstatus = 1
            {dcs_condition}
            {shift_condition}
        GROUP BY 
            dcs_id
    """.format(dcs_condition=dcs_condition, shift_condition=shift_condition)
    
    milk_params = [from_date, to_date] + dcs_filter
    if shift:
        milk_params.append(shift)
    
    milk_data = frappe.db.sql(milk_entry_sql_query, tuple(milk_params), as_dict=True)
    
    # Query to get tanker data
    tank_sql_query = """
        SELECT 
            tio.dcs as dcs, 
            COALESCE(SUM(tid.quantity), 0) as rec_liter, 
            COALESCE(SUM(tid.quantity_kg), 0) as rec_kg, 
            COALESCE(AVG(tid.fat_), 0) as rec_fat, 
            COALESCE(AVG(tid.snf_), 0) as rec_snf,
            COALESCE(SUM((tid.quantity_kg * tid.fat_)/100), 0) as rec_kg_fat, 
            COALESCE(SUM((tid.quantity_kg * tid.snf_)/100), 0) as rec_kg_snf
        FROM
            `tabTanker Inward Outward` tio
        LEFT JOIN
            `tabTanker Inward Divison` tid ON tid.parent = tio.name
        WHERE 
            tio.date BETWEEN %s AND %s
            AND tio.docstatus = 1
            {tank_condition}
            {tank_shift_condition}
        GROUP BY 
            tio.dcs
    """.format(tank_condition=tank_condition, tank_shift_condition=tank_shift_condition)
    
    tank_params = [from_date, to_date] + dcs_filter
    if shift:
        tank_params.append(shift)
    
    tank_data = frappe.db.sql(tank_sql_query, tuple(tank_params), as_dict=True)
    
    milk_dict = {item['dcs']: item for item in milk_data}
    tank_dict = {item['dcs']: item for item in tank_data}
    
    result = []
    
    for dcs in set(milk_dict.keys()).union(tank_dict.keys()):
        milk_entry = milk_dict.get(dcs, {})
        tanker_entry = tank_dict.get(dcs, {})
        
        result.append({
            "dcs": dcs,
            "ack_liter": milk_entry.get('ack_liter', 0),
            "ack_kg": milk_entry.get('ack_kg', 0),
            "ack_fat": milk_entry.get('ack_fat', 0),
            "ack_snf": milk_entry.get('ack_snf', 0),
            "ack_kg_fat": milk_entry.get('ack_kg_fat', 0),
            "ack_kg_snf": milk_entry.get('ack_kg_snf', 0),
            "rec_liter": tanker_entry.get('rec_liter', 0),
            "rec_kg": tanker_entry.get('rec_kg', 0),
            "rec_fat": tanker_entry.get('rec_fat', 0),
            "rec_snf": tanker_entry.get('rec_snf', 0),
            "rec_kg_fat": tanker_entry.get('rec_kg_fat', 0),
            "rec_kg_snf": tanker_entry.get('rec_kg_snf', 0),
            "diff_liter": milk_entry.get('ack_liter', 0) - tanker_entry.get('rec_liter', 0),
            "diff_kg": milk_entry.get('ack_kg', 0) - tanker_entry.get('rec_kg', 0),
            "diff_fat": milk_entry.get('ack_fat', 0) - tanker_entry.get('rec_fat', 0),
            "diff_snf": milk_entry.get('ack_snf', 0) - tanker_entry.get('rec_snf', 0),
            "diff_kg_fat": milk_entry.get('ack_kg_fat', 0) - tanker_entry.get('rec_kg_fat', 0),
            "diff_kg_snf": milk_entry.get('ack_kg_snf', 0) - tanker_entry.get('rec_kg_snf', 0),
        })
    
    return columns, result


# import frappe

# def execute(filters=None):
#     columns = [
#         {"label": "DCS", "fieldname": "dcs", "fieldtype": "Link", "options": "Warehouse"},
#         {"label": "ACK LITER", "fieldname": "ack_liter", "fieldtype": "Float", "width": 120},
#         {"label": "ACK KG", "fieldname": "ack_kg", "fieldtype": "Float", "width": 120},
#         {"label": "ACK FAT", "fieldname": "ack_fat", "fieldtype": "Float", "width": 120},
#         {"label": "ACK SNF", "fieldname": "ack_snf", "fieldtype": "Float", "width": 120},
#         {"label": "ACK KG FAT", "fieldname": "ack_kg_fat", "fieldtype": "Float", "width": 120},
#         {"label": "ACK KG SNF", "fieldname": "ack_kg_snf", "fieldtype": "Float", "width": 120},
#         {"label": "REC LITER", "fieldname": "rec_liter", "fieldtype": "Float", "width": 120},
#         {"label": "REC KG", "fieldname": "rec_kg", "fieldtype": "Float", "width": 120},
#         {"label": "REC FAT", "fieldname": "rec_fat", "fieldtype": "Float", "width": 120},
#         {"label": "REC SNF", "fieldname": "rec_snf", "fieldtype": "Float", "width": 120},
#         {"label": "REC KG FAT", "fieldname": "rec_kg_fat", "fieldtype": "Float", "width": 120},
#         {"label": "REC KG SNF", "fieldname": "rec_kg_snf", "fieldtype": "Float", "width": 120},
#         {"label": "DIFF LITER", "fieldname": "diff_liter", "fieldtype": "Float", "width": 120},
#         {"label": "DIFF KG", "fieldname": "diff_kg", "fieldtype": "Float", "width": 120},
#         {"label": "DIFF FAT", "fieldname": "diff_fat", "fieldtype": "Float", "width": 120},
#         {"label": "DIFF SNF", "fieldname": "diff_snf", "fieldtype": "Float", "width": 120},
#         {"label": "DIFF KG FAT", "fieldname": "diff_kg_fat", "fieldtype": "Float", "width": 120},
#         {"label": "DIFF KG SNF", "fieldname": "diff_kg_snf", "fieldtype": "Float", "width": 120},
#     ]
    
#     from_date = filters.get('from_date')
#     to_date = filters.get('to_date')
#     from_shift = filters.get('from_shift')
#     to_shift = filters.get('to_shift')
#     dcs_filter = filters.get('dcs')

#     # Ensure dcs_filter is a list
#     if not isinstance(dcs_filter, list):
#         dcs_filter = [dcs_filter] if dcs_filter else []

#     # Filter conditions
#     dcs_condition = " AND dcs_id IN ({})".format(', '.join(['%s'] * len(dcs_filter))) if dcs_filter else ""
#     shift_condition = """
#         AND (
#             (date = %s AND shift = %s)
#             OR (date = %s AND shift = %s)
#             OR (date > %s AND date < %s)
#             OR (date BETWEEN %s AND %s)
#         )
#     """

#     tank_condition = " AND tio.dcs IN ({})".format(', '.join(['%s'] * len(dcs_filter))) if dcs_filter else ""
#     tank_shift_condition = """
#         AND (
#             (tio.date = %s AND tio.shift = %s)
#             OR (tio.date = %s AND tio.shift = %s)
#             OR (tio.date > %s AND tio.date < %s)
#             OR (tio.date BETWEEN %s AND %s)
#         )
#     """

#     # Query to get milk entry data
#     milk_entry_sql_query = """
#         SELECT 
#             dcs_id as dcs, 
#             SUM(volume) as ack_liter,
#             SUM(volume*1.03) as ack_kg,
#             AVG(fat) as ack_fat, 
#             AVG(snf) as ack_snf,
#             SUM(fat_kg) as ack_kg_fat, 
#             SUM(snf_kg) as ack_kg_snf
#         FROM 
#             `tabMilk Entry`
#         WHERE 
#             date BETWEEN %s AND %s AND

#             AND docstatus = 1
#             {dcs_condition}
#             {shift_condition}
#         GROUP BY 
#             dcs_id
#     """.format(dcs_condition=dcs_condition, shift_condition=shift_condition)
    
#     milk_params = [from_date, to_date, from_date, from_shift, to_date, to_shift, from_date, to_date, from_date, to_date] + dcs_filter
    
#     milk_data = frappe.db.sql(milk_entry_sql_query, tuple(milk_params), as_dict=True)
    
#     # Query to get tanker data
#     tank_sql_query = """
#         SELECT 
#             tio.dcs as dcs, 
#             COALESCE(SUM(tid.quantity), 0) as rec_liter, 
#             COALESCE(SUM(tid.quantity_kg), 0) as rec_kg, 
#             COALESCE(AVG(tid.fat_), 0) as rec_fat, 
#             COALESCE(AVG(tid.snf_), 0) as rec_snf,
#             COALESCE(SUM((tid.quantity_kg * tid.fat_)/100), 0) as rec_kg_fat, 
#             COALESCE(SUM((tid.quantity_kg * tid.snf_)/100), 0) as rec_kg_snf
#         FROM
#             `tabTanker Inward Outward` tio
#         LEFT JOIN
#             `tabTanker Inward Divison` tid ON tid.parent = tio.name
#         WHERE 
#             tio.date BETWEEN %s AND %s
#             AND tio.docstatus = 1
#             {tank_condition}
#             {tank_shift_condition}
#         GROUP BY 
#             tio.dcs
#     """.format(tank_condition=tank_condition, tank_shift_condition=tank_shift_condition)
    
#     tank_params = [from_date, to_date, from_date, from_shift, to_date, to_shift, from_date, to_date, from_date, to_date] + dcs_filter
    
#     tank_data = frappe.db.sql(tank_sql_query, tuple(tank_params), as_dict=True)
    
#     # Merge the results based on dcs
#     milk_dict = {item['dcs']: item for item in milk_data}
#     tank_dict = {item['dcs']: item for item in tank_data}
    
#     result = []
    
#     for dcs in set(milk_dict.keys()).union(tank_dict.keys()):
#         milk_entry = milk_dict.get(dcs, {})
#         tanker_entry = tank_dict.get(dcs, {})
        
#         result.append({
#             "dcs": dcs,
#             "ack_liter": milk_entry.get('ack_liter', 0),
#             "ack_kg": milk_entry.get('ack_kg', 0),
#             "ack_fat": milk_entry.get('ack_fat', 0),
#             "ack_snf": milk_entry.get('ack_snf', 0),
#             "ack_kg_fat": milk_entry.get('ack_kg_fat', 0),
#             "ack_kg_snf": milk_entry.get('ack_kg_snf', 0),
#             "rec_liter": tanker_entry.get('rec_liter', 0),
#             "rec_kg": tanker_entry.get('rec_kg', 0),
#             "rec_fat": tanker_entry.get('rec_fat', 0),
#             "rec_snf": tanker_entry.get('rec_snf', 0),
#             "rec_kg_fat": tanker_entry.get('rec_kg_fat', 0),
#             "rec_kg_snf": tanker_entry.get('rec_kg_snf', 0),
#             "diff_liter": milk_entry.get('ack_liter', 0) - tanker_entry.get('rec_liter', 0),
#             "diff_kg": milk_entry.get('ack_kg', 0) - tanker_entry.get('rec_kg', 0),
#             "diff_fat": milk_entry.get('ack_fat', 0) - tanker_entry.get('rec_fat', 0),
#             "diff_snf": milk_entry.get('ack_snf', 0) - tanker_entry.get('rec_snf', 0),
#             "diff_kg_fat": milk_entry.get('ack_kg_fat', 0) - tanker_entry.get('rec_kg_fat', 0),
#             "diff_kg_snf": milk_entry.get('ack_kg_snf', 0) - tanker_entry.get('rec_kg_snf', 0),
#         })
    
#     return columns, result




# import frappe

# def execute(filters=None):
#     columns = [
#         {"label": "ACK/REC/DIFF", "fieldname": "ack", "fieldtype": "Data"},
#         {"label": "DCS Name", "fieldname": "dcs", "fieldtype": "Link", "options": "Warehouse"},
#         {"label": "LITRE", "fieldname": "liter", "fieldtype": "Float", "width": 120},
#         {"label": "KG", "fieldname": "kg", "fieldtype": "Float", "width": 120},
#         {"label": "FAT", "fieldname": "fat", "fieldtype": "Float", "width": 120},
#         {"label": "SNF", "fieldname": "snf", "fieldtype": "Float", "width": 120},
#         {"label": "KG FAT", "fieldname": "kg_fat", "fieldtype": "Float", "width": 120},
#         {"label": "KG SNF", "fieldname": "kg_snf", "fieldtype": "Float", "width": 120},
#     ]
    
#     from_date = filters.get('from_date')
#     to_date = filters.get('to_date')
#     dcs_filter = filters.get('dcs')
#     shift = filters.get('shift')

#     # Filter condition for DCS and shift
#     dcs_condition = " AND dcs_id IN (%s)" % ', '.join(['%s'] * len(dcs_filter)) if dcs_filter else ""
#     shift_condition = " AND shift = %s" % frappe.db.escape(shift) if shift else ""
    
#     tank_condition = " AND tio.dcs IN (%s)" % ', '.join(['%s'] * len(dcs_filter)) if dcs_filter else ""
#     tank_shift_condition = " AND tio.shift = %s" % frappe.db.escape(shift) if shift else ""

#     # Query to get milk entry data
#     milk_entry_sql_query = """
#         SELECT 
#             "<b>ACKNOWLEDGEMENT</b>" AS ack,
#             dcs_id as dcs, 
#             SUM(volume) as liter,
#             SUM(volume*1.03) as kg,
#             AVG(fat) as fat, 
#             AVG(snf) as snf,
#             SUM(fat_kg) as kg_fat, 
#             SUM(snf_kg) as kg_snf
#         FROM 
#             `tabMilk Entry`
#         WHERE 
#             date BETWEEN %s AND %s
#             AND docstatus = 1
#             {dcs_condition}
#             {shift_condition}
#         GROUP BY 
#             dcs_id
#     """.format(dcs_condition=dcs_condition, shift_condition=shift_condition)
    
#     milk_data = frappe.db.sql(milk_entry_sql_query, tuple(dcs_filter) + (from_date, to_date) if dcs_filter else (from_date, to_date), as_dict=True)
    
#     # Query to get tanker data
#     tank_sql_query = """
#         SELECT 
#             "<b>RECIVED</b>" AS ack,
#             tio.dcs as dcs, 
#             COALESCE(SUM(tid.quantity), 0) as liter, 
#             COALESCE(SUM(tid.quantity_kg), 0) as kg, 
#             COALESCE(AVG(tid.fat_), 0) as fat, 
#             COALESCE(AVG(tid.snf_), 0) as snf,
#             COALESCE(SUM((tid.quantity_kg * tid.fat_)/100), 0) as kg_fat, 
#             COALESCE(SUM((tid.quantity_kg * tid.snf_)/100), 0) as kg_snf
#         FROM
#             `tabTanker Inward Outward` tio
#         LEFT JOIN
#             `tabTanker Inward Divison` tid ON tid.parent = tio.name
#         WHERE 
#             tio.date BETWEEN %s AND %s
#             AND tio.docstatus = 1
#             {tank_condition}
#             {tank_shift_condition}
#         GROUP BY 
#             tio.dcs
#     """.format(tank_condition=tank_condition, tank_shift_condition=tank_shift_condition)
    
#     tank_data = frappe.db.sql(tank_sql_query, tuple(dcs_filter) + (from_date, to_date) if dcs_filter else (from_date, to_date), as_dict=True)

#     return columns, milk_data + tank_data


