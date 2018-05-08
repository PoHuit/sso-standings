# Character Standings Checker
Copyright (c) 2018 Po Huit

This code provides a couple of implementations of a lovely CCP
tutorial on EVE Online ESI SSO,
[*ESI Step By Step — SSO To Authenticated Calls*](https://developers.eveonline.com/blog/article/sso-to-authenticated-calls). Following
along with that tutorial is key to understanding this
codebase: it will likely make little sense read on its own.

There are two implementations here. The one in the `sh`
directory is essentially shell-script wrappers for the Linux
`curl` requests described in the tutorials. An occasional
`tee` and `aeson-pretty` (a JSON prettyprinter) are thrown
in for clarity. It's all pretty *ad hack*, and is mostly
preserving work I did interactively during an in-class
tutorial.

The more principled implementation, in `standings.py`, is a
command-line Python 3 client for displaying the standings of
a character as CSV. Again, it follows the CCP tutorial
closely, but with quite a bit of elaboration into a Python
app. It's definitely not ready for production use, but it's
close enough that the end should be visible from there.

## License

This program is licensed under the "MIT License".  Please
see the file `LICENSE` in the source distribution of this
software for license terms.
