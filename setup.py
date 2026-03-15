"""Package configuration for the medical imaging coursework repository."""

from setuptools import find_packages, setup


INSTALL_REQUIRES = [
    "numpy==2.2.6",
    "scipy==1.15.3",
    "scikit-image==0.25.2",
    "matplotlib==3.10.8",
    "pandas==2.3.3",
    "PyYAML==6.0.3",
    "tqdm==4.67.3",
]

EXTRAS_REQUIRE = {
    "dev": ["pytest==9.0.2"],
    "notebooks": [
        "ipykernel==7.2.0",
        "jupyterlab==4.5.6",
    ],
}


setup(
    name="medical-imaging-coursework",
    version="0.1.0",
    description="Coursework code for CT reconstruction and MRI denoising experiments.",
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    python_requires=">=3.10,<3.13",
)
