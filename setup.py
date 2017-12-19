from setuptools import setup, find_packages

setup(
  name="pshaw",
  version="0.1",
  packages="pshaw".split(),

  author="Tim Cooijmans",
  author_email="lastname.firstname@gmail.com",
  description="An sshpass wrapper with password persistence.",
  license="BSD-3-Clause",
  url="https://github.com/cooijmanstim/pshaw",

  entry_points=dict(console_scripts=[
    "pshaw = pshaw.pshaw:main",
    "pshawd = pshaw.pshawd:main",
  ]),

  install_requires="""
    asyncssh
  """,
)
