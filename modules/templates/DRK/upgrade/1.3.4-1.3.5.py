# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.3.4 => 1.3.5
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.3.4-1.3.5.py
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
ttable = s3db.dvr_case_event_type
etable = s3db.dvr_case_event
ctable = s3db.dvr_case

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade case events")

    query = (ttable.id == etable.type_id) & \
            (etable.deleted != True)
    rows = db(query).select(etable.id,
                            etable.person_id,
                            etable.quantity,
                            ttable.code,
                            )

    get_household_size = s3db.dvr_get_household_size

    updated = 0
    for row in rows:

        event = row.dvr_case_event
        if event.quantity is not None:
            continue

        quantity = 1.0

        event_type = row.dvr_case_event_type
        if event_type.code == "FOOD":
            adults, children = get_household_size(event.person_id,
                                                  formatted=False,
                                                  )
            household_size = adults + children
            if household_size > 1:
                quantity = float(household_size)

        event.update_record(quantity=quantity)
        updated += 1

    infoln("...done (%s rows updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
