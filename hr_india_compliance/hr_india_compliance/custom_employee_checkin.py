#For Improve Employee Attendances
from datetime import datetime, timedelta
import frappe
from frappe.utils.data import get_datetime, get_time, getdate

def validate(self,method):
    get_shift(self)
def before_insert(self,method):
    update_last_sync_datetime(self)

def update_last_sync_datetime(self):
    if self.shift:
        shift = frappe.get_cached_doc("Shift Type",self.shift)
        shift.db_set("last_sync_of_checkin",get_datetime(self.time))
        shift.save()


def get_shift(self):
    settings = frappe.get_doc("Leave And Attendance Settings")
    if settings.process_attendance_strictly_based_on_shift:
        shift = ""
        emp = frappe.get_doc("Employee",self.employee)
        check_assignament = frappe.db.sql("""SELECT shift_type FROM `tabShift Assignment` 
                                    WHERE start_date <= "{0}"
                                    AND end_date >= "{0}"
                                    AND employee = "{1}"
                                    AND docstatus = 1
                                """.format(getdate(self.time),self.employee),as_dict=1)
        if check_assignament:
            shift = check_assignament[0].get('shift_type') if check_assignament else ""
        else:
            shift=emp.default_shift

        if shift:
            _shift = frappe.get_doc("Shift Type",shift)
            self.shift = _shift.name
            shift_actual_start = get_time(
                datetime.combine(get_datetime(self.time), datetime.min.time())
                + _shift.start_time
                - timedelta(minutes=_shift.begin_check_in_before_shift_start_time)
            )
            shift_actual_end = get_time(
                datetime.combine(get_datetime(self.time), datetime.min.time())
                + _shift.end_time
                - timedelta(minutes=_shift.allow_check_out_after_shift_end_time)
            )
            for_time = get_time(self.time)
            start_datetime = end_datetime = None
            for_timestamp = get_datetime(self.time)
            if _shift.start_time > _shift.end_time:
                # shift spans across 2 different days
                if for_time >= shift_actual_start:
                    # if for_timestamp is greater than start time, it's within the first day
                    start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.start_time
                    for_timestamp += timedelta(days=1)
                    end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.end_time

                elif for_time < shift_actual_start:
                    # if for_timestamp is less than start time, it's within the second day
                    end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.end_time
                    for_timestamp += timedelta(days=-1)
                    start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.start_time
            elif (
                shift_actual_start > shift_actual_end
                and for_time < shift_actual_start
                and get_time(_shift.end_time) > shift_actual_end
            ):
                # for_timestamp falls within the margin period in the second day (after midnight)
                # so shift started and ended on the previous day
                for_timestamp += timedelta(days=-1)
                end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.end_time
                start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.start_time
            elif (
                shift_actual_start > shift_actual_end
                and for_time > shift_actual_end
                and get_time(_shift.start_time) < shift_actual_start
            ):
                # for_timestamp falls within the margin period in the first day (before midnight)
                # so shift started and ended on the next day
                for_timestamp += timedelta(days=1)
                start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.start_time
                end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.end_time
            else:
                # start and end timings fall on the same day
                start_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.start_time
                end_datetime = datetime.combine(for_timestamp, datetime.min.time()) + _shift.end_time


            self.shift_start = start_datetime
            self.shift_end = end_datetime
            actual_start = start_datetime - timedelta(
            minutes=_shift.begin_check_in_before_shift_start_time
            )
            actual_end = end_datetime + timedelta(minutes=_shift.allow_check_out_after_shift_end_time)
            self.shift_actual_start = actual_start
            self.shift_actual_end = actual_end
            return start_datetime, end_datetime
        
