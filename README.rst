repex
=====

-  Master Branch |Build Status|
-  PyPI |PyPI|
-  Version |PypI|

``repex`` replaces strings in single/multiple files based on regular
expressions.

Why not use sed you ask? Because ``repex`` provides some layers of
protection and an easy to use config yaml in which you easily add new
files and folders to iterate through.

The layers are: \* Match and only then replace in the matched regular
expression. \* Check for existing strings in a file before replacing
anything. \* Exclude files and folders so that you don't screw up.

AND, you can use variables (sorta jinja2 style). How cool is that? See
reference config below.

Installation
~~~~~~~~~~~~

.. code:: shell

    pip install repex

For dev:

.. code:: shell

    pip install https://github.com/cloudify-cosmo/repex/archive/master.tar.gz

Usage
~~~~~

Let's say you have files named "VERSION" in different directories which
look like this:

.. code:: json

    {
      "date": "",
      "commit": "",
      "version": "3.1.0-m2",
      "version_other": "3.1.2-m1",
      "build": "8"
    }

And you'd like to replace 3.1.0-m2 with 3.1.0-m3 in all of those files

You would create a repex config.yaml with the following:

.. code:: yaml


    variables:
        base_dir: .

    paths:
        -   type: VERSION
            path: resources
            excluded:
                - excluded_file.file
            base_directory: "{{ .base_dir }}"
            match: '"version": "\d+\.\d+(\.\d+)?(-\w\d+)?'
            replace: \d+\.\d+(\.\d+)?(-\w\d+)?
            with: "{{ .version }}"
            validate_before: true
            must_include:
                - date
                - commit
                - version
            validator:
                type: per_file
                path: my/validator/script/path.py
                function: my_validation_function

and do the following

.. code:: python


    import os
    import repex.repex as rpx

    CONFIG_YAML_FILE = "tester.yaml"
    VERSION = os.environ['VERSION']  # '3.1.0-m3'

    variables = {
        'version': VERSION,
    }

    rpx.iterate(CONFIG_YAML_FILE, variables)

and even add a validator file:

.. code:: python


    def my_validation_function(version_file_path):
        result = verify_replacement()
        return True if result else False

Config yaml Explained
^^^^^^^^^^^^^^^^^^^^^

IMPORTANT NOTE: variables MUST be enclosed within single or double
quotes or they will not expand! Might fix that in future versions...

ANOTHER IMPORTANT NOTE: variables must be structured EXACTLY like this:
{{ .VER\_NAME }} Don't forget the spaces!

-  ``variables`` is a dict of variables you can use throughout the
   config. ``type``, ``path``, ``base_directory``, ``match``,
   ``replace`` and ``with`` can all receive variables. For now, all
   attributes which are not strings cannot receive variables. This might
   change in future versions. ``variables`` can be sent to one of the 3
   basic functions described below or by being hardcoded into the yaml.
   Variables with the same name sent via the API will override the
   hardcoded ones.
-  ``type`` is a regex string representing the file name you're looking
   for.
-  ``path`` is a regex string representing the path in which you'd like
   to search for files (so, for instance, if you only want to replace
   files in directory names starting with "my-", you would write
   "my-.\*"). If ``path`` is a path to a single file, the ``type``
   attribute must not be configured.
-  ``excluded`` is a list of excluded paths. The paths must be relative
   to the working directory, NOT to the ``path`` variable.
-  ``base_directory`` is the directory from which you'd like to start
   the recursive search for files. If ``path`` is a path to a file, this
   property can be omitted. Alternatively, you can set the
   ``base_directory`` and a ``path`` relative to it.
-  ``match`` is the initial regex based string you'd like to match
   before replacing the expression. This provides a more robust way to
   replace strings where you first match the exact area in which you'd
   like to replace the expression and only then match the expression you
   want to replace within it. It also provides a way to replace only
   specific instances of an expression, and not all.
-  ``replace`` - which regex would you like to replace?
-  ``with`` - what you replace with.
-  ``validate_before`` - a flag stating that you'd like to validate that
   the pattern you're looking for exists in the file and that all
   strings in ``must_include`` exists in the file as well.
