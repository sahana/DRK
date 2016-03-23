# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.1.4 => 1.1.5
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.1.4-1.1.5.py
#
import sys

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
#ptable = s3db.pr_person

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade GIS Config")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "gis", "config.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "gis_config.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("gis_config")
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
    info("Upgrade feature layers")

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
if not failed:
    info("Restoring missing default appointments")

    # Get open case statuses
    stable = s3db.dvr_case_status
    query = (stable.is_closed == False) & \
            (stable.deleted != True)
    rows = db(query).select(stable.id)
    open_statuses = set(row.id for row in rows)

    # Get default appointments
    ttable = s3db.dvr_case_appointment_type
    query = (ttable.active == True) & \
            (ttable.deleted != True)
    rows = db(query).select(ttable.id)
    active_appointments = set(row.id for row in rows)

    ctable = s3db.dvr_case
    atable = s3db.dvr_case_appointment
    created = 0
    if open_statuses and active_appointments:
        for appointment_type in active_appointments:

            # Get all open cases which have no default appointment of this type
            left = atable.on((atable.person_id == ctable.person_id) &
                             (atable.type_id == appointment_type) &
                             (atable.deleted != True))
            query = (ctable.status_id.belongs(open_statuses)) & \
                    (ctable.archived != True) & \
                    (ctable.deleted != True) & \
                    (atable.id == None)
            rows = db(query).select(ctable.id,
                                    ctable.person_id,
                                    left=left,
                                    )
            for row in rows:
                case_id = row.id
                if case_id:
                    # Create the missing appointment
                    success = atable.insert(case_id = case_id,
                                            person_id = row.person_id,
                                            type_id = appointment_type,
                                            )
                    if success:
                        created += 1
                        info(".")
                    else:
                        info("X")
    infoln("...done (%s appointments created)" % created)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
