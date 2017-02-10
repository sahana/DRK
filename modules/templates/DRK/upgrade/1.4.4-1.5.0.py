# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.4.4 => 1.5.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.4.4-1.5.0.py
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
atable = s3db.dvr_case_activity
gtable = current.auth.settings.table_group
ptable = current.auth.permission.table


IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade user roles")

    # Migrate existing roles
    roles_to_migrate = ("ADMIN_HEAD",
                        "ADMINISTRATION",
                        "AUTHENTICATED",
                        "FOOD_STATS",
                        "INFO_POINT",
                        "MEDICAL",
                        "POLICE",
                        "RP",
                        "QUARTIER",
                        "SCAN",
                        "SECURITY",
                        "SECURITY_HEAD",
                        "STAFF",
                        )

    for uid in roles_to_migrate:
        # Get the role ID
        row = db(gtable.uuid == uid).select(gtable.id,
                                            limitby = (0, 1),
                                            ).first()
        if not row:
            continue

        group_id = row.id

        # Archive all current permission rules for this role
        data = {"group_id": None,
                "deleted": True,
                "deleted_fk": '{"group_id": %d}' % group_id,
                }
        try:
            success = db(ptable.id == group_id).update(**data)
        except Exception, e:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True
            break

if not failed:

    # Hide unused roles
    roles_to_hide = ("ORG_ADMIN",
                     "ORG_GROUP_ADMIN",
                     "MAP_ADMIN",
                     "EDITOR",
                     )

    query = (gtable.uuid.belongs(roles_to_hide))
    try:
        success = db(query).update(hidden=True)
    except Exception, e:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True

if not failed:

    # Remove obsolete roles
    roles_to_remove = ("Regierungspräsidium",
                       "Info Point",
                       )

    for name in roles_to_remove:
        query = (gtable.role == name) & \
                (gtable.deleted != True)
        rows = db(query).select(gtable.id)
        for row in rows:
            try:
                auth.s3_delete_role(row.id)
            except Exception, e:
                infoln("...failed")
                infoln(sys.exc_info()[1])
                failed = True
                break

if not failed:

    # Install new user roles
    bi = s3base.S3BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

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
    info("Create document keys for case activities")

    query = (atable.deleted != True) & (atable.doc_id == None)
    rows = db(query).select(atable.id,
                            atable.doc_id,
                            )

    updated = 0
    for row in rows:
        s3db.update_super(atable, row)
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
    info("Migrate case activity details")

    query = (atable.id > 0)

    try:
        updated = db(query).update(activity_details = atable.referral_details,
                                   modified_by = atable.modified_by,
                                   modified_on = atable.modified_on,
                                   )
    except:
        updated = 0
        failed = True
    else:
        try:
            db(query).update(referral_details = None,
                             modified_by = atable.modified_by,
                             modified_on = atable.modified_on,
                             )
        except:
            updated = 0
            failed = True

    if failed:
        infoln("...failed")
    else:
        infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
