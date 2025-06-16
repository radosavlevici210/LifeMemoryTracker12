# ============================================
# Project: LifeMemoryTracker12
# Author: Ervin Remus Radosavlevici
# Copyright: © 2025 Ervin Remus Radosavlevici
# All rights reserved. Protected under digital trace monitoring.
# Unauthorized usage will trigger automated reports.
# ============================================

import datetime
import socket
import platform
import getpass

def log_access():
    log_info = {
        "timestamp": datetime.datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "user": getpass.getuser()
    }
    with open("access_log.txt", "a") as f:
        f.write(str(log_info) + "\n")

log_access()

from app import app  # noqa: F401
