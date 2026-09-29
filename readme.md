# VirtuaNES for 3DS

VirtuaNES is a high compatibility NES emulator for your old 3DS or 2DS. It's not as accurate as FCEUX or Nestopia, but it runs at full 60 FPS for almost all games, and supports tonnes of mappers: MMC1,3,5,6; VRC1,2,3,4,6,7; and tonnes of other mappers. As a result, the library of games it supports are huge.

This 3DS version also fixes a few bugs from VirtuaNES's MMC5 mappers and even plays Rockman 4 Minus Infinity and Zelda Legend of Link hacks.

This is a fork of bubble2k16's [emus3ds](https://github.com/bubble2k16/emus3ds), narrowed down to the VirtuaNES core. See [readme-virtuanes.md](readme-virtuanes.md) for installation, usage and the change history.

![alt tag](https://github.com/bubble2k16/emus3ds/blob/master/screenshots/VirtuaNES%20-%20Gradius%20II.bmp)

![alt tag](https://github.com/bubble2k16/emus3ds/blob/master/screenshots/VirtuaNES%20-%20Kirby's%20Adventure.bmp)

## Building

The code builds with a current devkitARM (libctru 2.x). If you have devkitPro installed, run `make`, which produces `virtuanes_3ds.3dsx` and `virtuanes_3ds.cia`.

Without a local devkitPro, `tools/build.sh` runs the same `make` inside the official `devkitpro/devkitarm` Docker image and passes its arguments through, so `tools/build.sh clean` works too.

`make DEBUGOUT=1` turns on the `DEBUGOUT()` traces that are sprinkled through the VirtuaNES core and mappers (ROM header details at load time, unhandled mapper writes and so on). They go to `svcOutputDebugString`, which shows up in the emulator's log. The flag isn't tracked by the build, so run `make clean` when switching it on or off.

## Running and debugging in Azahar

The [Azahar](https://azahar-emu.org/) 3DS emulator (the successor of Citra and Lime3DS) runs the `.3dsx` directly, which is the quickest way to try a change. If you have it installed, open `virtuanes_3ds.3dsx` from it, and put your ROMs on its emulated SD card, the `sdmc` folder in Azahar's user directory. Under an emulator VirtuaNES runs without sound, because Azahar doesn't implement the CSND sound service it uses.

`tools/azahar/run.sh` runs Azahar from the `linuxserver/azahar` Docker image instead, and can script it. By default it runs headless on a virtual display, presses 3DS buttons and takes screenshots of both screens at native size, which is handy for checking that a game boots and looks right after a mapper change:

```sh
tools/build.sh
tools/azahar/run.sh -r game.nes -- wait:8 key:a wait:5 shot:title key:start wait:3 shot:ingame
```

The ROMs given with `-r` are the only ones on the emulated SD card, so pressing A at the ROM menu loads the first one. Screenshots and the Azahar log (including `DEBUGOUT()` output) end up in `.azahar/out`. `tools/azahar/run.sh --help` lists all the steps and options, and `--gui` shows the emulator on your X11 display instead.

For a debugger, start the emulator with `-g`, which makes Azahar's GDB stub wait for a connection, and then attach devkitARM's GDB with `tools/azahar/gdb.sh`:

```sh
tools/azahar/run.sh -r game.nes -g -t 3600 &
tools/azahar/gdb.sh
(gdb) break Mapper004::Write
(gdb) continue
```

`tools/azahar/smoketest.py` checks the whole setup end to end. It builds a tiny test ROM that shows a blue screen and turns it red while A is held, runs it in Azahar and checks the screenshots.

`tools/azahar/mappertest.py` does the same for mappers: it generates a test ROM per mapper whose code sets the mapper's registers and checks what the CPU and PPU then see (every PRG and CHR bank starts with its own number) and how the nametables are mirrored. The screen turns green when every check passes, and red otherwise. Pass mapper numbers to run only those, e.g. `tools/azahar/mappertest.py 210`.

## Adding a mapper

Mappers live in `src/cores/virtuanes/NES/Mapper`, one class per mapper (`MapperNNN.h` and `MapperNNN.cpp`) deriving from `Mapper`. They are compiled as part of `src/cores/virtuanes/NES/MapperFactory.cpp`, which `#include`s every mapper header and source file, and whose `CreateMapper()` maps iNES mapper numbers (and UNIF board names) to the classes. So a new mapper needs its two files plus the two `#include`s and a `case` in `CreateMapper()`. The existing mappers such as `Mapper003` (CNROM) are the best reference for the bank switching helpers (`SetPROM_8K_Bank()`, `SetVROM_1K_Bank()` and friends).

To test a new mapper, add a test function and a `TESTS` entry to `tools/azahar/mappertest.py`. [docs/mappers.md](docs/mappers.md) lists the iNES mappers that VirtuaNES doesn't support yet, and which ones are the easiest to add.
