from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()
with open("LICENSE") as f:
    license = f.read()
setup(
    name="tasks_pipeline",
    version="1",
    description="A curses CLI tasks pipeline",
    long_description=readme,
    author="Hélio Santos",
    author_email="heliosantos99@gmail.com",
    url="",
    install_requires=["pyyaml", "windows-curses"],
    license=license,
    packages=find_packages(exclude=("tests", "docs")),
)
