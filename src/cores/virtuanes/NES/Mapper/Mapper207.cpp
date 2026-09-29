//////////////////////////////////////////////////////////////////////////
// Mapper207  Taito X1-005 with CHR-controlled nametables               //
//////////////////////////////////////////////////////////////////////////
void	Mapper207::WriteLow( WORD addr, BYTE data )
{
	switch( addr ) {
		case	0x7EF0:	// bit 7 selects the nametable at $2000 and $2400
			Mapper080::WriteLow( addr, data );
			SetVRAM_1K_Bank(  8, data>>7 );
			SetVRAM_1K_Bank(  9, data>>7 );
			break;
		case	0x7EF1:	// bit 7 selects the nametable at $2800 and $2C00
			Mapper080::WriteLow( addr, data );
			SetVRAM_1K_Bank( 10, data>>7 );
			SetVRAM_1K_Bank( 11, data>>7 );
			break;
		case	0x7EF6:	// no mirroring register
			break;
		default:
			Mapper080::WriteLow( addr, data );
			break;
	}
}
