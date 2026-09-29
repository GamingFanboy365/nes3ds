//
// Debug output
//
#include "TypeDef.h"
#include "DebugOut.h"

#ifdef _3DS
#include <3ds.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#endif

CDebugOut	Dbg;

static const CHAR szClassName[] = "DebugWindow_wndclass";

CDebugOut::CDebugOut()
{
#if	(defined(_DEBUG) || defined(_DEBUGOUT)) && !defined(_3DS)
	hWndDebugOutput = ::FindWindow( szClassName, NULL );
	if( !hWndDebugOutput ) {
		::OutputDebugString( "DebugWindow �������܂���\n" );
	}
#endif
}

void CDebugOut::Clear()
{
#if	(defined(_DEBUG) || defined(_DEBUGOUT)) && !defined(_3DS)
	if( hWndDebugOutput ) {
		if( ::IsWindow( hWndDebugOutput ) ) {
			::SendMessage( hWndDebugOutput, WM_APP+1, (WPARAM)NULL, (LPARAM)NULL );
		}
	}
#endif
}

void __cdecl CDebugOut::Out( LPSTR fmt, ... )
{
#if	defined(_DEBUG) || defined(_DEBUGOUT)
	CHAR	buf[1000];
	va_list	va;
	va_start( va, fmt );
#ifdef _3DS
	// Shows up in the emulator's log (Azahar: Debug.Emulated), one entry
	// per line. (A zero length output means something else to the GDB stub.)
	static CHAR line[1000];
	static INT lineLen = 0;
	::vsnprintf( buf, sizeof(buf), fmt, va );
	va_end( va );
	for( CHAR* p = buf; *p; p++ ) {
		if( *p == '\n' || lineLen == sizeof(line) ) {
			if( lineLen )
				svcOutputDebugString( line, lineLen );
			lineLen = 0;
			if( *p == '\n' )
				continue;
		}
		line[lineLen++] = *p;
	}
#else
	::vsprintf( buf, fmt, va );

	if( hWndDebugOutput ) {
		if( ::IsWindow( hWndDebugOutput ) ) {
			COPYDATASTRUCT	cds;
			cds.dwData = 0;
			cds.lpData = (void*)buf;
			cds.cbData = ::strlen(buf)+1; //  �I�[��NULL������
			//  �����񑗐M
			::SendMessage( hWndDebugOutput, WM_COPYDATA, (WPARAM)NULL, (LPARAM)&cds );
		} else {
			::OutputDebugString( buf );
		}
	} else {
		::OutputDebugString( buf );
	}
#endif
#endif
}

void CDebugOut::Out( const string& str )
{
#if	defined(_DEBUG) || defined(_DEBUGOUT)
	Out( (LPSTR)str.c_str() );
#endif
}

