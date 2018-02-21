# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.6.8 => 1.7.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.6.8-1.7.0.py
#
#import datetime
import sys
#from s3 import S3DateTime

#from gluon.storage import Storage
#from gluon.tools import callback

# Override auth (disables all permission checks)
auth.override = True

# Failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write(msg)
def infoln(msg):
    sys.stderr.write("%s\n" % msg)

# Load models for tables
ctable = s3db.dvr_case

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade cases")

    updated = 0
    rows = db(ctable.deleted == False).select(ctable.id)
    for row in rows:
        success = s3db.update_super(ctable, row)
        if not success:
            infoln("...failed")
            failed = True
            break
        else:
            updated += 1
    if not failed:
        infoln("...done (%s updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    sys.stderr.write("UPGRADE FAILED - Action rolled back.\n")
else:
    db.commit()
    sys.stderr.write("UPGRADE SUCCESSFUL.\n")
