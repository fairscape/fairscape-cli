from setuptools import setup, find_packages

setup(
    name='fairscape_cli',
    version='0.1.8',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
				'pydantic>=2.5.1',
				'prettytable>=3.9.0'
    ],
    entry_points={
        'console_scripts': [
            'fairscape-cli=fairscape_cli.__main__:cli',
        ],
    },
)