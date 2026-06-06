"""
Constants for the Kinect camera data, specific to the Living Lab pickle replay.
"""

KINECT_JOINT_NAMES = [
    'pelvis', 'spine - navel', 'spine - chest', 'neck',
    'left clavicle', 'left shoulder', 'left elbow', 'left wrist',
    'left hand', 'left handtip', 'left thumb',
    'right clavicle', 'right shoulder', 'right elbow', 'right wrist',
    'right hand', 'right handtip', 'right thumb',
    'left hip', 'left knee', 'left ankle', 'left foot',
    'right hip', 'right knee', 'right ankle', 'right foot',
    'head', 'nose', 'left eye', 'left ear', 'right eye', 'right ear',
]

KINECT_LIMB_CONNECTIONS = [
    ('pelvis', 'spine - navel'),
    ('spine - navel', 'spine - chest'),
    ('spine - chest', 'neck'),
    ('neck', 'head'),
    ('spine - chest', 'left clavicle'),
    ('left clavicle', 'left shoulder'),
    ('left shoulder', 'left elbow'),
    ('left elbow', 'left wrist'),
    ('left wrist', 'left hand'),
    ('left hand', 'left handtip'),
    ('left hand', 'left thumb'),
    ('spine - chest', 'right clavicle'),
    ('right clavicle', 'right shoulder'),
    ('right shoulder', 'right elbow'),
    ('right elbow', 'right wrist'),
    ('right wrist', 'right hand'),
    ('right hand', 'right handtip'),
    ('right hand', 'right thumb'),
    ('pelvis', 'left hip'),
    ('left hip', 'left knee'),
    ('left knee', 'left ankle'),
    ('left ankle', 'left foot'),
    ('pelvis', 'right hip'),
    ('right hip', 'right knee'),
    ('right knee', 'right ankle'),
    ('right ankle', 'right foot'),
]

KINECT_KPT_DIMS = ['px', 'py', 'pz', 'conf']
