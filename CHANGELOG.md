# Changelog

## [0.6.0](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.5.1...v0.6.0) (2026-10-30)


### Features

* **form:** edit a rider's chip ids next to the site entry ([7df7297](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/7df7297533849e39f6ac21bdb28a9bfad90cce13))
* **form:** name the loaded lines whose chip ids hold a foreign character ([403cc72](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/403cc72f64c3e76aac051d0260c52713c5ef18c1))
* **form:** stop a save on a chip id typed in another keyboard layout ([05ec781](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/05ec781bc75cdfe3851eda981961fa2e4337f21a))
* **protocol:** bind each relay rider's chips to their own stage bib ([1c111b1](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/1c111b1878fc4db950a7a27b594a0b1b282c43b0))
* **protocol:** flag protocol lines whose chip ids no reader can use ([efc2afc](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/efc2afccac5ea3398d9b4cced5c3906395b6e8ca))
* **protocol:** keep each rider's chip ids in field 11 ([8af0c30](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/8af0c30851083483f8414b20fb48918c28bccb8f))
* **protocol:** report a chip id used on two protocol lines ([fcf67c1](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/fcf67c1df64f65fd88c02a864ade2ae532bc0d53))
* **search:** find the rider who carries a scanned chip id ([0960f2c](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0960f2c5c66899255dcec80f5482a4581338ff01))
* **team:** carry every member's chip ids into the team line ([8d2731f](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/8d2731fe720d644989c7b32a6311162cd596f9ba))


### Bug Fixes

