from setuptools import setup, find_packages

setup(
	name="fairscape_cli",
	version='0.1.14a1',
	description = "CLI tool for B2AI metadata validation and ROCrate creation",
	readme = "README.md",
	author = 'Max Levinson, Sadnan Al Manir, Tim Clark',
	author_email='mal8ch@virginia.edu, sadnanalmanir@gmail.com, twc8q@virginia.edu',
	license = "LICENSE",
	classifiers = [
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3"],
	keywords = ["fairscape", "reproducibility", "fair", "b2ai"],
	install_requires=[
		"click>=8.1.7",
		"pydantic>=2.5.1",
		"prettytable>=3.9.0",
		"imageio>=2.33.0",
		"jsonschema>=4.20.0",
		"pandas>=2.0.3",
		"pytest>=7.4.3",
		"sqids>=0.4.1",	
	],
	packages=find_packages(),
	package_dir= {"": "fairscape_cli"},
	include_package_data=True,
	entry_points={
		'console_points': [
			'fairscape-cli = fairscape_cli.__main__:cli'
		]
	}

)