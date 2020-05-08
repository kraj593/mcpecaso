import setuptools

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name='mcpecaso',
    version='1.0.0',
    packages=setuptools.find_packages(),
    url='www.github.com/kraj593/mcpecaso',
    license='',
    author='Kaushik Raj',
    author_email='kraj593@gmail.com',
    description='Two stage fermentation simulator to predict optimal operating points.',
    install_requires=requirements,
)
