# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.1.7 => 1.2.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.1.7-1.2.0.py
#
import sys
#from s3 import S3Duplicate

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
ftable = s3db.dvr_case_flag
ltable = s3db.dvr_case_flag_case
ctable = s3db.dvr_case
stable = s3db.dvr_case_status

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade case flags")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "case_flag.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_case_flag.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("dvr_case_flag")
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

            for field in ("advise_at_check_in",
                          "advise_at_check_out",
                          "deny_check_in",
                          "deny_check_out",
                          "is_not_transferable",
                          "is_external",
                          ):
                query = (ftable.deleted != True) & \
                        (ftable[field] == None)
                try:
                    db(query).update(**{field: False})
                except:
                    continue
            infoln("...done")

# -----------------------------------------------------------------------------
if not failed:
    info("Set flags for statuses")

    status_flags = {"STATUS9": "Hospital",
                    "STATUS9A": "Police",
                    "STATUS10": "AFA/UMF",
                    }

    updated = 0
    for status, flag in status_flags.items():

        # Get the flag ID
        query = (ftable.name == flag) & \
                (ftable.deleted != True)
        row = db(query).select(ftable.id, limitby=(0, 1)).first()
        if not row:
            infoln("...failed (Flag not found: %s)" % flag)
            failed = True
            break
        flag_id = row.id

        # Get all cases with the status
        query = (ctable.status_id == stable.id) & \
                (stable.code == status)
        cases = db(query).select(ctable.person_id)
        if not cases:
            continue
        person_ids = set(case.person_id for case in cases)

        # Set flag for all cases
        error = None
        for person_id in person_ids:
            try:
                success = ltable.insert(person_id = person_id,
                                        flag_id = flag_id,
                                        )
            except:
                error = sys.exc_info()[1]
                success = None
            if not success:
                infoln("...failed (could not set flag)")
                if error:
                    infoln(error)
                failed = True
                break
            else:
                updated += 1

        if failed:
            break

    if not failed:
        infoln("...done (%s flags set)" % updated)

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade case statuses")

    # Change code for status "Legally departed"
    # (because it will be renamed by import)
    query = (stable.code == "STATUS11")
    db(query).update(code = "DEPARTED")

    # Change code for status "Inactive"
    # (because it will be renamed by import)
    query = (stable.code == "STATUS8")
    db(query).update(code = "INACTIVE")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "case_status.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_case_status.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("dvr_case_status")
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
    info("Migrate case statuses")

    OBSOLETE = ("STATUS1",
                "STATUS2",
                "STATUS3",
                "STATUS4",
                "STATUS5",
                "STATUS9",
                "STATUS9A",
                "STATUS10",
                )

    NEW = "OPEN"

    query = (stable.code == NEW) & \
            (stable.deleted != True)
    row = db(query).select(stable.id, limitby=(0, 1)).first()
    if not row:
        infoln("...failed (OPEN status not found)")
        failed = True
    else:
        status_id = row.id

        query = (ctable.status_id == stable.id) & \
                (stable.code.belongs(OBSOLETE))
        rows = db(query).select(ctable.id)
        case_ids = set(row.id for row in rows)

        if case_ids:
            updated = db(ctable.id.belongs(case_ids)).update(status_id=status_id)
        else:
            updated = 0

        missed = db(query).count()
        if missed > 0:
            infoln("...failed (%s cases not updated) % missed")
            failed = True
        else:
            infoln("...done (%s cases updated)" % updated)

# -----------------------------------------------------------------------------
if not failed:
    info("Remove obsolete statuses")

    resource = s3db.resource("dvr_case_status",
                             filter = FS("code").belongs(OBSOLETE),
                             )
    success = resource.delete()
    if not success and resource.error:
        infoln("..failed")
        infoln(resource.error)
        failed = True
    else:
        query = (stable.code.belongs(OBSOLETE)) & \
                (stable.deleted != True)
        rows = db(query).select(stable.id)
        missed = len(rows)
        if missed > 0:
            infoln("...failed (%s statuses not deleted)" % missed)
            failed = True
        else:
            infoln("...done")

# -----------------------------------------------------------------------------
if not failed:
    info("Install case event types")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "case_event_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_case_event_type.csv")

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
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
