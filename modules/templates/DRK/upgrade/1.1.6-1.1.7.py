# -*- coding: utf-8 -*-
#
# Database upgrade script
#
# DRK Template Version 1.1.6 => 1.1.7
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/DRK/upgrade/1.1.6-1.1.7.py
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

IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "DRK")

# -----------------------------------------------------------------------------
if not failed:
    info("Upgrade case flags")

    query = (ftable.deleted != True) & \
            (ftable.advise_at_check_in == None) & \
            (ftable.advise_at_check_out == None) & \
            (ftable.deny_check_in == None) & \
            (ftable.deny_check_out == None)

    try:
        success = db(query).update(advise_at_check_in = False,
                                   advise_at_check_out = False,
                                   deny_check_in = False,
                                   deny_check_out = False,
                                   )
    except:
        infoln("...failed")
        infoln(sys.exc_info()[1])
        failed = True
    else:
        missed = db(query).count()
        infoln("...done (%s updated, %s missed)" % (success, missed))
# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    print >> sys.stderr, "UPGRADE FAILED - Action rolled back."
else:
    db.commit()
    print >> sys.stderr, "UPGRADE SUCCESSFUL."
