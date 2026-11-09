import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'reactive_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='student',
    maintainer_email='student@itu.edu.tr',
    description='Obstacle avoidance assignment',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'avoidance_node = reactive_robot.obstacle_avoidance:main',
        ],
    },
)