* **form:** carry only freshly typed chip ids into a rider, on every way of opening one ([0627b97](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0627b976cc7ddefa79b66c1ca003bc2f0c92e8a3))
* **form:** check field 11 of a loaded line only where the line has one ([049a5dc](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/049a5dc4e8673584a56912442ed61f5f092be2d5))
* **form:** count as typed only the chip ids the filled field did not have ([dfb39bd](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/dfb39bdf474398a75df56ca250884bb98cd6d0c1))
* **form:** drop typographic punctuation from chip ids instead of refusing them ([b282bab](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/b282bab07abff1981d9dfa2c21b6cf0335772c88))
* **form:** end filled-in chip ids with a separator so the next scan stays apart ([971a5d9](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/971a5d92ac87cdccbc35b6a7e804fe0a3a6346bc))
* **form:** ignore invisible characters in chip ids and name a foreign one ([9b9e9e7](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/9b9e9e72e408bf455ec5852ae2ade374fe24cb9a))
* **form:** keep a tag scanned before the rider is opened, and say so ([3882ea6](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/3882ea6022908cdf768d936c5f92edfaff2fe582))
* **form:** keep cleaned chip ids as the registrar's until saved ([8c29104](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/8c291044727394b3e0607193c9804c07f9e026a9))
* **form:** leave out a rider's own chip scanned before the line was opened ([e0c3160](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/e0c3160ea7fc8a1174ba714c0f9eacad719978fb))
* **form:** make only spaces and full-width forms plain in chip ids, not every look-alike ([e682b85](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/e682b8500841888332d842749f4233b7ab7f291a))
* **form:** name chip ids scanned before opening a relay instead of guessing the rider ([42b74f4](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/42b74f4981bee6382bbd529f0109813aebbfdd58))
* **form:** name every kind of character the loaded-list warning is about ([22b0984](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/22b0984a4e10095544ab21fca9e6af9bd9bbbe6c))
* **form:** separate a chip id at the cursor when a reader ends it with Enter ([0662883](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/06628838080e4161b82d03e0f757c0977212edc2))
* **form:** show a dropped repeated chip id before saving ([9695dac](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/9695dac9c5eabc5acae0cb2bbd2837100938c563))
* **form:** show cleaned chip ids before saving instead of guessing at spaces ([2885bcd](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/2885bcdf4bc4fde04e07784a005c2872d855214c))
* **form:** show two ids that only a zero-width space kept apart ([058e0c4](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/058e0c46360bf50dbaeaf48fa401c612fcfabf58))
* **protocol:** flag a relay rider past the last stage even when its chip repeats ([3a3d515](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/3a3d5157b93884d0577534925ba00f275ca465b5))
* **protocol:** flag any character outside ASCII in a copied chip field ([a9db2a4](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/a9db2a41f2da648c2d584fd2216083452af97679))
* **protocol:** flag full-width chip ids in lines copied verbatim ([35e6386](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/35e63862d823955a5ee3cc53e5bb1687b8a8aa1b))
* **protocol:** name a chip on two bibs instead of moving the selection to it ([5f3d5d6](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/5f3d5d69c66ac49ddd33e89bdefecabaf36a9b44))
* **protocol:** name the line with chip problems instead of selecting it ([10233ac](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/10233ac1c6e72dc8c1c0341df510f4d435fa573f))
* **protocol:** read two whole chip ids pasted with a space as two ([745f197](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/745f19722fc288e4bf10aaad1325f968f7c433b4))
* **protocol:** report a chip only when it is on the lines of two different bibs ([7632cb7](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/7632cb79f9a4c53e9bf319f0042b42efbc3fc01f))
* **protocol:** report one chip listed for two riders of a relay ([ae6fd9f](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/ae6fd9f4f46de4f7692d2a764379aebd28b22fb7))
* **protocol:** write a foreign chip id as typed rather than as another id ([708c9b6](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/708c9b6e83596851194d1a04afe4deff87ca900a))
* **protocol:** write an empty chip field for a team without chips ([21abb12](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/21abb121f53f4f78b62670c12ba1cfbfd4ef0b87))
* **search:** leave chip ids out of the scripts the list is said to hold ([acfee8b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/acfee8bd165296f9f5a1be3363e96fd88a024fe7))
* **search:** leave chip ids out of what Find matches ([555b5b0](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/555b5b0f88ed3476d4c5edf0fa086cb96f0ad21c))
* **search:** treat a query shorter than eight characters as a bib, not a chip ([a0e9041](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/a0e9041fd0ac38ec11bdfdf0a44d8df68d0ab8e9))
* **team:** count a relay's members joined by &lt;br&gt; in any case ([b017c07](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/b017c07b1d005be90e05f27934a3d630cb1bb633))
* **team:** count a site relay's members when a member is added ([9e6ce67](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/9e6ce67474a1ab3493b7f9533263d43cc433a0b2))
* **team:** give chips typed before the first member to that member ([e084a7d](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/e084a7dd84e1e798199815960e490231d8395950))
* **team:** give ids typed before adding a member to the member added last ([ee3e7b1](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/ee3e7b11c259de664f57819b5d184a4f18f34228))
* **team:** join a member's chips to those scanned ahead for that member ([8fda9da](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/8fda9da42df1c0b72d20f3b5eb061c182b37a928))
* **team:** keep a team's chip ids as typed so the save still checks them ([3f079a1](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/3f079a1e3e70e5c1e87e093a8927ff42e6547677))
* **team:** keep the team's stage count when a member is added ([f95d13d](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/f95d13d3abd56803fa7fdf6cd3b12159f770df5b))
* **team:** leave a repeated chip id to the save check instead of dropping it ([cd34d83](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/cd34d8313d2ba1cd92d5bf5f433487c7d0c008e5))
* **team:** leave a rider without chips empty instead of a dash the next scan sticks to ([3b7baa9](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/3b7baa9b606cae4df1ed9bdb7c0df53dec2c23c3))
* **team:** place an added member by the team's size, not by its chip field ([4cd974a](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/4cd974af88cddc9592f7bf5425dd22f107f1de86))
* **team:** point out chip ids typed before a member was added when the rider is unclear ([8f2811c](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/8f2811c583cdf09c514c70c0cda9358b73bee74f))
* **team:** start a new team from its own stage and count only named members ([d0e93e9](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/d0e93e925920923ca26ebbe0893c19d945143ac4))
* **team:** write a rider without chips as a dash so stages never shift ([898ed69](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/898ed69927a5563a38d889fe8de9e07059b07a3f))


### Performance Improvements

* **form:** read only field 11 when checking a loaded list ([da70f15](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/da70f1539e0c6a383a86fbc5f8469e1e9e0d41cd))
* **protocol:** find chip problems and chips on two bibs in one pass ([3030a23](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/3030a232c1fae844f3d1eadb86ed22dca83a5c8b))
* **protocol:** look at a line's riders only when it is a relay ([0b1437d](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0b1437dca212e7e178abdb2a21359ea862d78d7f))
* **protocol:** read the protocol list once for the duplicate checks ([e680161](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/e68016143555feb30d3dd248f434c0e1ad020357))
* **search:** make the chip id of a Find query once per search ([9523e16](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/9523e1664b185afe0522dfbb3c5d9fd91779f945))


### Documentation

