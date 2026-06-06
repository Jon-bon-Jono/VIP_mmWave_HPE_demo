"""Conversions between pure Python replay objects and ROS messages."""

from __future__ import annotations

from typing import Optional

import numpy as np
from builtin_interfaces.msg import Time

from vip_hpe_msgs.msg import (
    RadarPoint,
    RadarFrame,
    Joint3D,
    PersonPose3D,
    PersonPose3DArray,
)

from vip_hpe_core.constants.kinect import KINECT_JOINT_NAMES
from vip_hpe_runtime.replay.living_lab import LivingLabFrame


def now_to_header(node, frame_id: str):
    """Create a std_msgs/Header from a node clock."""
    header = node.get_clock().now().to_msg()
    # Caller fills Header object directly in message constructors below.
    return header


def stamp_from_node(node) -> Time:
    return node.get_clock().now().to_msg()


def frame_to_radar_msg(frame: LivingLabFrame, node, frame_id: str = 'radar_link') -> RadarFrame:
    msg = RadarFrame()
    msg.header.stamp = stamp_from_node(node)
    msg.header.frame_id = frame_id
    msg.frame_index = int(frame.frame_index)
    msg.source_timestamp = float(frame.source_timestamp)

    points = []
    for row in frame.pc:
        p = RadarPoint()
        p.x = float(row[0])
        p.y = float(row[1])
        p.z = float(row[2])
        p.doppler = float(row[3])
        p.snr = float(row[4])
        p.target_id = int(row[5])
        points.append(p)
    msg.points = points
    return msg


def frame_to_pose_msg(frame: LivingLabFrame, node, frame_id: str = 'radar_link') -> PersonPose3DArray:
    msg = PersonPose3DArray()
    msg.header.stamp = stamp_from_node(node)
    msg.header.frame_id = frame_id
    msg.frame_index = int(frame.frame_index)
    msg.source_timestamp = float(frame.source_timestamp)

    pose = frame.poses_3d_gt
    if pose is None:
        msg.people = []
        return msg

    people = []
    for person_idx in range(pose.shape[0]):
        person = PersonPose3D()
        person.person_id = int(person_idx)
        joints = []
        for joint_idx, name in enumerate(KINECT_JOINT_NAMES):
            joint = Joint3D()
            joint.name = name
            joint.x = float(pose[person_idx, joint_idx, 0])
            joint.y = float(pose[person_idx, joint_idx, 1])
            joint.z = float(pose[person_idx, joint_idx, 2])
            joint.confidence = float(pose[person_idx, joint_idx, 3]) if pose.shape[-1] >= 4 else 1.0
            joints.append(joint)
        person.joints = joints
        people.append(person)
    msg.people = people
    return msg


def radar_msg_to_numpy(msg: RadarFrame) -> np.ndarray:
    arr = np.zeros((len(msg.points), 6), dtype=np.float32)
    for i, p in enumerate(msg.points):
        arr[i] = [p.x, p.y, p.z, p.doppler, p.snr, p.target_id]
    return arr


def pose_msg_to_numpy(msg: PersonPose3DArray) -> Optional[np.ndarray]:
    if not msg.people:
        return None
    n_people = len(msg.people)
    n_joints = len(msg.people[0].joints)
    arr = np.zeros((n_people, n_joints, 4), dtype=np.float32)
    for p_idx, person in enumerate(msg.people):
        for j_idx, joint in enumerate(person.joints):
            arr[p_idx, j_idx] = [joint.x, joint.y, joint.z, joint.confidence]
    return arr
