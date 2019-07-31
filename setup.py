#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    setup,
    find_packages,
)

extras_require = {
    'test': [
        "pexpect>=4.7.0,<5",
        "pytest>=4.4.0,<5",
        "pytest-xdist>=1.29,<2",
        "tox>=2.9.1,<3",
    ],
    'lint': [
        "black>=19.3b0,<20",
        "flake8>=3.7.0,<4",
        "isort>=4.3.17,<5",   
        "mypy<0.800",
        "pydocstyle>=3.0.0,<4",
    ],
    'doc': [
        "Sphinx>=1.6.5,<2",
        "sphinx_rtd_theme>=0.1.9",
        "sphinx-argparse>=0.2.5,<1",
    ],
    'dev': [
        "bumpversion>=0.5.3,<1",
        "pytest-watch>=4.1.0,<5",
        "wheel",
        "twine",
        "ipython",
    ],
}

extras_require['dev'] = (
    extras_require['dev'] +
    extras_require['test'] +
    extras_require['lint'] +
    extras_require['doc']
)

setup(
    name='ethpm-cli',
    # *IMPORTANT*: Don't manually change the version here. Use `make bump`, as described in readme
    version='0.1.0-alpha.3',
    description="""ethpm-cli: CLI for EthPM""",
    long_description_markdown_filename='README.md',
    author='The Ethereum Foundation',
    author_email='snakecharmers@ethereum.org',
    url='https://github.com/ethereum/ethpm-cli',
    include_package_data=True,
    install_requires=[
        "eth-hash[pysha3]>=0.2.0,<1",
        "web3[tester]>=5.0.0b4,<6",
    ],
    setup_requires=['setuptools-markdown'],
    python_requires='>=3.6, <4',
    extras_require=extras_require,
    py_modules=['ethpm_cli'],
    license="MIT",
    zip_safe=False,
    keywords='ethereum',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    entry_points={
        'console_scripts': [
            'ethpm=ethpm_cli:main',
        ],
    },
)
