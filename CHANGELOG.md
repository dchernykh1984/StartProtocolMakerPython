# Changelog

## [0.1.1](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.1.0...v0.1.1) (2026-07-21)


### Bug Fixes

* reliable release builds (linux-aarch64 on ubuntu-24.04, drop Intel macOS) ([0983eb5](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0983eb582d019d8783f23520ae0dad1a3f406e9f))

## 0.1.0 (2026-07-21)


### Features

* cycling HTTP site integration for participant list download ([7ca8123](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/7ca8123feccfba1b2996ea71d4a59a4913ded761))
* migrate participants API to /api/v1/participants/ with competition_token ([#15](https://github.com/dchernykh1984/StartProtocolMakerPython/issues/15)) ([c47ee6a](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/c47ee6ad9695fba5235285edcf0a773ac16defae))
* persist a strictly-increasing client_revision counter for start-list uploads ([5438395](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/54383955851f643ffff8ca5939d1a2be4bec8035))
* port StartProtocolMaker from C++ to PySide6 ([49e8c8f](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/49e8c8fe84fede82f9399d6cf95de5f6fa5bd75f))
* resolve app data next to the executable for portable builds ([be403b5](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/be403b5820250de88dacdbe60ce6f79aac0b14ff))
* send a monotonic client_revision with start-list uploads ([6533af4](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/6533af49cb452348e2cae4378e1e4c27a042f9d5))
* send the start list to the site by token and device id ([40fa0bd](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/40fa0bd1cad7de8265aa4842006a230cb6a9ae28))
* set app name and icon at QApplication level for dock/taskbar ([1cb6590](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/1cb6590856c1b1e23408f98f273022da08e8331b))
* sync participant groups when loading from the site ([521ffd0](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/521ffd08c6191a6a31a9048b9cf0773d5b72d634))


### Bug Fixes

* carry each group's bib range from the site into the numbers list ([7aef163](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/7aef163e0209f4e84d983438284c5a82f3639305))
* clear groups on Replace when the site returns an empty group list ([e2d694a](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/e2d694a48e0daf4e3b80d944eb75c64d9cdd1ffe))
* compute ns_name before resetting argtypes ([da2e127](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/da2e1279416028a5ebca8ea564a996fdf07863cc))
* persist and restore First Number, Delay per number and AutoShift on backup save/load ([a20e8c2](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/a20e8c2fb0bf87a28e41b4b30a73596262f750d2))
* resolve dev data path against the working directory ([8b729f5](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/8b729f56e75a769bff032c3333bfcf820239fd84))
* restore C++ parity for parsing, backups, mail check, and FTP upload ([11c6e19](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/11c6e191179b995f557766ae40ea75d415b35f9f))
* show error dialog on save when output directory does not exist ([cff0d4a](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/cff0d4aec8d72b545d011f80632805f7d13b6a6a))
* sync groups on Replace even when the site has no participants ([233fed3](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/233fed37be167046ea1acbd307c7d4c92bdcf293))
* use participant_names/birth_years/cities for relay entries from API ([6426351](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/64263511b2741d8bb882e61d8f6de3d972b8c2ce))
* use Path to join backup folder and filename ([dd37b46](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/dd37b4629ac94b2628b21f24d5007016809a51fc))
* write output files as UTF-8 instead of cp1251 ([90c114b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/90c114b0344c901a9f43af9e9d97047bc3782b08))


### Documentation

* add contributing guidelines to README ([edc0764](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/edc076433a337285059fe55c13f8a2631cd08176))
* add Running the application section to README ([0aa0029](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0aa00298d34b24902bf4dc21b3afa71eabeeddd5))
* add setup instructions to README ([a562b9d](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/a562b9d889b6996502e48523c204c4cfb31e1fc7))
* document pre-commit setup and manual run command ([e903e33](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/e903e33e70e46823c8436e1f6f055a0b578268ef))
