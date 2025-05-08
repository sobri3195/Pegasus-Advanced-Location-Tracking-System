from setuptools import setup, find_packages

setup(
    name="location-tracker-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.0",
        "requests>=2.25.1",
        "python-dateutil>=2.8.2",
        "python-dotenv>=1.0.0",
    ],
    author="Muhammad Sobri Maulana",
    author_email="muhammadsobrimaulana31@gmail.com",
    description="Telegram bot for tracking locations",
    keywords="telegram, bot, location, tracking",
    python_requires=">=3.8",
) 