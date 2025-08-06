from setuptools import setup, find_packages

setup(
    name="ForeclosureAutomationSystem",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A system to automate the processing of foreclosure notice emails from Gmail.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Rebalida/foreclosure-notice-automation",
    packages=find_packages(),
    include_package_data=True,
    install_requires=open('requirements.txt').read().splitlines(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'foreclosure-automation=main:main',
        ],
    },
)
