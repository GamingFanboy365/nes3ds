//////////////////////////////////////////////////////////////////////////
// Mapper210  Namcot 175 / 340                                          //
//////////////////////////////////////////////////////////////////////////
class	Mapper210 : public Mapper
{
public:
	Mapper210( NES* parent ) : Mapper(parent) {}

	void	Reset();
	void	Write(WORD addr, BYTE data);

protected:
	BYTE	n340;
private:
};
