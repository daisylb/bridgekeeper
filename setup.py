from setuptools import find_packages, setup

setup(
    name='bridgekeeper',
    description='Django permissions, but with QuerySets',
    url='https://bridgekeeper.readthedocs.io/',
    author='Adam Brenecki',
    author_email='adam@brenecki.id.au',
    license='MIT',
    setup_requires=["setuptools_scm>=1.11.1"],
    use_scm_version=True,
    packages=find_packages(),
    include_package_data=True,

    install_requires=[
    ],
    extras_require={
        'dev': [
            'djangorestframework',
            'pytest',
            'pytest-django',
            'pytest-pythonpath',
            'prospector',
            'factory-boy~=2.9.2',
            'sphinx==1.6.5',
            'sphinx-rtd-theme==0.2.4',
        ]
    },
    entry_points={
        'console_scripts': ['bridgekeeper=bridgekeeper.cli:main.start'],
    },
)
