"""
Setup configuration for robotframework-LogXML2Chunks library.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the long description from README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='robotframework-logxml2chunks',
    version='1.1.0',
    author='Artur Jadach',
    author_email='artur.k.ziolkowski@example.com',
    description='Extract individual test cases from Robot Framework output.xml into separate chunks',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ajadach/robotframework-LogXML2Chunks',
    packages=find_packages(exclude=['tests', 'tests.*']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Robot Framework',
        'Framework :: Robot Framework :: Library',
    ],
    keywords='robotframework testing automation xml log chunks',
    python_requires='>=3.7',
    install_requires=[
        'robotframework>=4.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'logxml2chunks=LogXML2Chunks.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
