from setuptools import setup, find_packages

NAME = "receipt_generator"
VERSION = "1.0.0"

REQUIRES = ["Pillow", "qrcode"]

setup(
    name=NAME,
    version=VERSION,
    description="Receipt generator for FerryTix Receipts.",
    author_email="hendrik.lankers.hl@googlemail.com",
    url="https://github.com/ferrytix/receipt_generator",
    keywords=["Receipts", "FerryTix"],
    install_requires=REQUIRES,
    packages=find_packages(),
    include_package_data=True,
    long_description=open('README.md').read()
)
