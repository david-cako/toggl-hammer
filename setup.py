from setuptools import setup

setup(name='toggl_hammer',
      version='0.2',
      description='toggl for lazy people.',
      url='https://github.com/david-cako/toggl-hammer',
      author='david cako',
      author_email='dc@cako.io',
      license='GPL',
      packages=['toggl_hammer'],
      entry_points={
          "console_scripts": ['toggl_hammer = toggl_hammer.toggl_hammer:main']
      },
      install_requires=[
          'requests',
          'holidays'
      ]
)

