import numpy as np
from pathlib import Path
import pickle
import matplotlib.pyplot as plt

OOB_TID = 254
NOISE_TARGET_IDS = [253, OOB_TID, 255]

ROOM_BOUNDS = [
    [-3.9, 2.6], #x1,x2
    [0.8799999999999999, 4.922562584220408],  #y1,y2
    [-1.524204710660612, 4.273871500692704],  #z1,z2
]

KINECT_JOINT_NAMES = ['pelvis','spine - navel','spine - chest','neck','left clavicle','left shoulder','left elbow','left wrist','left hand','left handtip','left thumb','right clavicle','right shoulder','right elbow','right wrist','right hand','right handtip','right thumb','left hip','left knee','left ankle','left foot','right hip','right knee','right ankle','right foot','head','nose','left eye','left ear','right eye','right ear']
KINECT_LIMB_CONNECTIONS = [
    ('pelvis', 'spine - navel'),('spine - navel', 'spine - chest'),('spine - chest', 'neck'),('neck', 'head'),
    # Left arm
    ('spine - chest', 'left clavicle'),('left clavicle', 'left shoulder'),('left shoulder', 'left elbow'),('left elbow', 'left wrist'),('left wrist', 'left hand'),('left hand', 'left handtip'),('left hand', 'left thumb'),
    # Right arm
    ('spine - chest', 'right clavicle'),('right clavicle', 'right shoulder'),('right shoulder', 'right elbow'),('right elbow', 'right wrist'),('right wrist', 'right hand'),('right hand', 'right handtip'),('right hand', 'right thumb'),
    # Left leg
    ('pelvis', 'left hip'),('left hip', 'left knee'),('left knee', 'left ankle'),('left ankle', 'left foot'),
    # Right leg
    ('pelvis', 'right hip'),('right hip', 'right knee'),('right knee', 'right ankle'),('right ankle', 'right foot'),
]

KINECT_KPT_DIMS = ["px", "py", "pz", "conf"]

def _3d_pose_to_pc(poses, scale=1e-3):
    """
    Turn poses of shape (N_people, N_joints, 3) in (x,y,z) meters
    into (x, z, -y) in the same shape, all scaled to meters.
    """
    # poses[...,0]=x, [...,1]=y, [...,2]=z
    out = poses[..., [0, 2, 1]]  # (x, z, y)
    out[..., 2] *= -1.0          # (x, z, -y)
    out *= scale                  # mm -> m
    return out

class LivingLabFrameReplay:
    def __init__(self, frame, gtrack_filtering=True):
        self.frame = frame
        self.gtrack_filtering = gtrack_filtering
        self.parse_pc()
        self.parse_3d_gt_pose()
        
    def parse_pc(self):
        self.pc = self.frame['pc']
        if self.gtrack_filtering:
            target_ids = self.pc[:,5]
            mask_noise = np.isin(target_ids, NOISE_TARGET_IDS)
            self.pc = self.pc[~mask_noise]
        self.px, self.py, self.pz, self.pd, self.ps, self.tid = self.pc.T
    
    def parse_3d_gt_pose(self):
        poses3d = self.frame['poses3d']
        if poses3d is None or poses3d.shape[0] == 0:
            self.poses_3d_gt = None
            return
        P = poses3d.reshape(-1, len(KINECT_JOINT_NAMES), len(KINECT_KPT_DIMS))
        self.poses_3d_gt = _3d_pose_to_pc(P)

class LivingLabSubjectReplay:

    def __init__(self, path):
        self.path = path
        self.load_pickled_subject()
        

    def load_pickled_subject(self):
        with open(self.path, 'rb') as handle:
            self.data = pickle.load(handle)

    def __getitem__(self, idx):
        return LivingLabFrameReplay(self.data[idx])
    
class PosePointCloud3dPlot:
    def __init__(self, figsize=(8,6), boundless=False, pc_alpha=0.1):
        self.figsize = figsize 
        self.boundless = boundless
        self.pc_alpha = pc_alpha
        self.fig = plt.figure(figsize=figsize)
        self.ax  = self.fig.add_subplot(111, projection='3d')
        self.ax.set_title("mmWave 3D Point Cloud w Human Pose")
        self.ax.set_xlabel("x (m)")
        self.ax.set_ylabel("y (m)")
        self.ax.set_zlabel("z (m)")

    def plot_frame(self, frame: LivingLabFrameReplay):
        self.ax.scatter(frame.px, frame.py, frame.pz, c='r', s=1, alpha=self.pc_alpha)
        P = frame.poses_3d_gt
        if P is not None:
            # scatter all joints
            self.ax.scatter(P[...,0].ravel(), P[...,1].ravel(), P[...,2].ravel(), c='b', s=5)
            # draw bones
            name_to_idx = {n: i for i, n in enumerate(KINECT_JOINT_NAMES)}
            for person in range(P.shape[0]):
                for l, r in KINECT_LIMB_CONNECTIONS:
                    i, j = name_to_idx[l], name_to_idx[r]
                    self.ax.plot([P[person, i, 0], P[person, j, 0]],
                            [P[person, i, 1], P[person, j, 1]],
                            [P[person, i, 2], P[person, j, 2]],
                            c='b', linewidth=1)
        if not self.boundless:
            self.ax.set_xlim(*ROOM_BOUNDS[0])
            self.ax.set_ylim(*ROOM_BOUNDS[1])
            self.ax.set_zlim(*ROOM_BOUNDS[2])
        plt.show()



if __name__ == "__main__":
    root = Path("data/ll_replay")
    srp = root / "07_SW.pickle"
    llsr = LivingLabSubjectReplay(srp)
    llfr = llsr[35000]
    plotter = PosePointCloud3dPlot()
    plotter.plot_frame(llfr)

