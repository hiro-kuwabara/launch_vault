from setuptools import setup

requirements = ['docker',
                'requests',
                'argparse'
               ]

setup(
    name='launch_vault',
    description='Launches and automatically configures Vault docker container.',
    author='Hiro K',
    version='1.0',
    install_requires=requirements,
    packages=['launch_vault'],
    entry_points={'console_scripts': ['launch_vault = launch_vault.launch_vault:main']}
)
