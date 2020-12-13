# wsl-tool

Handy classes for WSL management.

Inspired by [GWSL](https://opticos.github.io/gwsl/),
a great work from [Pololot64](https://github.com/Pololot64),
this project is a wrapper around the WSL executable to:

- check if WSL is installed;
- list and access the installed distribution;
- import new distribution from tarball files;
- run commands inside a distribution;
- read and set known environment variables in the user `.profile`;
- get the installed apps (that have a .desktop entry).

```python

from wsl_tools import wsl_tools

manager = wsl_tools.WSLManager()

```

For more information read the reference documentation.

## contributing

Contributions are welcome! See [contributing](CONTRIBUTING.md).
