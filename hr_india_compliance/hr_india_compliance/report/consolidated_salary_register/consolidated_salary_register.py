import frappe
from frappe.utils.data import flt

def execute(filters=None):
    print("trigger this data***********************************")

    columns = get_columns(filters)
    data = get_data(filters)

    if filters.get("group_by") == "Department":
        print("trigger")
        condition = get_filters(filters)
        
        columns.append({
            "label": frappe.bold("Net Pay"),
            "fieldname": "total_net_pay",
            "fieldtype": "Currency",
            "width": 120
        })
        
        department_totals_query = """
            SELECT department, SUM(net_pay) AS total_net_pay
            FROM `tabSalary Slip` s
            WHERE {conditions}
            GROUP BY department
        """.format(conditions=condition)
        print("department_totals_query:", department_totals_query)
        
        department_totals_results = frappe.db.sql(department_totals_query, as_dict=True)
        
        department_totals = {result['department']: result['total_net_pay'] for result in department_totals_results}
       
        for item in data:
            department = item.get('department')
            item["total_net_pay"] = department_totals.get(department, 0)

    if filters.get("group_by") == "Cost Center":
        condition = get_filters(filters)
        
        columns.append({
            "label": frappe.bold("Net Pay"),
            "fieldname": "total_net_pay_costcenter",
            "fieldtype": "Currency",
            "width": 120
        })
        
        data = [d for d in data if any(value != 0 for value in d.values())]
        
        cost_centers = set(d.get("cost_center") for d in data)
        cost_center_totals = {}
        
        for cost_center in cost_centers:
            query = """
                SELECT SUM(net_pay) AS total_net_pay
                FROM `tabSalary Slip` s
                WHERE custom_cost_center = %s AND {conditions}
            """.format(conditions=condition)
            
            cost_center_wise_total_net = frappe.db.sql(query, (cost_center,), as_dict=True)
            
            if cost_center_wise_total_net:
                cost_center_totals[cost_center] = cost_center_wise_total_net[0].total_net_pay
        
        
        for cost in data:
            cost_center = cost.get("cost_center")
            cost["total_net_pay_costcenter"] = cost_center_totals.get(cost_center,0)

        # data = [d for d in data if any(value != 0 for value in d.values())]
        
            

    return columns, data

def get_filters(filters):
    conditions = []
    doc_status = {"Draft": 0, "Submitted": 1}
    
    if filters.get("company"):
        conditions.append(f"s.company = '{filters.get('company')}'")
    if filters.get("branch"):
        conditions.append(f"s.branch = '{filters.get('branch')}'")
    if filters.get("from_date"):
        conditions.append(f"DATE(s.start_date) >= '{filters.get('from_date')}'")
    if filters.get("to_date"):
        conditions.append(f"DATE(s.end_date) <= '{filters.get('to_date')}'")
    if filters.get("docstatus"):
        if filters.get("docstatus") == "Draft":
            conditions.append("s.docstatus = 0")
        else:
            conditions.append(f"s.docstatus = {doc_status.get(filters.get('docstatus'))}")
    
    return " AND ".join(conditions) if conditions else "1=1"

def get_columns(filters):
    salary_components = frappe.get_all("Salary Component", fields=["name"])
    columns = []
    
    if filters.get("group_by") == "Department":
        columns.append({
            "label": frappe.bold("Department"),
            "fieldname": "department",
            "fieldtype": "Link",
            "options": "Department",
            "width": 120
        })
    if filters.get("group_by") == "Cost Center":
        columns.append({
            "label": frappe.bold("Cost Center"),
            "fieldname": "cost_center",
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 120
        })

    columns += [{
        "label": frappe.bold(component.name),
        "fieldname": component.name.lower().replace(" ", "_"),
        "fieldtype": "Currency",
        "width": 120
    } for component in salary_components]

    return columns

def get_data(filters):
    conditions = get_filters(filters)
    result = []

    salary_components = frappe.get_all("Salary Component", fields=["name"])
    
    if filters.get("group_by") == "Department":
        departments = frappe.get_all("Salary Slip", 
                                    fields=["department"], 
                                    filters={"company": filters.get("company")}, 
                                    distinct=True)

        for department in departments:
            row = {"department": department.department}
            for component in salary_components:
                salary_detail = frappe.db.sql("""
                    SELECT SUM(sd.amount) AS total_amount
                    FROM `tabSalary Detail` sd
                    LEFT JOIN `tabSalary Slip` s ON sd.parent = s.name
                    WHERE s.docstatus != 2 
                        AND sd.salary_component = %s
                        AND s.department = %s
                        AND {conditions}
                """.format(conditions=conditions), (component.name, department.department), as_dict=True)
                total_amount = salary_detail[0].total_amount if salary_detail and salary_detail[0].total_amount else 0
                            
                row[component.name.lower().replace(" ", "_")] = total_amount
            result.append(row)
    
    if filters.get("group_by") == "Cost Center":
        cost_center_data = cost_center_wise(filters)

        for cost_center in cost_center_data:
            row = {"cost_center": cost_center["cost_center"]}
            for component in salary_components:
                salary_detail = frappe.db.sql("""
                    SELECT SUM(sd.amount) AS total_amount
                    FROM `tabSalary Detail` sd
                    LEFT JOIN `tabSalary Slip` s ON sd.parent = s.name
                    LEFT JOIN `tabEmployee` e ON s.employee = e.employee
                    WHERE s.docstatus != 2 
                        AND sd.salary_component = %s
                        AND e.payroll_cost_center = %s
                        AND {conditions}
                """.format(conditions=conditions), (component.name, cost_center["cost_center"]), as_dict=True)

                total_amount = salary_detail[0].total_amount if salary_detail and salary_detail[0].total_amount else 0          
                row[component.name.lower().replace(" ", "_")] = total_amount
            result.append(row)
       
    return result

def cost_center_wise(filters):
    print("trigger>>>>>>")
    conditions = get_filters(filters)
    cost_center_data = []
    cost_centers = frappe.get_all("Employee", fields=["distinct payroll_cost_center"], filters={"company": filters.get("company")})

    for cost_center in cost_centers:
        salary_details = frappe.db.sql("""
            SELECT SUM(sd.amount) AS total_amount
            FROM `tabSalary Detail` sd
            LEFT JOIN `tabSalary Slip` s ON sd.parent = s.name
            WHERE s.docstatus != 2 
                AND s.employee IN (
                    SELECT employee FROM `tabEmployee` WHERE payroll_cost_center = %s
                )
                AND {conditions}
        """.format(conditions=conditions), (cost_center.payroll_cost_center,), as_dict=True)

        total_amount = salary_details[0].total_amount if salary_details else 0
        cost_center_data.append({
            "cost_center": cost_center.payroll_cost_center,
            "total_amount": total_amount
        })
    
    return cost_center_data
