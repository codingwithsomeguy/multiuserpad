from setuptools import setup, find_packages


setup(
    name="multiuserpad",
    version="0.1",
    description="collaborative / learning developer environment",
    author="codingwithsomeguy",
    url="https://codingwithsomeguy.com/",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
)
