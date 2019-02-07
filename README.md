<!---
Copyright (c) 2019 Michael Vilim

This file is part of the neovim-pytc-example. It is currently hosted at
https://github.com/mvilim/neovim-pytc-example

neovim-pytc-example is licensed under the MIT license. A copy of the license can be
found in the root folder of the project.
-->

## neovim-pytc-example

neovim-pytc-example is a Neovim terminal client implemented in Python (using libtermkey for input processing and curses for screen rendering). It reproduces the majority of the functionality of the integral Neovim terminal client. It serves no practical purpose, as no additional functionality is provided -- the project is just to demonstrate integration of the Neovim Python API into a curses terminal application.

### Comparison

Here you can see a comparison between the pytc client and a real nvim terminal client.

|  nvim  | neovim_pytc |
|--------|-------------|
| <img width="400" src="https://mvilim.github.io/neovim-pytc-example/img/nvim_capture.svg"> | <img width="400" src="https://mvilim.github.io/neovim-pytc-example/img/neovim_pytc_capture.svg"> |

### Features

Most Neovim features should be supported.

Known limitations include:
* command line arguments (exluding filename) are not forwarded to Neovim
* cursor style is not updated on mode change (as those cursor styles are not supported by curses)

### Installation

To install from the checkout directory:

```
pip install .
```

### Running neovim_pytc

The editor can be run in three ways:

Running the installed script:
`neovim_pytc [file]`

Directly running the source script:
`python neovim_pytc/neovim_pytc.py [file]`

Importing and running inside a python script:
`import neovim_pytc; neovim_pytc.run([file])`

### Licensing

This project is licensed under the [MIT license](https://github.com/mvilim/neovim-pytc-example/blob/master/LICENSE).
