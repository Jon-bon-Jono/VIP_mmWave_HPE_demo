from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'vip_hpe_runtime'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Jonathan Williams',
    maintainer_email='jonathan.williams@student.unsw.edu.au',
    description='Runtime skeleton for VIP mmWave HPE replay, inference stubs, and visualisation.',
    license='UNSW',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'radar_replay_node = vip_hpe_runtime.nodes.radar_replay_node:main',
            'pose_gt_replay_node = vip_hpe_runtime.nodes.pose_gt_replay_node:main',
            'animated_plot_node = vip_hpe_runtime.nodes.animated_plot_node:main',
            'live_model_inference_node = vip_hpe_runtime.nodes.live_model_inference_node:main',
        ],
    },
)
