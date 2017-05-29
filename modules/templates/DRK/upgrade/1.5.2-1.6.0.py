# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.5.2 => 1.6.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.5.2-1.6.0.py
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
#atable = s3db.dvr_case_activity
ettable = s3db.dvr_case_event_type

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade case event types")

    query = (ettable.is_inactive == None)
    try:
        updated = db(query).update(is_inactive = False)
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
if not failed:
    info("Install new FOOD event types")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "case_event_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_food_event_type.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("dvr_case_event_type")
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
