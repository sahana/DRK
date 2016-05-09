# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.2.1 => 1.3.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.2.1-1.3.0.py
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
ctable = s3db.dvr_case
stable = s3db.dvr_case_status
gtable = s3db.pr_group
mtable = s3db.pr_group_membership
rtable = s3db.pr_group_member_role

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
if not failed:
    info("Establish closed-on date for all valid cases")

    # Get all closed, valid cases without a closed_on date
    left = stable.on(stable.id == ctable.status_id)
    query = (ctable.archived == False) & \
            (stable.is_closed == True) & \
            (ctable.closed_on == None) & \
            (ctable.deleted != True)
    cases = db(query).select(ctable.id,
                             left = left,
                             )
    case_ids = set([case.id for case in cases])

    if case_ids:
        # Update those cases with closed_on=modified_on
        query = ctable.id.belongs(case_ids)
        success = db(query).update(closed_on = ctable.modified_on,
                                modified_on = ctable.modified_on,
                                modified_by = ctable.modified_by,
                                )

        if success != len(case_ids):
            infoln("...failed")
            failed = True
        else:
            infoln("...done (%s cases updated)" % success)
    else:
        infoln("...skipped (no closed cases without closed-on date found)")

# -----------------------------------------------------------------------------
if not failed:
    info("Identify heads of families")

    left = mtable.on((mtable.group_id == gtable.id) & \
                     (mtable.group_head == True))
    query = (gtable.group_type == 7) & \
            (gtable.deleted != True)
    rows = db(query).select(gtable.id,
                            groupby = gtable.id,
                            having = (mtable.id.count() == 0),
                            left = left,
                            )
    group_ids = set([row.id for row in rows])

    left = rtable.on(rtable.id == mtable.role_id)
    query = mtable.group_id.belongs(group_ids)
    rows = db(query).select(mtable.id,
                            mtable.group_id,
                            mtable.created_on,
                            rtable.name,
                            left = left,
                            orderby = (mtable.group_id, mtable.created_on, mtable.id),
                            )

    heads = {}
    updated = 0
    for row in rows:
        membership = row.pr_group_membership
        group_id = membership.group_id
        if group_id in heads:
            candidates = heads[group_id]
        else:
            candidates = heads[group_id] = {"1": None, "f": None}
        if row.pr_group_member_role.name == "Father":
            if candidates["f"] is None:
                candidates["f"] = membership
        if candidates["1"] is None:
            candidates["1"] = membership

    for group_id, candidates in heads.items():
        for role in ("f", "1"):
            candidate = candidates[role]
            if candidate:
                candidate.update_record(group_head = True)
                updated += 1
                break

    infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade family member roles")

    # File and Stylesheet Paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "pr", "group_member_role.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "group_member_role.csv")

    # Import, fail on any errors
    try:
        with open(filename, "r") as File:
            resource = s3db.resource("pr_group_member_role")
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

if not failed:
    info("Replace and remove obsolete family member roles")

    obsolete = ("Father", "Mother")
    replace_by = "Spouse"
    member_roles = list(obsolete) + [replace_by]

    # Get the role IDs
    query = (rtable.name.belongs(member_roles)) & \
            (rtable.deleted != True)
    rows = db(query).select(rtable.id,
                            rtable.name,
                            )
    roles = dict((row.name, row.id) for row in rows)

    # Replace old roles with new role
    old = [roles[name] for name in obsolete if name in roles]
    new = roles.get(replace_by)
    if old and new:
        query = (mtable.role_id.belongs(old)) & \
                (mtable.group_head != True) & \
                (mtable.deleted != True)
        try:
            db(query).update(role_id = new)
        except:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True

    if old and new and not failed:
        query = (mtable.role_id.belongs(old)) & \
                (mtable.group_head == True) & \
                (mtable.deleted != True)
        try:
            db(query).update(role_id = None)
        except:
            infoln("...failed")
            infoln(sys.exc_info()[1])
            failed = True

    # Remove obsolete roles
    if old and new and not failed:
        query = FS("name").belongs(obsolete)
        resource = s3db.resource("pr_group_member_role",
                                 filter = query,
                                 )
        try:
            resource.delete()
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
