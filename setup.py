from distutils.core import setup
setup(
  name = 'bkepub',         # How you named your package folder (MyLib)
  packages = ['bkepub'],   # Chose the same as "name"
  version = '0.7',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Create and manipulate ePub3 files',   # Give a short description about your library
  author = 'José fernando Tavares',                   # Type in your name
  author_email = 'fernando@booknando.com.br',      # Type in your E-Mail
  url = 'https://github.com/JFTavares/bkepub',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/JFTavares/bkepub/releases/tag/v.0.0.1',    # I explain this later on
  keywords = ["epub", "ebook", "publish", "xml", "epub3", "markdown", "parser", "generator"],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          "lxml>=4.6",       # Necessário para parsing robusto e geração de XML
        "Markdown>=3.3",
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package

    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',

    'License :: OSI Approved :: MIT License',   # Again, pick a license

    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)