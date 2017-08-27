try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name = 'PttWebCrawler',
    packages = ['PttWebCrawler'],
    version = '1.4',
    description = 'ptt web crawler',
    author = '',
    author_email = '',
    url = 'https://github.com/jwlin/ptt-web-crawler',
    download_url = '',
    keywords = [],
    classifiers = [],
    license='MIT',
    install_requires=[
        'argparse',
        'beautifulsoup4',
        'requests',
        'six',
        'pyOpenSSL'
    ],
    entry_points={
        'console_scripts': [
            'PttWebCrawler = PttWebCrawler.__main__:main'
        ]
    },
    zip_safe=True
)
