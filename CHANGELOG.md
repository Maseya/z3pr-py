# Changelog

## v1.0.0-dev6 Add new blend modes

* Update missing/wrong information in README and correct some typos.
* Add `--data-dir` compiler flag to specify custom directory to JSON
  offset files.
* Remove FAQ file, which was an artifact of a different project.
* Remove reference to this being a C# project (left over from the port).
* Add "dizzy", "sick", and "puke" modes, which randomize colors with
  increasingly less logic.
* Add "classic" mode, which loosely emulates the original alttpr's
  palette shuffle code. This should give you a bit more variety in
  color output which will be less visually appealing, if you're into
  that sort of thing.
* Remove ability to store default commands in config file. It only made
  getting commands harder, and a clever user can make their own script
  files to the same effect.
* Fix `ColorF.saturation` function using `and` where `or` should have
  been used.
* Add `hue_blend`, `chroma_blend`, and `luma_blend` functions in
  `ColorF` class, which replaces one HCY component of one color with
  another.
* Add `ColorF.__hash__` function.
* Add `acid_blend` function, which attempts to mimic the original
  palette shuffle code. Some people have referred to the original
  output as "acid colors", hence the name.

## v1.0.0-dev5

* Release testable dev release.

## v1.0.0-dev1

* Create test dev release.

## v0.9.1

* Fix Dark World Death Mountain reference address.
* Let user enter file paths if none were supplied.

## v0.9.0 Preview release

Tasks left before full release:

* There's a ground palette that exists during lightning flashes in Dark
  World Death Mountain that I cannot find.
