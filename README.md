# wsl-tool

Handy classes for WSL management.

Inspired by [GWSL](https://opticos.github.io/gwsl/), a great work from [Pololot64](https://github.com/Pololot64)

## Classes

### WSLManager

`UserDict` that holds the installed WSL distributions.

It also has a few helper methods/properties to check if `wsl` is installed and import distributions from tarball files.

### WSLDistro

This class does the heavy lifting.

It mainly calls subprocess to run `wsl ~ -d distro-name sh -lc '....'`.
Running the commands via `sh -lc` gives us a broader distribution support,
and ensures that we can use and edit the user .profile file.

### WSLApp

Object holding the information found in the distro installed apps that have a xdg Desktop Entry.

It doesn't do much at the time.
