//////////////////////////////////////////////////////////////////////////
// Mapper154  Namcot 108 with one-screen mirroring (Namco 3453)         //
//////////////////////////////////////////////////////////////////////////
void	Mapper154::Reset()
{
	Mapper088::Reset();
	SetVRAM_Mirror( VRAM_MIRROR4L );
}

void	Mapper154::Write( WORD addr, BYTE data )
{
	// Bit 6 of any write to $8000-$FFFF selects the nametable.
	if( data & 0x40 ) SetVRAM_Mirror( VRAM_MIRROR4H );
	else		  SetVRAM_Mirror( VRAM_MIRROR4L );

	// Mapper 88's $C000 mirroring register doesn't exist here.
	if( addr < 0xC000 ) {
		Mapper088::Write( addr, data );
	}
}
