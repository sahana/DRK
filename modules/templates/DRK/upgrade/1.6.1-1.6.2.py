# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.6.1 => 1.6.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.6.1-1.6.2.py
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
    print >> sys.stderr, msg,
def infoln(msg):
    print >> sys.stderr, msg

# Load models for tables
itable = s3db.security_seized_item

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade seized items")

    updated_total = 0

    q = (itable.status == None) & \
        (itable.deleted == False)

    # For items with a returned_on date => set status to RET
    query = (itable.returned_on != None) & q
    try:
        updated = db(query).update(status="RET")
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        updated_total += updated

if not failed:

    # For items without a returned_on date => set status to DEP
    query = (itable.returned_on == None) & q
    try:
        updated = db(query).update(status="DEP")
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        updated_total += updated
        infoln("...done (%s records updated)" % updated_total)

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade user roles")

    bi = s3base.S3BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    with open(filename, "r") as File:
        try:
            bi.import_role(filename)
        except:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
