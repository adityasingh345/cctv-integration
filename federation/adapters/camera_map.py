"""
Maps each vendor's camera identifier to a camera_id in YOUR registry.
Vendor VMS platforms use their own camera names; this is where we say
"Vendor A's camera A-01 is actually camera_id 2 in our system."

Adjust the numbers on the right to match real ids from GET /cameras.
(Your sample registry has ids 2..6 for KNP-TRAF-001..005.)
"""
CAMERA_MAP = {
    # Vendor A cameras
    "A-01": 2,
    "A-02": 3,
    "A-03": 4,
    # Vendor B cameras
    "CAM_B_7": 4,
    "CAM_B_8": 5,
    "CAM_B_9": 6,
}

def resolve(vendor_cam: str):
    """Return the registry camera_id for a vendor camera code, or None."""
    return CAMERA_MAP.get(vendor_cam)