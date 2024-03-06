from setuptools import setup, find_packages

setup(
	name="fairscape_cli",
	version='0.1.14a3',
	description = "CLI tool for B2AI metadata validation and ROCrate creation",
	author = 'Max Levinson, Sadnan Al Manir, Tim Clark',
	author_email='mal8ch@virginia.edu, sadnanalmanir@gmail.com, twc8q@virginia.edu',
	license = "LICENSE",
	# project urls
	url= "https://github.com/fairscape/fairscape-cli",
	classifiers = [
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3"],
	keywords = ["fairscape", "reproducibility", "fair", "b2ai"],
	install_requires=[
		"click",
		"pydantic",
		"prettytable",
		"jsonschema",
		"pytest",
		"sqids>=0.4.1",	
	],
	packages=find_packages(where="src"),
	package_dir= {"": "src"},
	include_package_data=True,
	entry_points={
		'console_points': [
			'fairscape-cli = fairscape_cli.__main__:cli'
		]
	}

)