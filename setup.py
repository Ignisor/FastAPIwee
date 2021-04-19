import setuptools


with open("README.md", "r") as readme:
    long_description = readme.read()

with open("VERSION", "r") as version_f:
    version = version_f.read()

setuptools.setup(
    name="FastAPIwee",
    version=version,
    author="German Gensetskyi",
    author_email="Ignis2497@gmail.com",
    description="FastAPIwee - FastAPI + PeeWee = <3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ignisor/FastAPIwee",
    packages=setuptools.find_packages(exclude=('tests', )),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    install_requires=[
        'fastapi==0.63.0',
        'pydantic==1.8.1',
        'peewee==3.14.4',
    ]
)
