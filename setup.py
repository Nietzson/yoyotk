from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="yoyotk",
    version="0.1",
    author="https://github.com/Nietzson",
    author_email="yvigouroux@telecom-paris.fr",
    description="Toolbix for medical image processing",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Nietzson/yoyotk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8.10",
    install_requires=requirements,
)