* describe the chip checks and rider groups as built ([9aeac71](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/9aeac7179ddbf842ee47a74e07799e16630ba319))
* describe the chip field of the start protocol line ([b1faa26](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/b1faa260f1a82adb14947e49d0fca79be984dd03))
* drop set_chips from the plan, since nothing needs it ([b5f193f](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/b5f193f182a5dda541570475720960e6bdc59534))
* drop the dash from the description of a rider without chips ([1e093ee](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/1e093eec26678fe8874ee05c1d561c3de1a60dcd))
* keep a chip id typed in groups of four as one id ([344ef1b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/344ef1b5bfe52e9d5a9649395062b5f7eda46035))
* let a desk reader's Enter separate chip ids ([1d48cbd](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/1d48cbd8306b6d7b0f3c32754eae59b62f523b00))
* plan the chip field of the start protocol line ([696fe97](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/696fe97a70f2f4137689a0752120b1d72f1c8679))
* say exactly what lights the chip indicator ([355165b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/355165bdb90760405dbff6c1d059b34b950a8676))
* say where an added member goes when the team lists more riders ([eed001a](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/eed001ab4fd962882251d76a91e2d0a5eeaaa00d))
* say which characters stop a chip id and which are dropped ([0a14193](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0a14193d404386103d4bcfbb19969d1d3df01d40))
* specify keeping each rider's timing chips on the start protocol line ([2e94aa9](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/2e94aa9f15ab570ab2d2795c223d484a509a043f))
* stop a save on a chip id typed in another keyboard layout ([1c2c4c3](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/1c2c4c38fbf8a16d2ff26fa8f253c9ebcf916276))

## [0.5.1](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.5.0...v0.5.1) (2026-10-27)


### Bug Fixes

* keep text separators from shifting registration references ([2e207bd](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/2e207bdf072c30f119997d9e83cd689e9d0b212e))
* keep the issued team bib when adding a member ([d8cf61e](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/d8cf61e47e8d93959987de249c130c9dcfa45867))

## [0.5.0](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.4.1...v0.5.0) (2026-10-26)


### Features

* keep the site registration on every start protocol line, through the form, teams and merges ([d0029bf](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/d0029bf182224785d63e262a605d1901279fb332))


### Bug Fixes

* keep the laps field in a line saved for a group without laps ([0d9781c](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0d9781c15e69b1d50b4a46339554bfa221e662e4))
* link an old line to a site registration only when the name match is one-to-one ([f689a7f](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/f689a7f54b9fd87ce9b14f2f176e241736db511b))


### Documentation

* adopt a constitution for spec-first changes ([a5fdbe8](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/a5fdbe855a9823fa5c8a21c85ca73935102f6eaf))
* describe the start protocol line, the backup and the site exchange as they work today ([ba0200b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/ba0200b2c3142c75d33cd05a9bed4864b5b90e77))
* show the site registration as a form field and keep it on both lists ([d9e9ab5](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/d9e9ab55bc91a5d7eb799fdf6f51c3de464db0dd))
* specify keeping the site registration on every start protocol line ([25f6a28](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/25f6a28c842b1745db282adca50ab256c2d2bd35))
* write the reference field even when empty, and never merge two references by name ([194be5b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/194be5bdb38f75209e59e3ebeb3fd9cd67efbc07))

## [0.4.1](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.4.0...v0.4.1) (2026-10-11)


### Bug Fixes

* resolve runtime files beside the portable application ([fa0e814](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/fa0e81497fd1666b5cb457d4c950f4fab1f5fc3e))


### Documentation

* clarify portable runtime paths for coding agents ([d99c84a](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/d99c84a57bc228c59626bd2f80b572ea37f8ec0a))

## [0.4.0](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.3.1...v0.4.0) (2026-10-09)


### Features

* show participants who have not paid, marked NOT_PAID in the bib column ([1b2f6c8](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/1b2f6c8e376158b7479ef5830398835e835e7aab))

## [0.3.1](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.3.0...v0.3.1) (2026-10-03)


### Bug Fixes

* keep additional info from splitting protocol records ([f03392d](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/f03392d136669b9216d86404b0f813fcb1f56774))
* preserve participant additional info in start protocols ([f953433](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/f953433c24475b421d47883e87f6ebb9eba51cd0))

## [0.3.0](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.2.3...v0.3.0) (2026-09-19)


### Features

* cover the kazakh alphabet and accented latin in search ([059057d](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/059057d4ccf6f644618a9e77eb0aae1705fde23e))
* find riders by transliteration in either direction ([ed8d6be](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/ed8d6be6c8d4f967593df2729da9d899c6eb2f66))


### Bug Fixes

* call an accented latin letter latin on the debug line ([b78056b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/b78056b4efebd5fcdb1076c48340667180d36b5c))
* keep digits out of the run collapsing so bib 11 is not bib 1 ([0b1dab4](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0b1dab43e658fde602e585666c8e29c96e1a5ee3))
* match a name across its alternative latin spellings ([07fdaa3](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/07fdaa3e2e74d948bf38ebfbc81362769ab64062))
* name only the scripts the debug line can tell apart ([4e43333](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/4e433339a4007e50abb7e979eb75da395e5b0441))


