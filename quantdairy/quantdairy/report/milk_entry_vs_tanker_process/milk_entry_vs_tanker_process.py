import frappe
from datetime import datetime, timedelta

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
    from_shift = filters.get('from_shift')
    to_shift = filters.get('to_shift')
    dcs_filter = filters.get('dcs')

    from_date = datetime.strptime(from_date, '%Y-%m-%d')
    to_date = datetime.strptime(to_date, '%Y-%m-%d')
    
    # Shift conditions
    if from_shift == "Morning":
        from_shift_condition = "AND shift IN ('Morning', 'Evening')"
    else:  # Evening
        from_shift_condition = "AND shift = 'Evening'"
    
    if to_shift == "Morning":
        to_shift_condition = "AND shift = 'Morning'"
    else:  # Evening
        to_shift_condition = "AND shift IN ('Morning', 'Evening')"

    if not isinstance(dcs_filter, list):
        dcs_filter = [dcs_filter] if dcs_filter else []

    dcs_condition = " AND dcs_id IN ({})".format(', '.join(['%s'] * len(dcs_filter))) if dcs_filter else ""
    tank_condition = " AND tio.dcs IN ({})".format(', '.join(['%s'] * len(dcs_filter))) if dcs_filter else ""

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
            {from_shift_condition}
            {dcs_condition}
        GROUP BY 
            dcs_id
    """.format(from_shift_condition=from_shift_condition, dcs_condition=dcs_condition)

    milk_params = [from_date, to_date] + dcs_filter
    
    milk_data = frappe.db.sql(milk_entry_sql_query, tuple(milk_params), as_dict=True)

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
            {to_shift_condition}
            {tank_condition}
        GROUP BY 
            tio.dcs
    """.format(to_shift_condition=to_shift_condition, tank_condition=tank_condition)

    tank_params = [from_date, to_date] + dcs_filter
    
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