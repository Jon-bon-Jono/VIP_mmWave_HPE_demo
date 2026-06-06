from setuptools import find_packages, setup

package_name = "vip_hpe_core"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(exclude=['test']),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer='Jonathan Williams',
    maintainer_email='jonathan.williams@student.unsw.edu.au',
    description="Shared ROS-free preprocessing and dataset utilities for VIP mmWave HPE.",
    license="UNSW",
)