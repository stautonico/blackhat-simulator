# Contributing to Transcriptase

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github

We use github to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html), So All Code Changes Happen Through Pull Requests

Pull requests are the best way to propose changes to the codebase (we
use [Github Flow](https://guides.github.com/introduction/flow/index.html)). We actively welcome your pull requests:

1. Fork the repo and create your branch from `master`.
2. If you've added code that should be tested, add tests.
3. If you've changed any code that has docstrings, update the documentation.
4. Ensure the test suite passes.
5. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the
same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the
maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/stautonico/blackhat-simulator/issues)

We use GitHub issues to track public bugs. Report a bug
by [opening a new issue](https://github.com/stautonico/blackhat-simulator/issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
    - Be specific!
    - Give sample code if you can. (what code were you running that caused an issue)
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Use a Consistent Coding Style

* Function and variable names use snake case (`user_id`) (`get_all_user_ids()`)
* Class names should use CapWords (`SysCallStatus`) (`RouterISP`)
* Python's [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide should be followed (loosely enforced because
  everyone's interpretation is different)
* 4 spaces are used rather than tabs (most editors give you the option) (I hit tab and pycharm inserts 4 spaces for me)
* Make sure you sufficiently comment your code
    * Comment anything that might require **ANY** explication
    * If you're not sure if you should comment something, just do it. It's significantly easier to remove unnecessary
      comments than it is to try to figure out how some uncommented code works after the fact.
* Note: Some pieces of code (specifically the `lib` folder in blackhat contains code that intentionally tries to
  replicate the functionality of their c++ equivalents. These modules don't follow the coding guidelines that well, but
  this is intentional to maintain realism.)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## References

This document was adapted from the open-source contribution guidelines
for [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md)
