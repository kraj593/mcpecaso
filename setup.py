import setuptools

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name='tsdyssco',
    version='1.0.0',
    packages=setuptools.find_packages(),
    url='www.github.com/kraj593/tsdyssco',
    license='',
    author='Kaushik Raj',
    author_email='kraj593@gmail.com',
    description='Two stage fermentation simulator to predict optimal operating points.',
    install_requires=requirements,
)
