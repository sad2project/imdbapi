import setuptools

setuptools.setup(
    name='imdbapi',
    version = '1.0',
    author = 'Jacob Zimmerman',
    author_email = 'jacobz_20@yahoo.com',
    description = 'A library for using the web api for IMDb',
    packages = setuptools.find_packages(exclude=['dist', 'imdbapi.egg-info', 'build', 'test']),
    classifiers = [
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',],
    python_requires = '>=3.8',
    #package_dir = {'':''},
    install_requires=['requests'],
)
