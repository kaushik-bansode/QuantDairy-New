# Copyright (c) 2024, quantdairy and contributors
# For license information, please see license.txt

import frappe  

def execute(filters=None):
    if not filters:
        filters = {}
    columns, data = [], []
    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    return [
        {
            "fieldname": "Date",
            "fieldtype": "Date",
            "label": "Date",
        },
        {
            "fieldname": "name",
            "fieldtype": "Link",
            "label": "Name",
            "options": "Stock Ledger Entry",
        },
        {
            "fieldname": "Item",
            "fieldtype": "Link",
            "label": "Item",
            "options": "Stock Ledger Entry",
        },
        {
            "fieldname": "Customer",
            "fieldtype": "Data",
            "label": "Party",
        },
        {
            "fieldname": "Voucher",
            "fieldtype": "Link",
            "label": "Voucher",
            "options": "Stock Ledger Entry",
        },
        {
            "fieldname": "Voucher Type",
            "fieldtype": "Link",
            "label": "Voucher Type",
            "options": "Stock Ledger Entry",
        },
        {
            "fieldname": "Warehouse",
            "fieldtype": "Link",
            "label": "Warehouse",
            "options": "Stock Ledger Entry",
        },
        {
            "fieldname": "Stock Uom",
            "fieldtype": "Data",
            "label": "Stock Uom",
        },
        {
            "fieldname": "Dispatch Qty",
            "fieldtype": "Float",
            "label": "Dispatch Qty",
        },
        {
            "fieldname": "Total Qty",
            "fieldtype": "Float",
            "label": "Total Qty",
        },
        {
            "fieldname": "Route",
            "fieldtype": "Data",
            "label": "Route",
        },
    ]


def get_data(filters):
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    item_code = filters.get('item_code')
    customer = filters.get('customer')
    route = filters.get('route')
    conditions = []
    params = {'from_date': from_date, 'to_date': to_date}

    sql_query = """
        SELECT
            DATE(sl.creation) AS 'Date', 
            sl.name, 
            sl.item_code AS 'Item', 
            si.customer_name AS 'Customer', 
            sl.voucher_no AS 'Voucher', 
            sl.voucher_type AS 'Voucher Type', 
            sl.warehouse AS 'Warehouse', 
            sl.stock_uom AS 'Stock Uom', 
            CASE WHEN sl.actual_qty < 0 THEN sl.actual_qty ELSE NULL END AS 'Dispatch Qty',
            SUM(si.total_qty) AS 'Total Qty',
            si.route AS 'Route'
        FROM 
            `tabStock Ledger Entry` sl
        LEFT OUTER JOIN 
            `tabSales Invoice` si ON sl.voucher_no = si.name
        WHERE
            DATE(sl.creation) BETWEEN %(from_date)s AND %(to_date)s
            AND si.docstatus = '1' 
            AND sl.voucher_type = 'Sales Invoice'
    """

    if item_code:
        conditions.append("sl.item_code = %(item_code)s")
        params.update({'item_code': item_code})

    if route:
        conditions.append("si.route = %(route)s")
        params.update({'route': route})

    if customer:
        conditions.append("si.customer_name = %(customer)s")
        params.update({'customer': customer})

    if conditions:
        sql_query += " AND " + " AND ".join(conditions)

    sql_query += """
        GROUP BY 
            DATE(sl.creation), 
            sl.name, 
            sl.item_code, 
            si.customer_name, 
            sl.voucher_no, 
            sl.voucher_type, 
            sl.warehouse, 
            sl.stock_uom, 
            sl.actual_qty,
            si.route
    """

    data = frappe.db.sql(sql_query, params, as_dict=True)
    return data
                    