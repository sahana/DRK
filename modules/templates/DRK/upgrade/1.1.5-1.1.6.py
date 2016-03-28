# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.1.5 => 1.1.6
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.1.5-1.1.6.py
#
import sys
from s3 import S3Duplicate

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
gtable = s3db.pr_group
attable = s3db.dvr_case_appointment_type
ftable = s3db.gis_layer_feature

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Re-count household size for all case groups")

    query = (gtable.group_type == 7) & \
            (gtable.deleted != True)
    rows = db(query).select(gtable.id)

    household_size = s3db.dvr_case_household_size

    updated = 0
    for row in rows:
        try:
            household_size(row.id)
        except Exception, e:
            failed = True
            infoln("...failed")
            break
        else:
            updated += 1
            info(".")

    if not failed:
        print >> sys.stderr, "...done (%s groups updated)" % updated

# -----------------------------------------------------------------------------
if not failed:
    info("Rename appointment type 'Zu RP geschickt'")

    query = (attable.name == "Zu RP geschickt")
    success = db(query).update(name="Sent to RP")
    if success:
        infoln("...done")
    else:
        infoln("...not found, please rename manually")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade map feature layers")

    # Deduplicate styles
    s3db.configure("gis_style",
                   deduplicate=S3Duplicate(primary = ("layer_id",),
                                           secondary = ("config_id",),
                                           ),
                   )

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "gis", "layer_feature.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "gis_layer_feature.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("gis_layer_feature")
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
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