### Documentation

* forbid ai credit lines in commits, prs and comments ([05828b6](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/05828b6032755d7de9f0b1ba490da1d9814e3919))

## [0.2.3](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.2.2...v0.2.3) (2026-09-15)


### Bug Fixes

* rebase the autoshift first bib when the site moves the range ([1094ccc](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/1094ccc7e281c55bf01b9ababe9c887035ccdebe))
* rebase the first bib only when the interval actually moved ([6792bad](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/6792bad44e0e8f613e3930d0288c3d7c64b08062))
* refresh a group bib range from the site on every download ([6ae1e75](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/6ae1e757a1be1d69327110305b2e40e9e60ae18c))
* refresh every row of a duplicated group, not just the last ([a0f4583](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/a0f4583db54466e1273ccd8e97a29f26718068f9))


### Documentation

* read the ci check status, not the empty conclusion field ([718eb5e](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/718eb5e16b6999943d644597dfdca25659ec083c))

## [0.2.2](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.2.1...v0.2.2) (2026-09-04)


### Documentation

* take the CI verdict from the rollup, not the lagging checks list ([dfc148d](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/dfc148d2098479808f54e58ad43606a79ca77c3f))

## [0.2.1](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.2.0...v0.2.1) (2026-09-02)


### Documentation

* record how to work in this repo for coding agents ([1d23e85](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/1d23e851c143fea6f41bf6ea37efdbdecdc5289a))

## [0.2.0](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.1.6...v0.2.0) (2026-08-20)


### Features

* add auto upload of the start list to the site ([0712ec1](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/0712ec1a544f88d60c5c67af8462dcde76bddd19))


### Bug Fixes

* clear the auto send status when a backup is loaded ([3cdaec4](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/3cdaec4d6baec2ba6ab3e97280f32562ec3918ee))
* drop a queued upload when another backup is loaded ([dbae90b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/dbae90b63f778bce4c6ca4077b3653d9acef4f7f))
* keep the auto upload from moving the protocol selection ([e1d3424](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/e1d3424af49233668f1b2655a02ac985b6d851f5))
* keep unsent edits pending until the site is configured ([f93a285](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/f93a285d79cc017cd1287999490c0361436cedf4))
* reject a malformed site response instead of raising in a slot ([45b9abb](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/45b9abbd4974c90d1b7fb5ae09735113db681e24))
* retry a failed upload on a timer instead of on the next edit ([cdaeecd](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/cdaeecd732b632720507c48f93dbc8b713693678))
* save the typed shift values rather than a group override ([e9def0b](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/e9def0b5d9b163f95bd622cc92c53d50e323de60))
* stop a group time shift override from leaking to other groups ([82a1203](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/82a1203a8439bed16455b080cf89e42b92559b1e))
* stop autoshift from clearing the first number and delay ([b17db48](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/b17db483063c5a9594a52e0581d9a8ec700e7664))
* turn a dropped connection into a message instead of a crash ([90cf619](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/90cf619476313d9c39c1d4aaa59d30542b086444))


### Documentation

* correct where the auto send status is shown ([35e70e4](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/35e70e47e4150fd9e5ad8391955a445e14cc4bce))

## [0.1.6](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.1.5...v0.1.6) (2026-07-27)


### Bug Fixes

* keep the macos bundle file name free of spaces ([85d7fc3](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/85d7fc3baf608ebcefa9336c0c5e09056ae83f0c))

## [0.1.5](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.1.4...v0.1.5) (2026-07-27)


### Bug Fixes

* give the macos bundle a proper identifier and version ([741e6d0](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/741e6d08603c919bfacafd7166e6567ddfa22ffc))
* show the full app name in the dock and task switcher ([cdc2f68](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/cdc2f68a7fea41c0874bf07074f43a2f9217f768))

## [0.1.4](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.1.3...v0.1.4) (2026-07-25)


### Bug Fixes

* keep uv.lock in step with the released version ([5f5e084](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/5f5e0843c77ddf738ec91ca9942dfff8e14ac146))

## [0.1.3](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.1.2...v0.1.3) (2026-07-25)


### Documentation

* explain how to run the app from a release ([4e2cddb](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/4e2cddbc047236a36e98991d82cb6cab55a5d6c2))

## [0.1.2](https://github.com/dchernykh1984/StartProtocolMakerPython/compare/v0.1.1...v0.1.2) (2026-07-22)


### Bug Fixes

* embed the app icon in the macOS build ([ff6ef69](https://github.com/dchernykh1984/StartProtocolMakerPython/commit/ff6ef699446dc4ed436ba373574ecd41154af6e9))

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
