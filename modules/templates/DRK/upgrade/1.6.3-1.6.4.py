# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.6.3 => 1.6.4
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.6.3-1.6.4.py
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
ctable = s3db.dvr_case
itable = s3db.pr_identity
sitable = s3db.security_seized_item

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Migrate stay-permit-until dates")

    RESIDENCE_PERMIT = 5

    left = itable.on((itable.person_id == ctable.person_id) & \
                     (itable.type == RESIDENCE_PERMIT) & \
                     (itable.deleted == False))
    query = (ctable.stay_permit_until != None) & \
            (ctable.deleted == False)
    rows = db(query).select(ctable.person_id,
                            ctable.stay_permit_until,
                            itable.id,
                            itable.valid_until,
                            left=left,
                            )

    created = 0
    updated = 0

    for row in rows:

        case = row.dvr_case
        identity = row.pr_identity

        if not identity.id:
            # Create one
            try:
                success = itable.insert(person_id = case.person_id,
                                        type = RESIDENCE_PERMIT,
                                        valid_until = case.stay_permit_until,
                                        )
            except:
                infoln("...failed")
                infoln(sys.exc_info()[1])
                failed = True
                break

            if success:
                created += 1

        elif not identity.valid_until:
            # Update it
            try:
                success = identity.update_record(valid_until = case.stay_permit_until)
            except:
                infoln("...failed")
                infoln(sys.exc_info()[1])
                failed = True
                break
            if success:
                updated += 1

    if not failed:
        infoln("...done (%s updated, %s newly created)" % (updated, created))

# -----------------------------------------------------------------------------
if not failed:
    info("Create document keys for seized items")

    query = (sitable.deleted != True) & (sitable.doc_id == None)
    rows = db(query).select(sitable.id,
                            sitable.doc_id,
                            )

    updated = 0
    for row in rows:
        s3db.update_super(sitable, row)
        if row.doc_id:
            updated += 1
        else:
            failed = True
            break

    if failed:
        infoln("...failed")
    else:
        infoln("...done (%s records updated)" % updated)

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
