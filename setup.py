from setuptools import setup

setup(
    name='swip',
    version="0.1.1",
    description='SignWriting Images in Python',
    long_description=open("README.md").read().split('##')[0],
    author='Gereon Kaiping',
    author_email='g.a.kaiping@hum.leidenuniv.nl',
    url='https://github.com/Anaphory/swip',
    install_requires=[
        # 'sqlite3',
    ],
    include_package_data=True,
    license="MIT",
    zip_safe=False,
    keywords='',
    classifiers=[
        ],
    packages=[
        'swip'],
    entry_points={
        'console_scripts': [
            'swip=swip.__main__:main',
            'swflashcards=swip.swflashcards:main',
        ]
    },
    tests_require=['nose'],
)
