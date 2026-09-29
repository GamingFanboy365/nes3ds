//////////////////////////////////////////////////////////////////////////
// Mapper210  Namcot 175 / 340                                          //
//////////////////////////////////////////////////////////////////////////
void	Mapper210::Reset()
{
	// Namco 175 boards have battery-backed WRAM and fixed mirroring,
	// Namco 340 boards have no WRAM and switchable mirroring. (The
	// 175's WRAM write-enable at $C000 isn't emulated; WRAM is always
	// writable.)
	n340 = nes->rom->IsSAVERAM() ? 0 : 1;

	SetPROM_32K_Bank( PROM_8K_SIZE-4, PROM_8K_SIZE-3, PROM_8K_SIZE-2, PROM_8K_SIZE-1 );
	if( VROM_1K_SIZE ) {
		SetVROM_8K_Bank( 0 );
	}
}

void	Mapper210::Write( WORD addr, BYTE data )
{
	switch( addr & 0xF800 ) {
		case	0x8000: case	0x8800: case	0x9000: case	0x9800:
		case	0xA000: case	0xA800: case	0xB000: case	0xB800:
			SetVROM_1K_Bank( (addr>>11) & 0x07, data );
			break;

		case	0xE000:
			SetPROM_8K_Bank( 4, data & 0x3F );
			if( n340 ) {
				switch( data >> 6 ) {
					case	0: SetVRAM_Mirror( VRAM_MIRROR4L ); break;
					case	1: SetVRAM_Mirror( VRAM_VMIRROR );  break;
					case	2: SetVRAM_Mirror( VRAM_HMIRROR );  break;
					case	3: SetVRAM_Mirror( VRAM_MIRROR4H ); break;
				}
			}
			break;
		case	0xE800:
			SetPROM_8K_Bank( 5, data & 0x3F );
			break;
		case	0xF000:
			SetPROM_8K_Bank( 6, data & 0x3F );
			break;
	}
}
