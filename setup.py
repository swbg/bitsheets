from setuptools import find_packages, setup

setup(
    name="bitsheets",
    version="0.0.1",
    packages=find_packages("src"),
    package_dir={"": "src"},
    url="https://github.com/swbg/bitsheets",
    author="Stefan Weissenberger",
    description="Music parser for GB roms.",
    zip_safe=False,
)
