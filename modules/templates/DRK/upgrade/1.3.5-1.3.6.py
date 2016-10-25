# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.3.5 => 1.3.6
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.3.5-1.3.6.py
#
import sys

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

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade case event types")

    query = (ttable.deleted != True)
    updated = db(query).update(presence_required = True,
                               modified_on = ttable.modified_on,
                               modified_by = ttable.modified_by,
                               )

    query = (ttable.code == "FOOD")
    db(query).update(presence_required = False)

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
