from setuptools import find_packages, setup

setup(
    name='bridgekeeper',
    description='My awesome project',
    url='https://example.com/',
    author='Adam Brenecki',
    author_email='abrenecki@cmv.com.au',
    license='Proprietary',
    setup_requires=["setuptools_scm>=1.11.1"],
    use_scm_version=True,
    packages=find_packages(),
    include_package_data=True,

    install_requires=[
        'begins',
    ],
    extras_require={
        'dev': [
            'pytest',
            'prospector',
        ]
    },
    entry_points={
        'console_scripts': ['bridgekeeper=bridgekeeper.cli:main.start'],
    },
)
