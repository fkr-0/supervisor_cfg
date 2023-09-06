[![CircleCI](https://dl.circleci.com/status-badge/img/gh/fkr-0/supervisor_cfg/tree/master.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/fkr-0/supervisor_cfg/tree/master)
[![Docs]Docs](https://fkr-0.github.io/supervisor_cfg/)

# supervisor-cfg

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
- [Exposed Methods](#exposed-methods)
- [Contribution](#contribution)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Introduction

`supervisor-cfg` is a [Supervisor](https://supervisord.org) plugin designed to provide
functionalities for persistent manipulation of Supervisor's configuration file using
supervisors xml-rpc interface. The design of this project is closely following the
design of the [supervisor_twiddler
plugin](https://github.com/mnaberez/supervisor_twiddler).
[Docs.](https://fkr-0.github.io/supervisor_cfg/)

## Todo

- `Usage` docs
- Also allow using conf dir as "backend" for config file
- more Tests

## Installation

~~Follow the standard Supervisor plugin installation guidelines.~~

This project is not yet available on PyPI. You can install it by cloning the repository
and running `pip install .` in the root directory.

## Features

- Get and set the Supervisor configuration file.
- Whitelist functionalities.
- Modify specific sections or commands for Supervisor programs and persist the changes.

# Usage

#TODO

## Contribution

If you would like to contribute to this Supervisor plugin, please feel free to submit a pull request, create an issue, or fork the repository.

## Acknowledgments

- Thanks to the [Supervisor](https://supervisord.org) project for a great daemon manager.
- Thanks to the [supervisor_twiddler](https://github.com/mnaberez/supervisor_twiddler) plugin for inspiration.
- Anyone whose code was used.

## License

This project is licensed under the MIT License

```
The MIT License (MIT)

Copyright (c) 2023

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

```
