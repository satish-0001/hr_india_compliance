import frappe
from frappe.utils.data import cint, flt


def execute(filters=None):
    validate_report(filters)
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "provident_fund_account", "label": "UAN", "fieldtype": "Data", "width": 170},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 170},
        {"fieldname": "gross_pay", "label": "Gross Pay", "fieldtype": "Currency", "width": 170},
        {"fieldname": "pf_salary", "label": "PF Salary", "fieldtype": "Currency", "width": 170},
        {"fieldname": "pension_salary", "label": "Pension Salary", "fieldtype": "Currency", "width": 170},
        {"fieldname": "edli", "label": "EDLI", "fieldtype": "Currency", "width": 170},
        {"fieldname": "pf_12_per", "label": "PF", "fieldtype": "Currency", "width": 170},
        {"fieldname": "employee_pension_amount", "label": "EPS", "fieldtype": "Currency", "width": 200},
        {"fieldname": "employee_pf", "label": "EPF", "fieldtype": "Currency", "width": 170},
        {"fieldname": "payment_absent_days", "label": "NCP Days", "fieldtype": "Float", "width": 170},
    ]


def validate_report(filters):
    if filters.from_date > filters.to_date:
        frappe.throw("From Date can't be greater than the To Date")


def get_data(filters):

    query = """
        SELECT DISTINCT ss.name, ss.employee, ss.employee_name, ss.salary_structure, ss.gross_pay, ss.total_working_days, ss.payment_days
        FROM `tabSalary Slip` ss
        JOIN `tabSalary Detail` sd ON ss.name = sd.parent
        WHERE sd.parentfield = 'Deductions'
        AND ss.docstatus IN (0,1)
        AND ss.company = %(company)s
        AND ss.start_date >= %(start_date)s
        AND ss.end_date <= %(end_date)s
        AND ss.name IN (
                SELECT parent 
                FROM `tabSalary Detail`
                WHERE parentfield = 'Deductions'
                AND custom_pf_12_per = 1
        )
        {branch_clause}
        ORDER BY ss.branch, ss.employee_name
        """
    branch_clause = ""
    args = {
        "company": filters.company,
        "start_date": filters.from_date,
        "end_date": filters.to_date
    }
    if filters.branch:
        branch_clause = "AND ss.branch = %(branch)s"
        args["branch"] = filters.branch

    salary_slip_data = frappe.db.sql(
        query.format(
            branch_clause = branch_clause
        ),
        args,
        as_dict=True
    )

    if not salary_slip_data:
        frappe.throw(f"No data found from {filters.from_date} to {filters.to_date} date range")
        
    structures = {}
    data = []
    for d in salary_slip_data:
        employee_uan = frappe.get_cached_value("Employee", d.employee, "uan_number")
        if not employee_uan:
            continue

        if d.salary_structure not in structures:
            structures[d.salary_structure] = frappe.get_cached_doc("Salary Structure", d.salary_structure)

        salary_slip_doc = frappe.get_cached_doc("Salary Slip", d.name)

        data_dict = {
            "employee_name": d.employee_name,
            "provident_fund_account": employee_uan,
            "gross_pay": d.gross_pay,
            "payment_absent_days": cint(d.total_working_days) - cint(d.payment_days),
        }

        add_structure_components(salary_slip_doc, structures[d.salary_structure], "deductions", data_dict)
        data.append(data_dict)

    return data

components = {}
def add_structure_components(salary_slip, salary_structure, component_type, data_dict):
    salary_slip.data, salary_slip.default_data = salary_slip.get_data_for_eval()

    for struct_row in salary_structure.get(component_type):
        amount = salary_slip.eval_condition_and_formula(struct_row, salary_slip.data)
        if struct_row.statistical_component:
            salary_slip.default_data[struct_row.abbr] = flt(amount)
            if struct_row.depends_on_payment_days:
                payment_days_amount = (
                    flt(amount) * flt(salary_slip.payment_days) / cint(salary_slip.total_working_days)
                    if salary_slip.total_working_days else 0
                )
                salary_slip.data[struct_row.abbr] = flt(payment_days_amount, struct_row.precision("amount"))
        
        amount = amount or 0
        if struct_row.salary_component not in components:
            components[struct_row.salary_component] = frappe.get_cached_doc("Salary Component", struct_row.salary_component)

        sc = components[struct_row.salary_component]
        if sc.round_to_the_nearest_integer:
            amount = round(amount)

        if sc.custom_pension_salary:
            data_dict["pension_salary"] = amount
            data_dict["edli"] = amount
        if sc.custom_pf_salary:
            data_dict["pf_salary"] = amount
        if sc.custom_pf_12_per:
            data_dict["pf_12_per"] = amount 
        if sc.custom_employee_pension_amount:
            data_dict["employee_pension_amount"] = amount
        if sc.custom_employee_pf:
            data_dict["employee_pf"] = amount