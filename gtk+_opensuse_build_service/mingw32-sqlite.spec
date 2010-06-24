%define __strip %{_mingw32_strip}
%define __objdump %{_mingw32_objdump}
%define _use_internal_dependency_generator 0
%define __find_requires %{_mingw32_findrequires}
%define __find_provides %{_mingw32_findprovides}
%define __os_install_post %{_mingw32_debug_install_post} \
                          %{_mingw32_install_post}

Name:           mingw32-sqlite
Version:        3.6.23.1
Release:        0
Summary:        MinGW Windows port of sqlite embeddable SQL database engine

License:        Public Domain
Group:          Applications/Databases
URL:            http://www.sqlite.org/
Source0:        http://www.sqlite.org/sqlite-%{version}.tar.gz
Source1000:     %{name}-rpmlintrc
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
#!BuildIgnore: post-build-checks  

Patch1000:      mingw32-sqlite-3.6.14-no-undefined.patch

BuildRequires:  mingw32-filesystem >= 26
BuildRequires:  mingw32-cross-gcc
BuildRequires:  mingw32-cross-binutils

BuildRequires:  autoconf libtool tcl


%description
SQLite is a C library that implements an SQL database engine. A large
subset of SQL92 is supported. A complete database is stored in a
single disk file. The API is designed for convenience and ease of use.
Applications that link against SQLite can enjoy the power and
flexibility of an SQL database without the administrative hassles of
supporting a separate database server.



%package -n mingw32-libsqlite
Summary:        MinGW Windows port of sqlite embeddable SQL database engine
Group:          Applications/Databases

%description -n mingw32-libsqlite
SQLite is a C library that implements an SQL database engine. A large
subset of SQL92 is supported. A complete database is stored in a
single disk file. The API is designed for convenience and ease of use.
Applications that link against SQLite can enjoy the power and
flexibility of an SQL database without the administrative hassles of
supporting a separate database server.



%package -n mingw32-libsqlite-devel
Summary:        MinGW Windows port of sqlite embeddable SQL database engine
Group:          Applications/Databases

%description -n mingw32-libsqlite-devel
SQLite is a C library that implements an SQL database engine. A large
subset of SQL92 is supported. A complete database is stored in a
single disk file. The API is designed for convenience and ease of use.
Applications that link against SQLite can enjoy the power and
flexibility of an SQL database without the administrative hassles of
supporting a separate database server.


%{_mingw32_debug_package}

%prep
%setup -q -n sqlite-%{version}

%patch1000 -p1

# Ships with an old/broken version of libtool which cannot create
# Windows libraries properly.  So pull in the current version.
libtoolize --force --copy
autoreconf -f -i


%build
# I think there's a bug in the configure script where, if
# cross-compiling, it cannot correctly determine the target executable
# extension (ie. .exe).  As a result it doesn't correctly detect that
# the target is Windows and so tries to use Unix-specific functions
# which don't exist.  In any case we can work around this by forcing
# the extension via this export.
#   - RWMJ 2008-09-30
export config_TARGET_EXEEXT=.exe

echo "lt_cv_deplibs_check_method='pass_all'" >>%{_mingw32_cache}
perl -pi -e 's#archive_cmds_need_lc=yes#archive_cmds_need_lc=no#g' configure
%{_mingw32_configure} --enable-shared --disable-static \
	--disable-tcl --disable-readline \
	--disable-debug --disable-load-extension --disable-gcov

grep "\-O2" Makefile
sed -i "s/-O2 -g/-Os/g" Makefile


%{_mingw32_make} %{?_smp_mflags} || %{_mingw32_make}


%install
rm -rf $RPM_BUILD_ROOT
%{_mingw32_makeinstall}

mkdir -p $RPM_BUILD_ROOT%{_mingw32_mandir}/man1
install sqlite3.1 $RPM_BUILD_ROOT%{_mingw32_mandir}/man1/
test -e $RPM_BUILD_ROOT%{_mingw32_libdir}/*.dll && mv $RPM_BUILD_ROOT%{_mingw32_libdir}/*.dll $RPM_BUILD_ROOT%{_mingw32_bindir}

du -bcs $RPM_BUILD_ROOT%{_mingw32_bindir}/*.dll

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root)
%{_mingw32_bindir}/sqlite3.exe
%{_mingw32_mandir}/man1

%files -n mingw32-libsqlite
%defattr(-,root,root)
%{_mingw32_bindir}/libsqlite3-0.dll

%files -n mingw32-libsqlite-devel
%defattr(-,root,root)
%{_mingw32_libdir}/libsqlite3.dll.a
%{_mingw32_includedir}/sqlite3.h
%{_mingw32_includedir}/sqlite3ext.h
%{_mingw32_libdir}/pkgconfig/sqlite3.pc


%changelog
