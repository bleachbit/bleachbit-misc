%define __strip %{_mingw32_strip}
%define __objdump %{_mingw32_objdump}
%define _use_internal_dependency_generator 0
%define __find_requires %{_mingw32_findrequires}
%define __find_provides %{_mingw32_findprovides}
%define __os_install_post %{_mingw32_debug_install_post} \
                          %{_mingw32_install_post}

Name:           mingw32-glib2
Version:        2.24.1
Release:        0
Summary:        MinGW Windows GLib2 library

License:        LGPLv2+
Group:          Development/Libraries
URL:            http://www.gtk.org
Source0:        http://download.gnome.org/sources/glib/2.24/glib-%{version}.tar.bz2
Source1:        %{name}-rpmlintrc
#This patch is needed by gnumeric
Patch0:         glib-goption-disable-localization.patch
Patch1:         glib-2.22.2-no-gdb-scripts.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
#!BuildIgnore: post-build-checks  

BuildRequires:  mingw32-filesystem >= 23
BuildRequires:  mingw32-cross-gcc
BuildRequires:  mingw32-cross-binutils
BuildRequires:  mingw32-win_iconv-devel
BuildRequires:  mingw32-gettext-tools
BuildRequires:  mingw32-zlib-devel
BuildRequires:  pkgconfig
# It looks like one needs to run autogen.sh
BuildRequires:  autoconf, automake, libtool, gtk-doc
# Native version required for msgfmt use in build
BuildRequires:  gettext-runtime
# Native version required for glib-genmarshal
BuildRequires:  glib2-devel
Requires:       %{name}-lang = %{version}

%description
MinGW Windows Glib2 library.

%package devel
Summary:        MinGW Windows GLib2 library (development tools)
Group:          Development/Libraries
Requires:       mingw32-gettext-tools

%description devel
MinGW Windows Glib2 library (development tools).


%{_mingw32_debug_package}

%lang_package 

%prep
%setup -q -n glib-%{version}

%patch0 -p0 -b .delocalize
%patch1 -p1 -b .no-gdb-scripts


%build
./autogen.sh --help
echo "lt_cv_deplibs_check_method='pass_all'" >>%{_mingw32_cache}
%{_mingw32_configure} \
	--enable-debug=no \
	--disable-selinux \
	--disable-fam \
	--disable-xattr

# Cannot export g_regex_check_replacement: symbol not defined
#	--disable-regex

grep "\-O2" Makefile
sed -i "s/-O2 -g/-Os/g" {{*/,}*/,}Makefile

make glibconfig.h.win32 &&
make glibconfig.h &&
mv glibconfig.h glibconfig.h.autogened &&
cp glibconfig.h.win32 glibconfig.h &&
make %{?_smp_mflags} || make


%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR=$RPM_BUILD_ROOT install

rm -f $RPM_BUILD_ROOT/%{_mingw32_libdir}/charset.alias

%find_lang glib20

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root)
%{_mingw32_bindir}/gspawn-win32-helper-console.exe
%{_mingw32_bindir}/gspawn-win32-helper.exe
%{_mingw32_bindir}/libgio-2.0-0.dll
%{_mingw32_bindir}/libglib-2.0-0.dll
%{_mingw32_bindir}/libgmodule-2.0-0.dll
%{_mingw32_bindir}/libgobject-2.0-0.dll
%{_mingw32_bindir}/libgthread-2.0-0.dll

%files lang -f glib20.lang

%files devel
%defattr(-,root,root)
%{_mingw32_bindir}/glib-genmarshal.exe
%{_mingw32_bindir}/glib-gettextize
%{_mingw32_bindir}/glib-mkenums
%{_mingw32_bindir}/gobject-query.exe
%{_mingw32_bindir}/gio-querymodules.exe
%{_mingw32_includedir}/glib-2.0/
%{_mingw32_libdir}/gio-2.0.def
%{_mingw32_libdir}/glib-2.0.def
%{_mingw32_libdir}/glib-2.0/
%{_mingw32_libdir}/gmodule-2.0.def
%{_mingw32_libdir}/gobject-2.0.def
%{_mingw32_libdir}/gthread-2.0.def
%{_mingw32_libdir}/libgio-2.0.dll.a
%{_mingw32_libdir}/libglib-2.0.dll.a
%{_mingw32_libdir}/libgmodule-2.0.dll.a
%{_mingw32_libdir}/libgobject-2.0.dll.a
%{_mingw32_libdir}/libgthread-2.0.dll.a
%{_mingw32_libdir}/pkgconfig/gio-2.0.pc
%{_mingw32_libdir}/pkgconfig/glib-2.0.pc
%{_mingw32_libdir}/pkgconfig/gmodule-2.0.pc
%{_mingw32_libdir}/pkgconfig/gmodule-export-2.0.pc
%{_mingw32_libdir}/pkgconfig/gmodule-no-export-2.0.pc
%{_mingw32_libdir}/pkgconfig/gobject-2.0.pc
%{_mingw32_libdir}/pkgconfig/gthread-2.0.pc
%{_mingw32_datadir}/aclocal/glib-2.0.m4
%{_mingw32_datadir}/aclocal/glib-gettext.m4
%{_mingw32_datadir}/glib-2.0/
%{_mingw32_datadir}/gtk-doc/html/gio/
%{_mingw32_datadir}/gtk-doc/html/glib/
%{_mingw32_datadir}/gtk-doc/html/gobject/
%{_mingw32_mandir}

%changelog
* Wed Sep 24 2008 Richard W.M. Jones <rjones@redhat.com> - 2.18.1-2
- Rename mingw -> mingw32.

* Mon Sep 22 2008 Daniel P. Berrange <berrange@redhat.com> - 2.18.1-1
- Update to 2.18.1 release

* Sun Sep 21 2008 Richard W.M. Jones <rjones@redhat.com> - 2.18.0-3
- Remove manpages which duplicate Fedora native.

* Thu Sep 11 2008 Daniel P. Berrange <berrange@redhat.com> - 2.18.0-2
- Add BR on pkgconfig, gettext and glib2 (native)

* Tue Sep  9 2008 Daniel P. Berrange <berrange@redhat.com> - 2.18.0-1
- Initial RPM release
