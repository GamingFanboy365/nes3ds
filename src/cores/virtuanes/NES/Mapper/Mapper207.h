//////////////////////////////////////////////////////////////////////////
// Mapper207  Taito X1-005 with CHR-controlled nametables               //
//////////////////////////////////////////////////////////////////////////
class	Mapper207 : public Mapper080
{
public:
	Mapper207( NES* parent ) : Mapper080(parent) {}

	void	WriteLow(WORD addr, BYTE data);

protected:
private:
};
