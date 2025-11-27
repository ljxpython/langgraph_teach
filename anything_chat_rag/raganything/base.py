from enum import Enum
# type: ignore  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002VldseE1nPT06NjBlNDBkYmQ=


class DocStatus(str, Enum):
    """Document processing status"""

    READY = "ready"
    HANDLING = "handling"
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
# type: ignore  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002VldseE1nPT06NjBlNDBkYmQ=
