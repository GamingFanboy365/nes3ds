//////////////////////////////////////////////////////////////////////////
// Mapper154  Namcot 108 with one-screen mirroring (Namco 3453)         //
//////////////////////////////////////////////////////////////////////////
class	Mapper154 : public Mapper088
{
public:
	Mapper154( NES* parent ) : Mapper088(parent) {}

	void	Reset();
	void	Write( WORD addr, BYTE data );

protected:
private:
};
