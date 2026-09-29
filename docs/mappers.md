# Mapper support

VirtuaNES for 3DS reads the iNES 1.0 header, so it knows mapper numbers 0 to 255. Of those, `CreateMapper()` in `src/cores/virtuanes/NES/MapperFactory.cpp` handles 186, plus 20 UNIF boards and the NSF player. This page lists the other 70.

The makers come from the icons in the NESdev wiki's iNES 1.0 mapper grid (the September 2026 export of the [Mapper](https://www.nesdev.org/wiki/Mapper) page). The names are FCEUX's (`src/ines.cpp`) where it has one. Names marked † are from memory and should be checked against the mapper's NESdev page before implementing.

## Missing mappers with known hardware

| Mapper | Maker | Board / name | Notes |
|---:|---|---|---|
| 14 | Supertone | REX SL-1632 | VRC2/MMC3 hybrid |
| 29 | homebrew | RET-CUFROM | |
| 30 | homebrew | UNROM 512 | Used by a lot of modern homebrew |
| 31 | homebrew | INL NSF-style board | |
| 37 | Nintendo | PAL-ZZ (Super Mario Bros./Tetris/Nintendo World Cup) | MMC3 multicart |
| 38 | Bit Corp | Bit Corp. PCI556 | |
| 53 | pirate | Supervision 16-in-1 | |
| 54 | generic | (unnamed in FCEUX) | |
| 55 | pirate | BTL-MARIO1-MALEE2 † | Pirate Super Mario Bros. |
| 56 | Kaiser | KS202 † | Pirate Super Mario Bros. 3 |
| 59 | generic | (unnamed in FCEUX) | Multicart † |
| 63 | NTDEC | (unnamed in FCEUX) | Multicart † |
| 81 | NTDEC | N715021 † | |
| 103 | generic | FDS Doki Doki Panic conversion | |
| 104 | Codemasters | Golden Five / Pegasus 5-in-1 † | |
| 106 | pirate | SMB3 pirate A | |
| 123 | generic | MMC3 pirate H2288 | |
| 124 | pirate | (unnamed in FCEUX) | |
| 125 | Whirlwind Manu | FDS LH32 conversion | |
| 126 | pirate | (unnamed in FCEUX) | MMC3 multicart † |
| 127 | pirate | (unnamed in FCEUX) | |
| 128 | pirate | (unnamed in FCEUX) | |
| 136 | Sachen | TCU02 | |
| 137 | Sachen | 8259D | |
| 138 | Sachen | 8259B | |
| 139 | Sachen | 8259C | |
| 143 | Sachen | TCA01 | |
| 144 | AGCI | AGCI 50282 | Death Race |
| 145 | Sachen | SA-72007 | |
| 147 | Sachen | TCU01 | |
| 149 | Sachen | SA-0036 | |
| 152 | Bandai | Bandai/Taito discrete board with one-screen mirroring | |
| 153 | Bandai | Bandai FCG with SRAM | Close to mapper 16 |
| 154 | Namco | Namcot 108 with one-screen mirroring † | Devil Man |
| 155 | Nintendo | MMC1A | MMC1 without the WRAM disable bit; almost free to add on top of mapper 1 |
| 157 | Bandai | Bandai Datach barcode reader | |
| 158 | Tengen | 800037 † | Alien Syndrome |
| 159 | Bandai | Bandai FCG with 24C01 EEPROM | Close to mapper 16 |
| 175 | Kaiser | (unnamed in FCEUX) | |
| 186 | generic | Fukutake Study Box | |
| 196 | pirate | (unnamed in FCEUX) | MMC3 pirate † |
| 197 | pirate | (unnamed in FCEUX) | MMC3 variant † |
| 203 | pirate | (unnamed in FCEUX) | Multicart † |
| 204 | pirate | (unnamed in FCEUX) | Multicart † |
| 205 | pirate MMC3 | JC-016-2 | MMC3 multicart |
| 207 | Taito | Taito X1-005 rev. B | Variant of mapper 80 |
| 208 | Supertone | (unnamed in FCEUX) | MMC3 pirate † |
| 210 | Namco | Namcot 175/340 | Close to mapper 19 |
| 214 | pirate | (unnamed in FCEUX) | Multicart † |
| 215 | Realtec | UNL-8237 | MMC3 variant |
| 217 | pirate | (unnamed in FCEUX) | MMC3 multicart † |
| 218 | homebrew | Magic Floor † | Uses the console's nametable RAM as CHR |
| 219 | NT | UNL-A9746 | MMC3 pirate |
| 221 | NTDEC | UNL-N625092 | Multicart |
| 238 | pirate MMC3 | UNL-603-5052 | MMC3 with protection |
| 250 | generic | Nitra † | MMC3 with swapped address lines |

## Numbers that don't need an implementation

NESdev marks 39, 84, 102, 129, 130, 131, 146, 161, 213, 223 and 224 as bad assignments: duplicates of other mappers (146 is mapper 79, 213 is mapper 58) or numbers that were never used consistently. A ROM with one of these numbers is best fixed with the right number in its header. 98 is reserved, and 239 and 247 have no known assignment.

## NES 2.0 mappers (256 and up)

The NES 2.0 header format extends mapper numbers to 4095 and adds submappers. The wiki lists 267 assigned numbers in the 256 to 767 range, mostly Chinese pirate boards, multicarts and educational computers. VirtuaNES can't load any of them yet. It reads the mapper number from the iNES 1.0 bytes only (`ROM.cpp`, `(header.control1>>4)|(header.control2&0xF0)`), so an NES 2.0 ROM with a mapper above 255 loads as the wrong mapper. Recognising the NES 2.0 header is the first step before adding any of these.

## Where to start

The cheapest wins are the variants of mappers that already exist. Mapper 155 is mapper 1 with one register bit ignored; 153 and 159 are variants of mapper 16; 210 is close to mapper 19; 207 is close to mapper 80; and 154 is a Namcot 108 board like mappers 88 and 206. After those, mapper 30 (UNROM 512) matters most for current homebrew, and 29, 31 and 218 are small homebrew boards too.
