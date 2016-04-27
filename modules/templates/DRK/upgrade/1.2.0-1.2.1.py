# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.2.0 => 1.2.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.2.0-1.2.1.py
#
import datetime
import sys
from s3 import S3DateTime

#from gluon.storage import Storage
#from gluon.tools import callback

# Override auth (disables all permission checks)
auth.override = True

# Failed-flag
failed = False

# Info
def info(msg):
    print >> sys.stderr, msg,
def infoln(msg):
    print >> sys.stderr, msg

# Load models for tables
ctable = s3db.dvr_case
etable = s3db.dvr_case_event
htable = s3db.cr_shelter_registration_history
atable = s3db.dvr_case_appointment
ttable = s3db.dvr_case_appointment_type
ptable = s3db.dvr_allowance
ftable = s3db.dvr_case_flag

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade appointment types")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "case_appointment_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_case_appointment_type.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("dvr_case_appointment_type")
            resource.import_xml(File, format="csv", stylesheet=stylesheet)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        if resource.error:
            infoln("...failed")
            infoln(resource.error)
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade case flags with allowance_suspended attribute")

    query = (ftable.deleted != True) & \
            (ftable.allowance_suspended == None)

    try:
        success = db(query).update(allowance_suspended = False)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        missed = db(query).count()
        infoln("...done (%s updated, %s missed)" % (success, missed))

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade case flags with advise_at_id_check attribute")

    query = (ftable.deleted != True) & \
            (ftable.advise_at_id_check == None)

    try:
        success = db(query).update(advise_at_id_check = False)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        missed = db(query).count()
        infoln("...done (%s updated, %s missed)" % (success, missed))

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade user roles")

    bi = s3base.S3BulkImporter()
    filename = os.path.join(request.folder, "modules", "templates", "DRK", "auth_roles.csv")

    with open(filename, "r") as File:
        try:
            bi.import_role(filename)
        except Exception, e:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
if not failed:
    info("Establish last-seen-on for all valid cases")

    now = current.request.utcnow

    last_event = etable.date.max()
    last_check = htable.date.max()
    last_appointment = atable.date.max()
    last_payment = ptable.paid_on.max()

    # Fields to select
    fields = [ctable.id,
              last_event,
              last_check,
              ]

    left = [etable.on((etable.person_id == ctable.person_id) & \
                      (etable.date != None) & \
                      (etable.date <= now) & \
                      (etable.deleted != True)),
            htable.on((htable.person_id == ctable.person_id) & \
                      (htable.status.belongs(2, 3)) & \
                      (htable.date != None) & \
                      (htable.deleted != True))
            ]

    # Appointments
    check_appointments = settings.get_dvr_appointments_update_last_seen_on()
    if check_appointments:

        # Appointment types that require presence
        query = (ttable.presence_required == True)
        rows = db(query).select(ttable.id)
        type_ids = [row.id for row in rows]

        # Additional join
        left.append(atable.on((atable.person_id == ctable.person_id) & \
                              (atable.date != None) & \
                              (atable.date <= now.date()) & \
                              (atable.status == 4) & \
                              (atable.type_id.belongs(type_ids)) & \
                              (atable.deleted != True)))
        # Additional field
        fields.append(last_appointment)

    # Allowance payments
    check_payments = settings.get_dvr_payments_update_last_seen_on()
    if check_payments:
        # Additional join
        left.append(ptable.on((ptable.person_id == ctable.person_id) & \
                              (ptable.paid_on != None) & \
                              (ptable.status == 2) & \
                              (ptable.deleted != True)))
        # Additional field
        fields.append(last_payment)

    # Select for valid cases, group by case
    query = (ctable.archived != True) & \
            (ctable.last_seen_on == None) & \
            (ctable.deleted != True)
    rows = db(query).select(groupby = ctable.id,
                            left = left,
                            *fields)

    # Counter
    updated = 0

    for row in rows:

        case = row.dvr_case
        last_seen_on = row[last_event]

        max_check = row[last_check]
        if max_check and \
           not (last_seen_on or max_check > last_seen_on):
            last_seen_on = max_check

        if check_appointments:
            max_appointment = row[last_appointment]
            if max_appointment and \
               (not last_seen_on or max_appointment > last_seen_on.date()):

                date = max_appointment
                try:
                    date = datetime.datetime.combine(date, datetime.time(0, 0, 0))
                except TypeError:
                    pass
                # Local time offset to UTC (NB: can be 0)
                delta = S3DateTime.get_offset_value(current.session.s3.utc_offset)
                # Default to 08:00 local time (...unless that would be future)
                date = min(now, date + datetime.timedelta(seconds = 28800 - delta))
                last_seen_on = date

        if check_payments:
            max_payment = row[last_payment]
            if max_payment and \
               (not last_seen_on or max_payment > last_seen_on):
                last_seen_on = max_payment

        if last_seen_on:
            case.update_record(last_seen_on = last_seen_on,
                               modified_by = ctable.modified_by,
                               modified_on = ctable.modified_on,
                               )
            updated += 1

    infoln("...done (%s updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