-  ``must_include`` - as an additional layer of security, you can
   specify a set of regex based strings to look for to make sure that
   the files you're dealing with are the actual files you'd like to
   replace the expressions in.
-  ``validator`` - validator allows you to run a validation function
   after replacing expressions. It receives ``type`` which can be either
   ``per_file`` or ``per_type`` where ``per_file`` runs the validation
   on every file while ``per_type`` runs once for every ``type`` of
   file; it receives a ``path`` to the script and a ``function`` within
   the script to call. Note that each validation function must return
   ``True`` if successful and ``False`` if failed. The validating
   function receives the file's path as a parameter.

In case you're providing a path to a file rather than a directory:

-  ``type`` and ``base_directory`` are depracated
-  you can provide a ``to_file`` key with the path to the file you'd
   like to create after replacing.

Basic Functions
^^^^^^^^^^^^^^^

3 basic functions are provided:

The following examples all perform the exact same function (``iterate``)
but using the different provided methods for the sake of granularity.

Note that under normal circumstanaces, you will not need to drill down
into these and just use ``iterate``.

iterate
'''''''

Receives the config yaml file and the variables dict and iterates
through the config file's ``paths`` list destroying everything that
comes in its path :)

.. code:: python


    import os
    import repex.repex as rpx

    CONFIG_YAML_FILE = "tester.yaml"
    VERSION = os.environ['VERSION']  # '3.1.0-m3'
    VERBOSE = True

    variables = {
        'version': VERSION,
        'base_dir': .
    }

    rpx.iterate(CONFIG_YAML_FILE, variables, verbose=VERBOSE)

handle\_path
''''''''''''

Receives one of the objects in the ``paths`` list in the config yaml
file and the variables dict, finds all files of name ``type`` and
processes them (is used by ``iterate``).

.. code:: python


    import os
    import repex.repex as rpx

    CONFIG_YAML_FILE = "tester.yaml"
    VERSION = os.environ['VERSION']  # '3.1.0-m3'
    VERBOSE = True

    variables = {
        'version': VERSION,
        'base_dir': .
    }

    # this is what iterate would do if it was called directly
    config = rpx.import_config(CONFIG_YAML_FILE)
    vars = config.get('variables', {})
    vars.update(variables)
    for p in config['paths']:
        rpx.handle_path(p, vars, verbose=VERBOSE)

handle\_file
''''''''''''

Receives one of the objects in the ``paths`` list in the config yaml
file and the variables dict, and processes the specific file specified
in the ``path`` key (used by ``handle_path``).

IMPORTANT:

-  Variable expansion occurs only in ``handle_path``. Therefore, if
   variables exist, we must manually call the variable expansion method.
-  The ``path`` attribute in each object must be a path to a file.
-  ``get_all_files`` will find all files with name ``type`` in ``path``
   from dir ``base_directory``, excluding ``excluded``.

.. code:: python


    import os
    import repex.repex as rpx


    CONFIG_YAML_FILE = "tester.yaml"
    VERSION = os.environ['VERSION']  # '3.1.0-m3'
    VERBOSE = True

    variables = {
        'version': VERSION,
        'base_dir': .
    }

    # this is what iterate would do if it was called directly
    config = rpx.import_config(CONFIG_YAML_FILE)
    vars = config.get('variables', {})
    vars.update(variables)
    for p in config['paths']:
        files = get_all_files(
            p['type'], p['path'], p['base_directory'], p['excluded'], , verbose=VERBOSE)
        # this will run the validator if applicable.
        _validate(p['path'])
        # this is what handle_path would do if it was called directly
        var_expander = rpx.VarHandler(p)
        p = var_expander.expand(variables)
        for file in files:
            p['path'] = file
            rpx.handle_file(file, vars, verbose=VERBOSE)

.. |Build Status| image:: https://travis-ci.org/cloudify-cosmo/repex.svg?branch=master
   :target: https://travis-ci.org/cloudify-cosmo/repex
.. |PyPI| image:: http://img.shields.io/pypi/dm/repex.svg
   :target: http://img.shields.io/pypi/dm/repex.svg
.. |PypI| image:: http://img.shields.io/pypi/v/repex.svg
   :target: http://img.shields.io/pypi/v/repex.svg
