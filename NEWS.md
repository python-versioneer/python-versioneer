## Release 0.19 (10-Nov-2020)

Versioneer's 0.19 release is the first under new maintainership, and most of the work
done has been maintenance along with a few features and bug fixes. No significant
changes to the mode of operation have been included here.

The current maintainers are Nathan Buckner, Yaroslav Halchenko, Chris Markiewicz,
Kevin Sheppard and Brian Warner.

* Drop support for Python < 3.6, test up to Python 3.9
* Strip GPG signature information from date (#222)
* Add `bdist_ext` cmdclass, to support native code extensions (#171)
* Canonicalize pep440-pre style (#163)
* Take arguments to `get_cmdclass`

## Release 0.18 (01-Jan-2017)

* switch to entrypoints to get the right executable suffix on windows (#131)
* update whitespace to appease latest flake8

Thanks to xoviat for the windows patch.
